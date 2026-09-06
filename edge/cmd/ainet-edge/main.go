package main

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/ai-network-agent/edge/internal/control"
	"github.com/ai-network-agent/edge/internal/credentials"
	"github.com/ai-network-agent/edge/internal/executor"
	"github.com/ai-network-agent/edge/internal/security"
)

const protocolVersion = 1

type Envelope struct {
	ProtocolVersion         int                    `json:"protocol_version"`
	DriverCapabilityVersion int                    `json:"driver_capability_version"`
	MessageID               string                 `json:"message_id"`
	TaskID                  string                 `json:"task_id"`
	AttemptID               string                 `json:"attempt_id"`
	IdempotencyKey          string                 `json:"idempotency_key"`
	EdgeID                  string                 `json:"edge_id"`
	Sequence                uint64                 `json:"sequence"`
	Nonce                   string                 `json:"nonce"`
	IssuedAt                time.Time              `json:"issued_at"`
	ValidForSeconds         int                    `json:"valid_for_seconds"`
	RetryClass              string                 `json:"retry_class"`
	Capability              string                 `json:"capability"`
	CredentialRef           string                 `json:"credential_ref,omitempty"`
	Payload                 map[string]interface{} `json:"payload"`
}

type Journal struct {
	mu      sync.Mutex
	results map[string]map[string]interface{}
}

func (j *Journal) get(attemptID string) (map[string]interface{}, bool) {
	j.mu.Lock()
	defer j.mu.Unlock()
	r, ok := j.results[attemptID]
	return r, ok
}

func (j *Journal) put(attemptID string, result map[string]interface{}) {
	j.mu.Lock()
	defer j.mu.Unlock()
	j.results[attemptID] = result
}

func validate(e Envelope, now time.Time) error {
	if e.ProtocolVersion != protocolVersion {
		return fmt.Errorf("unsupported protocol_version")
	}
	if e.MessageID == "" || e.TaskID == "" || e.AttemptID == "" || e.EdgeID == "" {
		return errors.New("missing identity field")
	}
	if len(e.Nonce) < 16 {
		return errors.New("nonce too short")
	}
	if e.ValidForSeconds < 1 || e.ValidForSeconds > 300 {
		return errors.New("invalid validity window")
	}
	if now.Before(e.IssuedAt.Add(-30*time.Second)) || now.After(e.IssuedAt.Add(time.Duration(e.ValidForSeconds)*time.Second+30*time.Second)) {
		return errors.New("message outside validity window")
	}
	if e.Capability != "device.read.facts" {
		return errors.New("unsupported capability")
	}
	if e.RetryClass != "SAFE_RETRY" {
		return errors.New("capability retry class mismatch")
	}
	return nil
}

func execute(e Envelope, j *Journal, now time.Time) map[string]interface{} {
	if r, ok := j.get(e.AttemptID); ok {
		return r
	}
	// Device I/O is intentionally an explicit connector seam in this first slice.
	// No arbitrary command from payload is accepted.
	r := map[string]interface{}{"attempt_id": e.AttemptID, "task_id": e.TaskID, "status": "NOT_CONFIGURED", "error_code": "LOCAL_DEVICE_CONNECTOR_NOT_CONFIGURED", "capability": e.Capability}
	j.put(e.AttemptID, r)
	return r
}

func executeFacts(ctx context.Context, e Envelope, ex executor.FactsExecutor, j *Journal) map[string]interface{} {
	if r, ok := j.get(e.AttemptID); ok {
		return r
	}
	host, _ := e.Payload["device_host"].(string)
	vendor, _ := e.Payload["device_vendor"].(string)
	port := 22
	if p, ok := e.Payload["device_port"].(float64); ok {
		port = int(p)
	}
	raw, err := ex.Execute(ctx, executor.FactsRequest{Host: host, Port: port, CredentialRef: e.CredentialRef, Vendor: vendor})
	if err != nil {
		r := map[string]interface{}{"status": "FAILED", "task_id": e.TaskID, "attempt_id": e.AttemptID, "capability": e.Capability, "error_code": "LOCAL_DEVICE_EXECUTION_FAILED"}
		j.put(e.AttemptID, r)
		return r
	}
	normalized := executor.NormalizeCiscoFacts(raw)
	if vendor == "mikrotik" || vendor == "routeros" {
		normalized = executor.NormalizeRouterOSFacts(raw)
	}
	r := map[string]interface{}{"status": "SUCCEEDED", "task_id": e.TaskID, "attempt_id": e.AttemptID, "capability": e.Capability, "data": normalized, "raw": raw}
	j.put(e.AttemptID, r)
	return r
}

func pollTasks(ctx context.Context, client *control.Client, ex executor.FactsExecutor, j *Journal) {
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}
		envelope, err := client.PollTask(ctx)
		if err == nil && envelope != nil {
			encoded, _ := json.Marshal(envelope)
			var task Envelope
			if json.Unmarshal(encoded, &task) == nil {
				result := executeFacts(ctx, task, ex, j)
				_ = client.SubmitTaskResult(ctx, task.AttemptID, result)
			}
		}
		timer := time.NewTimer(500 * time.Millisecond)
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
	}
}

func run(in io.Reader, out io.Writer, now func() time.Time) error {
	s := bufio.NewScanner(in)
	enc := json.NewEncoder(out)
	j := &Journal{results: map[string]map[string]interface{}{}}
	for s.Scan() {
		var e Envelope
		if err := json.Unmarshal(s.Bytes(), &e); err != nil {
			return err
		}
		if err := validate(e, now()); err != nil {
			_ = enc.Encode(map[string]interface{}{"status": "REJECTED", "error": err.Error()})
			continue
		}
		if err := enc.Encode(execute(e, j, now())); err != nil {
			return err
		}
	}
	return s.Err()
}

func main() {
	listen := flag.String("control-listen", "", "mTLS control listen address, e.g. 0.0.0.0:9443")
	controlURL := flag.String("control-url", "", "Central mTLS control URL, e.g. https://central:9443")
	controlServerName := flag.String("control-server-name", "central", "Central TLS server name, e.g. edge-control.antlinx.com")
	edgeID := flag.String("edge-id", "", "registered Edge identity")
	bootID := flag.String("boot-id", "", "Edge boot/session identity")
	caFile := flag.String("ca-file", "", "project CA PEM")
	certFile := flag.String("cert-file", "", "Edge certificate PEM")
	keyFile := flag.String("key-file", "", "Edge private key PEM")
	keystoreFile := flag.String("keystore-file", "", "Edge-local credential keystore JSON")
	journalFile := flag.String("journal-file", "", "Edge-local durable terminal-attempt journal JSON")
	journalSigningKey := flag.String("journal-signing-key", "", "Edge-local Ed25519 PKCS#8 journal signing key PEM")
	flag.Parse()
	if *controlURL != "" {
		if *edgeID == "" || *bootID == "" {
			fmt.Fprintln(os.Stderr, "edge-id and boot-id are required")
			os.Exit(2)
		}
		tlsConfig, err := security.ClientConfig(security.MTLSFiles{CAFile: *caFile, CertificateFile: *certFile, PrivateKeyFile: *keyFile, ServerName: *controlServerName})
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		client := &control.Client{BaseURL: *controlURL, TLSConfig: tlsConfig, EdgeID: *edgeID, BootID: *bootID}
		store, err := credentials.Load(*keystoreFile)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		ex := executor.FactsExecutor{Store: store}
		journal := &Journal{results: map[string]map[string]interface{}{}}
		if *journalSigningKey != "" {
			signingKey, err := security.LoadEd25519PrivateKey(*journalSigningKey)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(2)
			}
			client.SigningKey = signingKey
		}
		scheduler := &control.HeartbeatScheduler{Sender: client, PresenceInterval: 15 * time.Second, TaskInterval: 10 * time.Second}
		ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()
		go pollTasks(ctx, client, ex, journal)
		if err := client.Run(ctx, scheduler, time.Second, 30*time.Second); err != nil && ctx.Err() == nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}
	if *listen != "" {
		if *edgeID == "" || *keystoreFile == "" {
			fmt.Fprintln(os.Stderr, "edge-id and keystore-file are required")
			os.Exit(2)
		}
		tlsConfig, err := security.ServerConfig(security.MTLSFiles{CAFile: *caFile, CertificateFile: *certFile, PrivateKeyFile: *keyFile})
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		store, err := credentials.Load(*keystoreFile)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		ln, err := net.Listen("tcp", *listen)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		ex := executor.FactsExecutor{Store: store}
		srv := control.Server{EdgeID: *edgeID, TLSConfig: tlsConfig, JournalPath: *journalFile, Handler: func(ctx context.Context, e control.Envelope) (map[string]interface{}, error) {
			host, _ := e.Payload["device_host"].(string)
			vendor, _ := e.Payload["device_vendor"].(string)
			port := 22
			if p, ok := e.Payload["device_port"].(float64); ok {
				port = int(p)
			}
			raw, err := ex.Execute(ctx, executor.FactsRequest{Host: host, Port: port, CredentialRef: e.CredentialRef, Vendor: vendor})
			if err != nil {
				return nil, err
			}
			normalized := executor.NormalizeCiscoFacts(raw)
			if vendor == "mikrotik" || vendor == "routeros" {
				normalized = executor.NormalizeRouterOSFacts(raw)
			}
			return map[string]interface{}{"status": "SUCCEEDED", "task_id": e.TaskID, "attempt_id": e.AttemptID, "capability": e.Capability, "data": normalized, "raw": raw}, nil
		}}
		if err := srv.Serve(context.Background(), ln); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return
	}
	if err := run(os.Stdin, os.Stdout, time.Now); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
