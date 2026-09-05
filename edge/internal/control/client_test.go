package control

import (
	"context"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestClientConnectAndHeartbeatUsesSession(t *testing.T) {
	var seenSession string
	var seenUnresolved bool
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v1/control/hello" {
			var payload struct {
				UnresolvedAttemptIDs []string `json:"unresolved_attempt_ids"`
			}
			_ = json.NewDecoder(r.Body).Decode(&payload)
			seenUnresolved = len(payload.UnresolvedAttemptIDs) == 1 && payload.UnresolvedAttemptIDs[0] == "attempt-unknown"
			_ = json.NewEncoder(w).Encode(map[string]interface{}{"session_id": "session-central-1", "reconciliation": map[string]string{"attempt-unknown": "RECONCILE_REQUIRED"}})
			return
		}
		if r.URL.Path == "/v1/control/ready" {
			w.WriteHeader(http.StatusOK)
			return
		}
		if r.URL.Path == "/v1/control/reconcile" {
			_ = json.NewEncoder(w).Encode(map[string]interface{}{"decisions": map[string]map[string]interface{}{"attempt-unknown": {"decision": "RECONCILE_REQUIRED"}}})
			return
		}
		seenSession = r.Header.Get("X-Edge-Session")
		w.WriteHeader(http.StatusOK)
	})
	ts := httptest.NewTLSServer(handler)
	defer ts.Close()
	transport := ts.Client().Transport.(*http.Transport).Clone()
	transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // test server certificate only
	client := &Client{BaseURL: ts.URL, HTTPClient: &http.Client{Transport: transport}, EdgeID: "edge-1", BootID: "boot-1", UnresolvedAttemptIDs: []string{"attempt-unknown"}}
	if err := client.Connect(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := client.SendPresenceHeartbeat(context.Background(), PresenceHeartbeat{SessionID: "session-central-1", EdgeID: "edge-1", BootID: "boot-1"}); err != nil {
		t.Fatal(err)
	}
	if err := client.SendTaskHeartbeat(context.Background(), TaskHeartbeat{SessionID: "session-central-1", AttemptID: "attempt-1"}); err != nil {
		t.Fatal(err)
	}
	if seenSession != "session-central-1" {
		t.Fatalf("session header=%q", seenSession)
	}
	if !seenUnresolved || client.Reconciliation["attempt-unknown"] != "RECONCILE_REQUIRED" {
		t.Fatalf("reconciliation=%v unresolved_sent=%v", client.Reconciliation, seenUnresolved)
	}
	decisions, err := client.Reconcile(context.Background(), []string{"attempt-unknown"})
	if err != nil {
		t.Fatal(err)
	}
	if decisions["attempt-unknown"]["decision"] != "RECONCILE_REQUIRED" {
		t.Fatalf("decisions=%v", decisions)
	}
}

func TestClientRequiresHTTPSAndIdentity(t *testing.T) {
	client := &Client{BaseURL: "http://central", EdgeID: "edge-1", BootID: "boot-1"}
	if err := client.Connect(context.Background()); err == nil {
		t.Fatal("expected HTTPS requirement")
	}
}

func TestClientSendsEmptyUnresolvedListWhenUnset(t *testing.T) {
	var unresolved interface{}
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v1/control/hello" {
			var payload map[string]interface{}
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			unresolved = payload["unresolved_attempt_ids"]
			_ = json.NewEncoder(w).Encode(map[string]interface{}{"session_id": "s", "reconciliation": map[string]string{}})
			return
		}
		w.WriteHeader(http.StatusOK)
	})
	ts := httptest.NewTLSServer(handler)
	defer ts.Close()
	client := &Client{BaseURL: ts.URL, HTTPClient: ts.Client(), EdgeID: "edge-1", BootID: "boot-1"}
	if err := client.Connect(context.Background()); err != nil {
		t.Fatal(err)
	}
	items, ok := unresolved.([]interface{})
	if !ok || len(items) != 0 {
		t.Fatalf("unresolved_attempt_ids=%#v, want empty JSON list", unresolved)
	}
}

func TestReconcileSummariesSignsCanonicalSummary(t *testing.T) {
	publicKey, privateKey, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatal(err)
	}
	summary := JournalAttemptSummary{AttemptID: "attempt-1", IdempotencyKey: "idem-1", Status: "UNKNOWN", ResultAvailable: false}
	signed, err := signSummary(summary, privateKey)
	if err != nil {
		t.Fatal(err)
	}
	rawSignature, err := base64.RawURLEncoding.DecodeString(signed.Signature)
	if err != nil || !ed25519.Verify(publicKey, mustCanonical(summary), rawSignature) {
		t.Fatalf("signature did not verify: %v", err)
	}
	if string(mustCanonical(summary)) != `{"attempt_id":"attempt-1","idempotency_key":"idem-1","result_available":false,"status":"UNKNOWN"}` {
		t.Fatalf("unexpected canonical summary: %s", mustCanonical(summary))
	}
}

func mustCanonical(summary JournalAttemptSummary) []byte {
	canonical, err := canonicalSummary(summary)
	if err != nil {
		panic(err)
	}
	return canonical
}

func TestClientRunReconnectsAfterHeartbeatFailure(t *testing.T) {
	var hellos atomic.Int32
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/v1/control/hello":
			hellos.Add(1)
			_ = json.NewEncoder(w).Encode(map[string]string{"session_id": "session-reconnect"})
		case "/v1/control/ready":
			w.WriteHeader(http.StatusOK)
		case "/v1/control/heartbeat":
			w.WriteHeader(http.StatusServiceUnavailable)
		default:
			w.WriteHeader(http.StatusOK)
		}
	})
	ts := httptest.NewTLSServer(handler)
	defer ts.Close()
	transport := ts.Client().Transport.(*http.Transport).Clone()
	transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} // test server certificate only
	client := &Client{BaseURL: ts.URL, HTTPClient: &http.Client{Transport: transport}, EdgeID: "edge-1", BootID: "boot-1"}
	scheduler := &HeartbeatScheduler{Sender: client, PresenceInterval: time.Millisecond, TaskInterval: time.Hour}
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Millisecond)
	defer cancel()
	if err := client.Run(ctx, scheduler, time.Millisecond, 2*time.Millisecond); err != context.DeadlineExceeded {
		t.Fatalf("run error=%v", err)
	}
	if hellos.Load() < 2 {
		t.Fatalf("expected reconnect, hello count=%d", hellos.Load())
	}
}
