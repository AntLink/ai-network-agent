package control

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"sync"
	"time"
)

type Envelope struct {
	ProtocolVersion         int                    `json:"protocol_version"`
	DriverCapabilityVersion int                    `json:"driver_capability_version"`
	MessageID               string                 `json:"message_id"`
	TaskID                  string                 `json:"task_id"`
	AttemptID               string                 `json:"attempt_id"`
	IdempotencyKey          string                 `json:"idempotency_key"`
	EdgeID                  string                 `json:"edge_id"`
	Nonce                   string                 `json:"nonce"`
	IssuedAt                time.Time              `json:"issued_at"`
	ValidForSeconds         int                    `json:"valid_for_seconds"`
	RetryClass              string                 `json:"retry_class"`
	Capability              string                 `json:"capability"`
	CredentialRef           string                 `json:"credential_ref"`
	Payload                 map[string]interface{} `json:"payload"`
}

type HandlerFunc func(context.Context, Envelope) (map[string]interface{}, error)

type helloRequest struct {
	EdgeID                  string   `json:"edge_id"`
	EdgeVersion             string   `json:"edge_version"`
	MinProtocolVersion      int      `json:"min_protocol_version"`
	MaxProtocolVersion      int      `json:"max_protocol_version"`
	DriverCapabilityVersion int      `json:"driver_capability_version"`
	Capabilities            []string `json:"capabilities"`
	BootID                  string   `json:"boot_id"`
	UnresolvedAttemptIDs    []string `json:"unresolved_attempt_ids,omitempty"`
}
type readyRequest struct {
	SessionID string `json:"session_id"`
}
type heartbeatRequest struct {
	SessionID string `json:"session_id"`
	EdgeID    string `json:"edge_id"`
	BootID    string `json:"boot_id"`
}
type taskHeartbeatRequest struct {
	SessionID string    `json:"session_id"`
	AttemptID string    `json:"attempt_id"`
	SentAt    time.Time `json:"sent_at"`
}
type SessionRecord struct {
	Ready          bool
	LastSeen       time.Time
	TaskHeartbeats map[string]time.Time
}
type SessionRegistry struct {
	mu             sync.Mutex
	sessions       map[string]*SessionRecord
	attemptResults map[string]map[string]interface{}
	attemptOrder   []string
	inFlight       map[string]bool
	journalLimit   int
	journalPath    string
	journalLoaded  bool
}

type Server struct {
	EdgeID       string
	TLSConfig    *tls.Config
	Handler      HandlerFunc
	MaxBodyBytes int64
	Sessions     *SessionRegistry
	JournalPath  string
}

func (s Server) HTTPHandler() http.Handler {
	max := s.MaxBodyBytes
	if max == 0 {
		max = 64 * 1024
	}
	mux := http.NewServeMux()
	sessions := s.Sessions
	if sessions == nil {
		sessions = &SessionRegistry{sessions: map[string]*SessionRecord{}}
	}
	sessions.mu.Lock()
	if sessions.sessions == nil {
		sessions.sessions = map[string]*SessionRecord{}
	}
	if sessions.attemptResults == nil {
		sessions.attemptResults = map[string]map[string]interface{}{}
	}
	if sessions.inFlight == nil {
		sessions.inFlight = map[string]bool{}
	}
	if sessions.journalLimit == 0 {
		sessions.journalLimit = 1024
	}
	if !sessions.journalLoaded {
		sessions.journalPath = s.JournalPath
		if sessions.journalPath != "" {
			_ = sessions.loadJournalLocked()
		}
		sessions.journalLoaded = true
	}
	sessions.mu.Unlock()
	mux.HandleFunc("/v1/control/hello", func(w http.ResponseWriter, r *http.Request) {
		var h helloRequest
		if r.Method != http.MethodPost || json.NewDecoder(http.MaxBytesReader(w, r.Body, max)).Decode(&h) != nil || h.EdgeID != s.EdgeID || h.MinProtocolVersion > 1 || h.MaxProtocolVersion < 1 || h.DriverCapabilityVersion != 1 {
			http.Error(w, "hello rejected", http.StatusBadRequest)
			return
		}
		sessionID := fmt.Sprintf("session-%d", time.Now().UnixNano())
		sessions.mu.Lock()
		sessions.sessions[sessionID] = &SessionRecord{LastSeen: time.Now().UTC(), TaskHeartbeats: map[string]time.Time{}}
		sessions.mu.Unlock()
		reconciliation := make(map[string]string, len(h.UnresolvedAttemptIDs))
		for _, attemptID := range h.UnresolvedAttemptIDs {
			if attemptID != "" {
				reconciliation[attemptID] = "RECONCILE_REQUIRED"
			}
		}
		_ = json.NewEncoder(w).Encode(map[string]interface{}{"type": "WELCOME", "session_id": sessionID, "protocol_version": 1, "driver_capability_version": 1, "heartbeat_interval_seconds": 15, "server_time": time.Now().UTC(), "reconciliation": reconciliation})
	})
	mux.HandleFunc("/v1/control/ready", func(w http.ResponseWriter, r *http.Request) {
		var ready readyRequest
		if r.Method != http.MethodPost || json.NewDecoder(http.MaxBytesReader(w, r.Body, max)).Decode(&ready) != nil {
			http.Error(w, "ready rejected", http.StatusBadRequest)
			return
		}
		sessions.mu.Lock()
		record, ok := sessions.sessions[ready.SessionID]
		if ok {
			record.Ready = true
			record.LastSeen = time.Now().UTC()
		}
		sessions.mu.Unlock()
		if !ok {
			http.Error(w, "unknown session", http.StatusForbidden)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]interface{}{"type": "READY_ACK", "session_id": ready.SessionID})
	})
	mux.HandleFunc("/v1/control/heartbeat", func(w http.ResponseWriter, r *http.Request) {
		var heartbeat heartbeatRequest
		if r.Method != http.MethodPost || json.NewDecoder(http.MaxBytesReader(w, r.Body, max)).Decode(&heartbeat) != nil || heartbeat.SessionID == "" || heartbeat.EdgeID != s.EdgeID {
			http.Error(w, "heartbeat rejected", http.StatusBadRequest)
			return
		}
		sessions.mu.Lock()
		record, ok := sessions.sessions[heartbeat.SessionID]
		ready := ok && record.Ready
		if ready {
			record.LastSeen = time.Now().UTC()
		}
		sessions.mu.Unlock()
		if !ready {
			http.Error(w, "control session is not ready", http.StatusConflict)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]interface{}{"type": "SESSION_HEARTBEAT_ACK", "session_id": heartbeat.SessionID, "server_time": time.Now().UTC()})
	})
	mux.HandleFunc("/v1/control/task-heartbeat", func(w http.ResponseWriter, r *http.Request) {
		var heartbeat taskHeartbeatRequest
		if r.Method != http.MethodPost || json.NewDecoder(http.MaxBytesReader(w, r.Body, max)).Decode(&heartbeat) != nil || heartbeat.SessionID == "" || heartbeat.AttemptID == "" {
			http.Error(w, "task heartbeat rejected", http.StatusBadRequest)
			return
		}
		sessions.mu.Lock()
		record, ok := sessions.sessions[heartbeat.SessionID]
		ready := ok && record.Ready
		if ready {
			now := time.Now().UTC()
			record.LastSeen = now
			if heartbeat.SentAt.IsZero() {
				heartbeat.SentAt = now
			}
			record.TaskHeartbeats[heartbeat.AttemptID] = heartbeat.SentAt
		}
		sessions.mu.Unlock()
		if !ready {
			http.Error(w, "control session is not ready", http.StatusConflict)
			return
		}
		// The Edge reports liveness only. Central remains the lease authority.
		_ = json.NewEncoder(w).Encode(map[string]interface{}{"type": "TASK_HEARTBEAT_ACK", "session_id": heartbeat.SessionID, "attempt_id": heartbeat.AttemptID, "server_time": time.Now().UTC()})
	})
	mux.HandleFunc("/v1/control/task", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var e Envelope
		body := http.MaxBytesReader(w, r.Body, max)
		defer body.Close()
		if err := json.NewDecoder(body).Decode(&e); err != nil {
			http.Error(w, "invalid envelope", http.StatusBadRequest)
			return
		}
		if e.EdgeID == "" || e.EdgeID != s.EdgeID || e.Capability != "device.read.facts" || e.CredentialRef == "" {
			http.Error(w, "envelope rejected", http.StatusForbidden)
			return
		}
		sessionID := r.Header.Get("X-Edge-Session")
		sessions.mu.Lock()
		record, known := sessions.sessions[sessionID]
		ready := known && record.Ready
		if ready {
			record.LastSeen = time.Now().UTC()
		}
		sessions.mu.Unlock()
		if !ready {
			http.Error(w, "control session is not ready", http.StatusConflict)
			return
		}
		if e.ProtocolVersion != 1 || e.DriverCapabilityVersion != 1 || e.MessageID == "" || e.TaskID == "" || e.AttemptID == "" || e.IdempotencyKey == "" || len(e.Nonce) < 16 || e.RetryClass != "SAFE_RETRY" || e.ValidForSeconds < 1 || e.ValidForSeconds > 300 {
			http.Error(w, "envelope rejected", http.StatusBadRequest)
			return
		}
		now := time.Now()
		if now.Before(e.IssuedAt.Add(-30*time.Second)) || now.After(e.IssuedAt.Add(time.Duration(e.ValidForSeconds)*time.Second+30*time.Second)) {
			http.Error(w, "envelope expired", http.StatusBadRequest)
			return
		}
		if s.Handler == nil {
			http.Error(w, "handler not configured", http.StatusServiceUnavailable)
			return
		}
		journalKey := e.AttemptID + "\x00" + e.IdempotencyKey
		sessions.mu.Lock()
		if recorded, ok := sessions.attemptResults[journalKey]; ok {
			duplicate := make(map[string]interface{}, len(recorded)+1)
			for key, value := range recorded {
				duplicate[key] = value
			}
			duplicate["duplicate_delivery"] = true
			sessions.mu.Unlock()
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(duplicate)
			return
		}
		if sessions.inFlight[journalKey] {
			sessions.mu.Unlock()
			http.Error(w, "attempt is already executing", http.StatusConflict)
			return
		}
		sessions.inFlight[journalKey] = true
		sessions.mu.Unlock()
		result, err := s.Handler(r.Context(), e)
		if err != nil {
			sessions.mu.Lock()
			delete(sessions.inFlight, journalKey)
			sessions.mu.Unlock()
			http.Error(w, "execution failed", http.StatusBadGateway)
			return
		}
		sessions.mu.Lock()
		delete(sessions.inFlight, journalKey)
		sessions.attemptResults[journalKey] = result
		sessions.attemptOrder = append(sessions.attemptOrder, journalKey)
		for len(sessions.attemptOrder) > sessions.journalLimit {
			oldest := sessions.attemptOrder[0]
			sessions.attemptOrder = sessions.attemptOrder[1:]
			delete(sessions.attemptResults, oldest)
		}
		_ = sessions.persistJournalLocked()
		sessions.mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(result)
	})
	return mux
}

// loadJournalLocked restores terminal results only. In-flight state is never
// restored: Central must reconcile unresolved attempts after an Edge restart.
func (s *SessionRegistry) loadJournalLocked() error {
	if s.journalPath == "" {
		return nil
	}
	data, err := os.ReadFile(s.journalPath)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var results map[string]map[string]interface{}
	if err := json.Unmarshal(data, &results); err != nil {
		return err
	}
	for key, result := range results {
		s.attemptResults[key] = result
		s.attemptOrder = append(s.attemptOrder, key)
	}
	for len(s.attemptOrder) > s.journalLimit {
		oldest := s.attemptOrder[0]
		s.attemptOrder = s.attemptOrder[1:]
		delete(s.attemptResults, oldest)
	}
	return nil
}

// persistJournalLocked uses a same-directory temporary file and atomic rename.
func (s *SessionRegistry) persistJournalLocked() error {
	if s.journalPath == "" {
		return nil
	}
	data, err := json.Marshal(s.attemptResults)
	if err != nil {
		return err
	}
	temporary := s.journalPath + ".tmp"
	if err := os.WriteFile(temporary, data, 0600); err != nil {
		return err
	}
	return os.Rename(temporary, s.journalPath)
}

func (s Server) Serve(ctx context.Context, listener net.Listener) error {
	if s.TLSConfig == nil {
		return fmt.Errorf("mTLS config is required")
	}
	server := &http.Server{Handler: s.HTTPHandler(), ReadHeaderTimeout: 5 * time.Second}
	go func() { <-ctx.Done(); _ = server.Shutdown(context.Background()) }()
	return server.Serve(tls.NewListener(listener, s.TLSConfig))
}
