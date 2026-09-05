package control

import (
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

const maxControlResponseBytes = 64 * 1024

// Client is the Edge-side authenticated control transport. It uses HTTPS with
// a client certificate; the server remains responsible for central lease state.
type Client struct {
	BaseURL              string
	HTTPClient           *http.Client
	TLSConfig            *tls.Config
	EdgeID               string
	BootID               string
	UnresolvedAttemptIDs []string
	SigningKey           ed25519.PrivateKey

	mu             sync.RWMutex
	SessionID      string
	Reconciliation map[string]string
}

type welcomeResponse struct {
	SessionID      string            `json:"session_id"`
	Reconciliation map[string]string `json:"reconciliation"`
}

type reconciliationResponse struct {
	Decisions map[string]map[string]interface{} `json:"decisions"`
}

type TaskEnvelopeResponse struct {
	Type      string                 `json:"type"`
	SessionID string                 `json:"session_id"`
	Task      map[string]interface{} `json:"task"`
}

type JournalAttemptSummary struct {
	AttemptID       string `json:"attempt_id"`
	IdempotencyKey  string `json:"idempotency_key"`
	Status          string `json:"status"`
	ResultAvailable bool   `json:"result_available"`
	Signature       string `json:"signature,omitempty"`
}

func (c *Client) httpClient() (*http.Client, error) {
	if !strings.HasPrefix(strings.ToLower(strings.TrimSpace(c.BaseURL)), "https://") {
		return nil, fmt.Errorf("central control URL must use https")
	}
	if c.HTTPClient != nil {
		return c.HTTPClient, nil
	}
	if c.TLSConfig == nil {
		return nil, fmt.Errorf("mTLS TLS config is required")
	}
	return &http.Client{Transport: &http.Transport{TLSClientConfig: c.TLSConfig.Clone()}, Timeout: 30 * time.Second}, nil
}

// Connect establishes HELLO/READY before any heartbeat is sent.
func (c *Client) Connect(ctx context.Context) error {
	if c.EdgeID == "" || c.BootID == "" {
		return fmt.Errorf("Edge ID and boot ID are required")
	}
	client, err := c.httpClient()
	if err != nil {
		return err
	}
	unresolvedAttemptIDs := c.UnresolvedAttemptIDs
	if unresolvedAttemptIDs == nil {
		unresolvedAttemptIDs = []string{}
	}
	var welcome welcomeResponse
	if err := c.postJSON(ctx, client, "/v1/control/hello", map[string]interface{}{
		"edge_id": c.EdgeID, "edge_version": "m1", "min_protocol_version": 1,
		"max_protocol_version": 1, "driver_capability_version": 1,
		"capabilities": []string{"device.read.facts"}, "boot_id": c.BootID,
		"unresolved_attempt_ids": unresolvedAttemptIDs,
	}, &welcome, ""); err != nil {
		return fmt.Errorf("control hello failed: %w", err)
	}
	if welcome.SessionID == "" {
		return fmt.Errorf("control hello returned no session")
	}
	if err := c.postJSON(ctx, client, "/v1/control/ready", map[string]string{"session_id": welcome.SessionID}, nil, ""); err != nil {
		return fmt.Errorf("control ready failed: %w", err)
	}
	c.mu.Lock()
	c.SessionID = welcome.SessionID
	c.Reconciliation = welcome.Reconciliation
	c.mu.Unlock()
	return nil
}

func (c *Client) SendPresenceHeartbeat(ctx context.Context, heartbeat PresenceHeartbeat) error {
	if heartbeat.SessionID == "" {
		return fmt.Errorf("session ID is required")
	}
	client, err := c.httpClient()
	if err != nil {
		return err
	}
	return c.postJSON(ctx, client, "/v1/control/heartbeat", heartbeat, nil, heartbeat.SessionID)
}

func (c *Client) SendTaskHeartbeat(ctx context.Context, heartbeat TaskHeartbeat) error {
	if heartbeat.SessionID == "" || heartbeat.AttemptID == "" {
		return fmt.Errorf("session and attempt IDs are required")
	}
	client, err := c.httpClient()
	if err != nil {
		return err
	}
	return c.postJSON(ctx, client, "/v1/control/task-heartbeat", heartbeat, nil, heartbeat.SessionID)
}

func (c *Client) PollTask(ctx context.Context) (map[string]interface{}, error) {
	c.mu.RLock()
	sessionID := c.SessionID
	c.mu.RUnlock()
	if sessionID == "" {
		return nil, fmt.Errorf("session ID is required")
	}
	client, err := c.httpClient()
	if err != nil {
		return nil, err
	}
	var response TaskEnvelopeResponse
	if err := c.postJSON(ctx, client, "/v1/control/tasks/next", map[string]string{"session_id": sessionID}, &response, sessionID); err != nil {
		return nil, fmt.Errorf("poll task failed: %w", err)
	}
	return response.Task, nil
}

func (c *Client) SubmitTaskResult(ctx context.Context, attemptID string, result map[string]interface{}) error {
	c.mu.RLock()
	sessionID := c.SessionID
	c.mu.RUnlock()
	if sessionID == "" || attemptID == "" {
		return fmt.Errorf("session and attempt IDs are required")
	}
	client, err := c.httpClient()
	if err != nil {
		return err
	}
	return c.postJSON(ctx, client, "/v1/control/tasks/result", map[string]interface{}{"session_id": sessionID, "attempt_id": attemptID, "result": result}, nil, sessionID)
}

// Reconcile asks Central to classify unresolved attempts. It never authorizes replay.
func (c *Client) Reconcile(ctx context.Context, attemptIDs []string) (map[string]map[string]interface{}, error) {
	summaries := make([]JournalAttemptSummary, 0, len(attemptIDs))
	for _, attemptID := range attemptIDs {
		summaries = append(summaries, JournalAttemptSummary{AttemptID: attemptID, Status: "UNKNOWN"})
	}
	return c.ReconcileSummaries(ctx, summaries)
}

// ReconcileSummaries sends typed, non-authoritative Edge journal metadata.
func (c *Client) ReconcileSummaries(ctx context.Context, summaries []JournalAttemptSummary) (map[string]map[string]interface{}, error) {
	c.mu.RLock()
	sessionID := c.SessionID
	c.mu.RUnlock()
	if sessionID == "" {
		return nil, fmt.Errorf("session ID is required")
	}
	client, err := c.httpClient()
	if err != nil {
		return nil, err
	}
	var response reconciliationResponse
	attemptIDs := make([]string, 0, len(summaries))
	for _, summary := range summaries {
		if c.SigningKey != nil {
			var err error
			summary, err = signSummary(summary, c.SigningKey)
			if err != nil {
				return nil, fmt.Errorf("sign journal summary: %w", err)
			}
		}
		attemptIDs = append(attemptIDs, summary.AttemptID)
	}
	if err := c.postJSON(ctx, client, "/v1/control/reconcile", map[string]interface{}{"session_id": sessionID, "attempt_ids": attemptIDs, "summaries": summaries}, &response, sessionID); err != nil {
		return nil, fmt.Errorf("reconciliation failed: %w", err)
	}
	return response.Decisions, nil
}

// Run maintains an authenticated session and restarts it after a transport
// heartbeat failure. The scheduler is cancelled before reconnecting, so stale
// session loops cannot continue sending messages.
func (c *Client) Run(ctx context.Context, scheduler *HeartbeatScheduler, initialBackoff, maxBackoff time.Duration) error {
	if scheduler == nil {
		return fmt.Errorf("heartbeat scheduler is required")
	}
	if initialBackoff <= 0 {
		initialBackoff = time.Second
	}
	if maxBackoff < initialBackoff {
		maxBackoff = 30 * time.Second
	}
	backoff := initialBackoff
	for {
		if err := c.Connect(ctx); err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			fmt.Fprintf(os.Stderr, "control connect retry: %v\n", err)
			if err := waitBackoff(ctx, backoff); err != nil {
				return err
			}
			backoff = minDuration(backoff*2, maxBackoff)
			continue
		}
		backoff = initialBackoff
		c.mu.RLock()
		sessionID := c.SessionID
		c.mu.RUnlock()
		scheduler.Presence = PresenceHeartbeat{SessionID: sessionID, EdgeID: c.EdgeID, BootID: c.BootID}
		runCtx, cancel := context.WithCancel(ctx)
		disconnected := make(chan error, 1)
		scheduler.ErrorSink = func(err error) {
			select {
			case disconnected <- err:
			default:
			}
		}
		scheduler.Start(runCtx)
		select {
		case <-ctx.Done():
			cancel()
			return ctx.Err()
		case <-disconnected:
			cancel()
			if err := waitBackoff(ctx, backoff); err != nil {
				return err
			}
			backoff = minDuration(backoff*2, maxBackoff)
		}
	}
}

func waitBackoff(ctx context.Context, duration time.Duration) error {
	timer := time.NewTimer(duration)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}

func minDuration(a, b time.Duration) time.Duration {
	if a < b {
		return a
	}
	return b
}

func (c *Client) postJSON(ctx context.Context, client *http.Client, path string, payload interface{}, response interface{}, sessionID string) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("encode control message: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(c.BaseURL, "/")+path, strings.NewReader(string(body)))
	if err != nil {
		return fmt.Errorf("build control request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	if sessionID != "" {
		req.Header.Set("X-Edge-Session", sessionID)
	}
	if c.EdgeID != "" {
		req.Header.Set("X-Client-Edge-ID", c.EdgeID)
	}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("control request transport error: %w", err)
	}
	defer resp.Body.Close()
	limited := io.LimitReader(resp.Body, maxControlResponseBytes)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(limited)
		return fmt.Errorf("control request rejected with status %d: %s", resp.StatusCode, strings.TrimSpace(string(body)))
	}
	if response != nil {
		if err := json.NewDecoder(limited).Decode(response); err != nil {
			return fmt.Errorf("decode control response: %w", err)
		}
	} else {
		_, _ = io.Copy(io.Discard, limited)
	}
	return nil
}
