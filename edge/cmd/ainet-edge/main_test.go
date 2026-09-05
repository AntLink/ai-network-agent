package main

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func validEnvelope(now time.Time) Envelope {
	return Envelope{ProtocolVersion: 1, MessageID: "m1", TaskID: "t1", AttemptID: "a1", EdgeID: "e1", Nonce: strings.Repeat("n", 16), IssuedAt: now, ValidForSeconds: 60, RetryClass: "SAFE_RETRY", Capability: "device.read.facts"}
}

func TestRejectsReplayWindowAndUnsupportedCapability(t *testing.T) {
	now := time.Date(2026, 9, 3, 0, 0, 0, 0, time.UTC)
	e := validEnvelope(now)
	if err := validate(e, now.Add(91*time.Second)); err == nil {
		t.Fatal("expected expired message")
	}
	e = validEnvelope(now)
	e.Capability = "command.exec"
	if err := validate(e, now); err == nil {
		t.Fatal("expected unsupported capability")
	}
}

func TestDuplicateAttemptReturnsJournaledResult(t *testing.T) {
	now := time.Date(2026, 9, 3, 0, 0, 0, 0, time.UTC)
	e := validEnvelope(now)
	j := &Journal{results: map[string]map[string]interface{}{}}
	one := execute(e, j, now)
	two := execute(e, j, now)
	if one["attempt_id"] != two["attempt_id"] || one["status"] != two["status"] {
		t.Fatalf("duplicate result mismatch: %#v %#v", one, two)
	}
}

func TestJSONLineRunnerRejectsInvalidAndReturnsBoundedResult(t *testing.T) {
	now := time.Date(2026, 9, 3, 0, 0, 0, 0, time.UTC)
	e := validEnvelope(now)
	var in bytes.Buffer
	_ = json.NewEncoder(&in).Encode(e)
	var out bytes.Buffer
	if err := run(&in, &out, func() time.Time { return now }); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(out.String(), "NOT_CONFIGURED") {
		t.Fatalf("unexpected output: %s", out.String())
	}
}
