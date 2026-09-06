package control

import (
	"context"
	"fmt"
	"os"
	"sync"
	"time"
)

// PresenceHeartbeat identifies the Edge session whose liveness is being reported.
type PresenceHeartbeat struct {
	SessionID string `json:"session_id"`
	EdgeID    string `json:"edge_id"`
	BootID    string `json:"boot_id"`
}

// TaskHeartbeat identifies one active execution. It carries no lease authority.
type TaskHeartbeat struct {
	SessionID string    `json:"session_id"`
	AttemptID string    `json:"attempt_id"`
	SentAt    time.Time `json:"sent_at,omitempty"`
}

// HeartbeatSender is implemented by the authenticated Central control transport.
// Implementations must treat task heartbeat as an observation, not a lease grant.
type HeartbeatSender interface {
	SendPresenceHeartbeat(context.Context, PresenceHeartbeat) error
	SendTaskHeartbeat(context.Context, TaskHeartbeat) error
}

// HeartbeatScheduler keeps Edge presence and active TaskAttempt liveness on
// separate schedules. A failed send is intentionally ignored so one transient
// transport failure cannot stop future heartbeats.
type HeartbeatScheduler struct {
	Sender           HeartbeatSender
	Presence         PresenceHeartbeat
	PresenceInterval time.Duration
	TaskInterval     time.Duration
	ErrorSink        func(error)

	mu       sync.Mutex
	attempts map[string]struct{}
}

func (s *HeartbeatScheduler) report(err error) {
	if err != nil && s.ErrorSink != nil {
		fmt.Fprintf(os.Stderr, "heartbeat send error: %v\n", err)
		s.ErrorSink(err)
	}
}

func (s *HeartbeatScheduler) TrackAttempt(attemptID string) {
	if attemptID == "" {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.attempts == nil {
		s.attempts = map[string]struct{}{}
	}
	s.attempts[attemptID] = struct{}{}
}

func (s *HeartbeatScheduler) UntrackAttempt(attemptID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.attempts, attemptID)
}

func (s *HeartbeatScheduler) Start(ctx context.Context) {
	if s.Sender == nil {
		return
	}
	presenceInterval := s.PresenceInterval
	if presenceInterval <= 0 {
		presenceInterval = 15 * time.Second
	}
	taskInterval := s.TaskInterval
	if taskInterval <= 0 {
		taskInterval = 10 * time.Second
	}
	go s.runPresence(ctx, presenceInterval)
	go s.runTasks(ctx, taskInterval)
}

func (s *HeartbeatScheduler) runPresence(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			s.report(s.Sender.SendPresenceHeartbeat(ctx, s.Presence))
		}
	}
}

func (s *HeartbeatScheduler) runTasks(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case now := <-ticker.C:
			s.mu.Lock()
			attempts := make([]string, 0, len(s.attempts))
			for attemptID := range s.attempts {
				attempts = append(attempts, attemptID)
			}
			s.mu.Unlock()
			for _, attemptID := range attempts {
				s.report(s.Sender.SendTaskHeartbeat(ctx, TaskHeartbeat{SessionID: s.Presence.SessionID, AttemptID: attemptID, SentAt: now.UTC()}))
			}
		}
	}
}
