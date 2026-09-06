package executor

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"time"

	"github.com/ai-network-agent/edge/internal/credentials"
	"golang.org/x/crypto/ssh"
)

const debugLog = "/root/edge-debug.log"

func _logDebug(format string, args ...interface{}) {
	f, err := os.OpenFile(debugLog, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return
	}
	fmt.Fprintf(f, format+"\n", args...)
	f.Close()
}

type FactsRequest struct {
	Host          string
	Port          int
	CredentialRef string
	Vendor        string
}

func factsCommand(vendor string) string {
	if vendor == "mikrotik" || vendor == "routeros" {
		return "/system resource print"
	}
	return "show version"
}

// FactsExecutor maps the capability to a fixed read-only command. It never
// accepts a command string from a task payload.
//
// For IOSv devices that offer legacy key exchange algorithms (e.g.
// diffie-hellman-group14-sha1), the executor shells out to the system ssh
// client (with sshpass for password auth) which supports these algorithms,
// rather than using Go's x/crypto/ssh which may not negotiate them.
type FactsExecutor struct {
	Store   *credentials.KeyStore
	Timeout time.Duration
}

func (e FactsExecutor) Execute(ctx context.Context, req FactsRequest) (string, error) {
	_logDebug("Execute called: ref=%s host=%s:%d", req.CredentialRef, req.Host, req.Port)
	if e.Store == nil {
		return "", fmt.Errorf("local credential keystore is not configured")
	}
	cred, err := e.Store.Resolve(req.CredentialRef)
	if err != nil {
		_logDebug("Store.Resolve error: %v", err)
		return "", err
	}
	_logDebug("Resolved cred user=%s hk_len=%d", cred.Username, len(cred.HostKey))
	if req.Host == "" {
		return "", fmt.Errorf("device host is required")
	}
	if req.Port == 0 {
		req.Port = 22
	}
	if cred.Password == "" {
		return "", fmt.Errorf("credential_ref has no password for SSH password authentication")
	}
	if cred.HostKey == "" {
		return "", fmt.Errorf("credential_ref has no pinned SSH host key")
	}
	if e.Timeout == 0 {
		e.Timeout = 30 * time.Second
	}

	// Use the system ssh client (with sshpass) FIRST because IOSv devices offer
	// legacy key exchange algorithms (diffie-hellman-group14-sha1) that Go's
	// x/crypto/ssh may not negotiate; trying Go SSH first could block on the
	// handshake and consume the whole timeout. System ssh + sshpass handles it.
	_logDebug("attempting system SSH (primary)...")
	sysOut, sysErr := e.executeWithSystemSSH(ctx, req, cred)
	if sysErr == nil {
		_logDebug("System SSH OK len=%d", len(sysOut))
		return sysOut, nil
	}
	_logDebug("System SSH FAILED: %v", sysErr)

	// Fall back to the in-process Go SSH client for modern devices.
	_logDebug("attempting Go SSH (fallback)...")
	goOut, goErr := e.executeWithGoSSH(ctx, req, cred)
	if goErr == nil {
		_logDebug("Go SSH OK len=%d", len(goOut))
		return goOut, nil
	}
	_logDebug("Go SSH FAILED: %v", goErr)
	return "", goErr
}

func (e FactsExecutor) executeWithGoSSH(ctx context.Context, req FactsRequest, cred credentials.Entry) (string, error) {
	publicKey, _, _, _, err := ssh.ParseAuthorizedKey([]byte(cred.HostKey))
	if err != nil {
		return "", fmt.Errorf("invalid pinned SSH host key: %w", err)
	}
	ctx, cancel := context.WithTimeout(ctx, e.Timeout)
	defer cancel()
	dialer := net.Dialer{}
	conn, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(req.Host, fmt.Sprint(req.Port)))
	if err != nil {
		return "", fmt.Errorf("facts connector failed to connect: %w", err)
	}
	config := &ssh.ClientConfig{
		User:            cred.Username,
		Auth:            []ssh.AuthMethod{ssh.Password(cred.Password)},
		HostKeyCallback: ssh.FixedHostKey(publicKey),
		Timeout:         e.Timeout,
	}
	clientConn, channels, requests, err := ssh.NewClientConn(conn, net.JoinHostPort(req.Host, fmt.Sprint(req.Port)), config)
	if err != nil {
		_ = conn.Close()
		return "", fmt.Errorf("facts connector SSH handshake failed: %w", err)
	}
	client := ssh.NewClient(clientConn, channels, requests)
	defer client.Close()
	session, err := client.NewSession()
	if err != nil {
		return "", fmt.Errorf("facts connector session failed: %w", err)
	}
	defer session.Close()
	var out []byte
	if req.Vendor == "mikrotik" || req.Vendor == "routeros" {
		out, err = executeRouterOSShell(session, factsCommand(req.Vendor))
	} else {
		out, err = session.Output(factsCommand(req.Vendor))
	}
	if err != nil {
		return "", fmt.Errorf("facts connector command failed: %w", err)
	}
	return string(out), nil
}

func executeRouterOSShell(session *ssh.Session, command string) ([]byte, error) {
	stdin, err := session.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("routeros shell stdin failed: %w", err)
	}
	var stdout, stderr bytes.Buffer
	session.Stdout = &stdout
	session.Stderr = &stderr
	if err := session.RequestPty("xterm", 80, 24, ssh.TerminalModes{ssh.ECHO: 0}); err != nil {
		return nil, fmt.Errorf("routeros shell pty failed: %w", err)
	}
	if err := session.Shell(); err != nil {
		return nil, fmt.Errorf("routeros shell start failed: %w", err)
	}
	if _, err := io.WriteString(stdin, command+"\n"); err != nil {
		return nil, fmt.Errorf("routeros shell write failed: %w", err)
	}
	time.Sleep(1500 * time.Millisecond)
	_ = session.Close()
	if err := session.Wait(); err != nil && stdout.Len() == 0 {
		return nil, fmt.Errorf("routeros shell command failed: %w: %s", err, stderr.String())
	}
	return stdout.Bytes(), nil
}

func (e FactsExecutor) executeWithSystemSSH(ctx context.Context, req FactsRequest, cred credentials.Entry) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, e.Timeout)
	defer cancel()

	// Debug log
	f, ferr := os.OpenFile(debugLog, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if ferr == nil {
		fmt.Fprintf(f, "=== systemSSH attempt host=%s:%d user=%s ===\n", req.Host, req.Port, cred.Username)
		f.Close()
	}

	args := []string{
		"-o", "StrictHostKeyChecking=no",
		"-o", "UserKnownHostsFile=/dev/null",
		"-o", "ConnectTimeout=15",
		"-o", "PreferredAuthentications=password",
		"-o", "NumberOfPasswordPrompts=1",
		"-o", "KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1",
		"-o", "HostKeyAlgorithms=+ssh-rsa",
		"-o", "PubkeyAcceptedAlgorithms=+ssh-rsa",
		"-o", "BatchMode=no",
		fmt.Sprintf("%s@%s", cred.Username, req.Host),
		factsCommand(req.Vendor),
	}
	proc := exec.CommandContext(ctx, "/usr/bin/sshpass", append([]string{"-p", cred.Password, "/usr/bin/ssh"}, args...)...)
	proc.Env = append(os.Environ(), "PATH=/usr/bin:/bin:/sbin:/usr/sbin", "LANG=C")
	out, err := proc.CombinedOutput()
	if ferr == nil {
		f2, _ := os.OpenFile(debugLog, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		fmt.Fprintf(f2, "sshpass exit=%v out_len=%d err=%v\n", err, len(out), err)
		f2.Close()
	}
	if err != nil {
		return "", fmt.Errorf("facts connector sshpass failed: %w: %s", err, string(out))
	}
	return string(out), nil
}
