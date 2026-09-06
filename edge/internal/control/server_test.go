package control

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestControlHandlerRejectsWrongEdgeAndAllowsTypedCapability(t *testing.T) {
	handlerCalls := 0
	s := Server{EdgeID: "edge-1", JournalPath: filepath.Join(t.TempDir(), "attempt-journal.json"), Handler: func(_ context.Context, e Envelope) (map[string]interface{}, error) {
		handlerCalls++
		return map[string]interface{}{"status": "SUCCEEDED", "attempt_id": e.AttemptID}, nil
	}}
	ts := httptest.NewServer(s.HTTPHandler())
	defer ts.Close()
	hello := `{"edge_id":"edge-1","edge_version":"m1","min_protocol_version":1,"max_protocol_version":1,"driver_capability_version":1,"capabilities":["device.read.facts"],"boot_id":"boot-1"}`
	helloResp, err := http.Post(ts.URL+"/v1/control/hello", "application/json", strings.NewReader(hello))
	if err != nil {
		t.Fatal(err)
	}
	var welcome map[string]interface{}
	if err := json.NewDecoder(helloResp.Body).Decode(&welcome); err != nil {
		t.Fatal(err)
	}
	_ = helloResp.Body.Close()
	sessionID, _ := welcome["session_id"].(string)
	readyResp, err := http.Post(ts.URL+"/v1/control/ready", "application/json", strings.NewReader(`{"session_id":"`+sessionID+`"}`))
	if err != nil || readyResp.StatusCode != http.StatusOK {
		t.Fatalf("ready status=%v %v", readyResp.StatusCode, err)
	}
	_ = readyResp.Body.Close()
	heartbeatResp, err := http.Post(ts.URL+"/v1/control/heartbeat", "application/json", strings.NewReader(`{"session_id":"`+sessionID+`","edge_id":"edge-1","boot_id":"boot-1"}`))
	if err != nil || heartbeatResp.StatusCode != http.StatusOK {
		t.Fatalf("session heartbeat status=%v %v", heartbeatResp.StatusCode, err)
	}
	_ = heartbeatResp.Body.Close()
	taskHeartbeatResp, err := http.Post(ts.URL+"/v1/control/task-heartbeat", "application/json", strings.NewReader(`{"session_id":"`+sessionID+`","attempt_id":"a1"}`))
	if err != nil || taskHeartbeatResp.StatusCode != http.StatusOK {
		t.Fatalf("task heartbeat status=%v %v", taskHeartbeatResp.StatusCode, err)
	}
	_ = taskHeartbeatResp.Body.Close()
	body := `{"protocol_version":1,"driver_capability_version":1,"message_id":"m1","task_id":"t1","attempt_id":"a1","idempotency_key":"i1","edge_id":"edge-1","nonce":"1234567890123456","issued_at":"2026-09-03T00:00:00Z","valid_for_seconds":300,"retry_class":"SAFE_RETRY","capability":"device.read.facts","credential_ref":"cred-1","payload":{}}`
	// Use a current timestamp so the validity window is meaningful.
	body = strings.Replace(body, "2026-09-03T00:00:00Z", time.Now().UTC().Format(time.RFC3339), 1)
	req, err := http.NewRequest(http.MethodPost, ts.URL+"/v1/control/task", strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("X-Edge-Session", sessionID)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status=%d", resp.StatusCode)
	}
	_ = resp.Body.Close()
	duplicateReq, err := http.NewRequest(http.MethodPost, ts.URL+"/v1/control/task", strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	duplicateReq.Header.Set("X-Edge-Session", sessionID)
	duplicateResp, err := http.DefaultClient.Do(duplicateReq)
	if err != nil {
		t.Fatal(err)
	}
	defer duplicateResp.Body.Close()
	if duplicateResp.StatusCode != http.StatusOK {
		t.Fatalf("duplicate status=%d", duplicateResp.StatusCode)
	}
	var duplicate map[string]interface{}
	if err := json.NewDecoder(duplicateResp.Body).Decode(&duplicate); err != nil {
		t.Fatal(err)
	}
	if duplicate["duplicate_delivery"] != true || handlerCalls != 1 {
		t.Fatalf("duplicate delivery was executed again: body=%v calls=%d", duplicate, handlerCalls)
	}
	if _, err := os.Stat(s.JournalPath); err != nil {
		t.Fatalf("journal was not persisted: %v", err)
	}
}

func TestSessionRegistryRestoresTerminalJournalAfterRestart(t *testing.T) {
	journalPath := filepath.Join(t.TempDir(), "attempt-journal.json")
	first := &SessionRegistry{attemptResults: map[string]map[string]interface{}{
		"attempt-1\x00idem-1": {"status": "SUCCEEDED", "attempt_id": "attempt-1"},
	}, journalLimit: 4, journalPath: journalPath}
	first.mu.Lock()
	if err := first.persistJournalLocked(); err != nil {
		first.mu.Unlock()
		t.Fatal(err)
	}
	first.mu.Unlock()

	second := &SessionRegistry{}
	server := Server{EdgeID: "edge-1", Sessions: second, JournalPath: journalPath}
	_ = server.HTTPHandler()
	second.mu.Lock()
	restored, ok := second.attemptResults["attempt-1\x00idem-1"]
	second.mu.Unlock()
	if !ok || restored["status"] != "SUCCEEDED" {
		t.Fatalf("terminal result was not restored: %v", second.attemptResults)
	}
}

func TestControlHandlerRejectsConcurrentDuplicateDelivery(t *testing.T) {
	started := make(chan struct{})
	release := make(chan struct{})
	var calls atomic.Int32
	registry := &SessionRegistry{sessions: map[string]*SessionRecord{
		"session-1": {Ready: true, TaskHeartbeats: map[string]time.Time{}},
	}}
	server := Server{EdgeID: "edge-1", Sessions: registry, Handler: func(_ context.Context, e Envelope) (map[string]interface{}, error) {
		calls.Add(1)
		close(started)
		<-release
		return map[string]interface{}{"status": "SUCCEEDED", "attempt_id": e.AttemptID}, nil
	}}
	handler := server.HTTPHandler()
	body := `{"protocol_version":1,"driver_capability_version":1,"message_id":"m-concurrent","task_id":"t-concurrent","attempt_id":"a-concurrent","idempotency_key":"i-concurrent","edge_id":"edge-1","nonce":"1234567890123456","issued_at":"` + time.Now().UTC().Format(time.RFC3339) + `","valid_for_seconds":300,"retry_class":"SAFE_RETRY","capability":"device.read.facts","credential_ref":"cred-1","payload":{}}`
	firstResponse := make(chan *httptest.ResponseRecorder, 1)
	go func() {
		recorder := httptest.NewRecorder()
		request := httptest.NewRequest(http.MethodPost, "/v1/control/task", strings.NewReader(body))
		request.Header.Set("X-Edge-Session", "session-1")
		handler.ServeHTTP(recorder, request)
		firstResponse <- recorder
	}()
	select {
	case <-started:
	case <-time.After(time.Second):
		t.Fatal("first execution did not start")
	}
	second := httptest.NewRecorder()
	secondRequest := httptest.NewRequest(http.MethodPost, "/v1/control/task", strings.NewReader(body))
	secondRequest.Header.Set("X-Edge-Session", "session-1")
	handler.ServeHTTP(second, secondRequest)
	if second.Code != http.StatusConflict {
		t.Fatalf("concurrent duplicate status=%d body=%s", second.Code, second.Body.String())
	}
	close(release)
	first := <-firstResponse
	if first.Code != http.StatusOK || calls.Load() != 1 {
		t.Fatalf("first status=%d calls=%d", first.Code, calls.Load())
	}
}
