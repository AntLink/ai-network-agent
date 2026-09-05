package executor

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/ai-network-agent/edge/internal/credentials"
	"golang.org/x/crypto/ssh"
)

func TestFactsExecutorFailsClosedWithoutKeystore(t *testing.T) {
	_, err := (FactsExecutor{}).Execute(context.Background(), FactsRequest{Host: "192.0.2.1", CredentialRef: "cred-1"})
	if err == nil {
		t.Fatal("expected keystore error")
	}
}

func TestFactsExecutorRequiresPinnedHostKey(t *testing.T) {
	path := filepath.Join(t.TempDir(), "keystore.json")
	data, err := json.Marshal(map[string]credentials.Entry{
		"r1": {Username: "admin", Password: "redacted"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	store, err := credentials.Load(path)
	if err != nil {
		t.Fatal(err)
	}
	_, err = (FactsExecutor{Store: store}).Execute(context.Background(), FactsRequest{Host: "192.0.2.1", CredentialRef: "r1"})
	if err == nil || err.Error() != "credential_ref has no pinned SSH host key" {
		t.Fatalf("expected host-key fail-closed error, got %v", err)
	}
}

func TestFactsExecutorExecutesFixedCommandWithPinnedHostKey(t *testing.T) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	signer, err := ssh.NewSignerFromKey(key)
	if err != nil {
		t.Fatal(err)
	}
	serverConfig := &ssh.ServerConfig{
		PasswordCallback: func(c ssh.ConnMetadata, password []byte) (*ssh.Permissions, error) {
			if c.User() != "admin" || string(password) != "unit-secret" {
				return nil, fmt.Errorf("unexpected credentials")
			}
			return nil, nil
		},
	}
	serverConfig.AddHostKey(signer)
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	go serveFactsTestSSH(t, listener, serverConfig)

	path := filepath.Join(t.TempDir(), "keystore.json")
	entry := credentials.Entry{
		Username: "admin", Password: "unit-secret",
		HostKey: string(ssh.MarshalAuthorizedKey(signer.PublicKey())),
	}
	data, err := json.Marshal(map[string]credentials.Entry{"r1": entry})
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	store, err := credentials.Load(path)
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().(*net.TCPAddr)
	out, err := (FactsExecutor{Store: store, Timeout: 5 * time.Second}).Execute(
		context.Background(), FactsRequest{Host: "127.0.0.1", Port: address.Port, CredentialRef: "r1"},
	)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(out, "Cisco IOS Software") {
		t.Fatalf("unexpected facts output: %q", out)
	}
}

func serveFactsTestSSH(t *testing.T, listener net.Listener, config *ssh.ServerConfig) {
	t.Helper()
	conn, err := listener.Accept()
	if err != nil {
		return
	}
	serverConn, chans, reqs, err := ssh.NewServerConn(conn, config)
	if err != nil {
		t.Errorf("SSH server handshake: %v", err)
		return
	}
	defer serverConn.Close()
	go ssh.DiscardRequests(reqs)
	for newChannel := range chans {
		if newChannel.ChannelType() != "session" {
			_ = newChannel.Reject(ssh.UnknownChannelType, "session only")
			continue
		}
		channel, requests, err := newChannel.Accept()
		if err != nil {
			continue
		}
		for request := range requests {
			if request.Type != "exec" || len(request.Payload) < 4 {
				_ = request.Reply(false, nil)
				continue
			}
			commandLength := int(request.Payload[0])<<24 | int(request.Payload[1])<<16 | int(request.Payload[2])<<8 | int(request.Payload[3])
			if commandLength != len(request.Payload)-4 || string(request.Payload[4:]) != "show version" {
				_ = request.Reply(false, nil)
				continue
			}
			_ = request.Reply(true, nil)
			_, _ = channel.Write([]byte("Cisco IOS Software\n"))
			_, _ = channel.SendRequest("exit-status", false, []byte{0, 0, 0, 0})
			_ = channel.Close()
			return
		}
		_ = channel.Close()
	}
}
