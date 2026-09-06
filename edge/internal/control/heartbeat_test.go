package control

import (
	"context"
	"sync"
	"testing"
	"time"
)

type recordingSender struct {
	mu       sync.Mutex
	presence int
	tasks    map[string]int
}

func (r *recordingSender) SendPresenceHeartbeat(context.Context, PresenceHeartbeat) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.presence++
	return nil
}

func (r *recordingSender) SendTaskHeartbeat(_ context.Context, heartbeat TaskHeartbeat) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.tasks == nil {
		r.tasks = map[string]int{}
	}
	r.tasks[heartbeat.AttemptID]++
	return nil
}

func TestHeartbeatSchedulerSeparatesPresenceAndTaskAttempts(t *testing.T) {
	sender := &recordingSender{}
	scheduler := &HeartbeatScheduler{
		Sender:           sender,
		Presence:         PresenceHeartbeat{SessionID: "session-1", EdgeID: "edge-1", BootID: "boot-1"},
		PresenceInterval: 5 * time.Millisecond,
		TaskInterval:     7 * time.Millisecond,
	}
	scheduler.TrackAttempt("attempt-1")
	ctx, cancel := context.WithTimeout(context.Background(), 45*time.Millisecond)
	defer cancel()
	scheduler.Start(ctx)
	<-ctx.Done()

	sender.mu.Lock()
	defer sender.mu.Unlock()
	if sender.presence == 0 {
		t.Fatal("expected presence heartbeat")
	}
	if sender.tasks["attempt-1"] == 0 {
		t.Fatal("expected task heartbeat")
	}
	if sender.tasks["attempt-1"] < 1 {
		t.Fatal("expected task heartbeat count")
	}
}

func TestHeartbeatSchedulerDoesNotTrackEmptyAttempt(t *testing.T) {
	scheduler := &HeartbeatScheduler{}
	scheduler.TrackAttempt("")
	scheduler.UntrackAttempt("")
	scheduler.UntrackAttempt("missing")
	if len(scheduler.attempts) != 0 {
		t.Fatal("empty attempt must not be tracked")
	}
}
