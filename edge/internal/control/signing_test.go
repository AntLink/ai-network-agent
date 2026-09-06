package control

import (
	"crypto/ed25519"
	"encoding/base64"
	"testing"
)

func TestGoVerifiesCrossRuntimeEd25519Vector(t *testing.T) {
	publicKey, err := base64.RawURLEncoding.DecodeString("A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg")
	if err != nil {
		t.Fatal(err)
	}
	signature, err := base64.RawURLEncoding.DecodeString("5FrW5WF3N3VIKNQuIw_0uy7kXSbLhqdpQizh5oBcxA_b3OYbaBpqy5uabf_QXh-YrcZnR_UVx2h7nmsUNSjzDw")
	if err != nil {
		t.Fatal(err)
	}
	canonical, err := canonicalSummary(JournalAttemptSummary{AttemptID: "attempt-vector-1", IdempotencyKey: "idem-vector-1", Status: "UNKNOWN", ResultAvailable: false})
	if err != nil {
		t.Fatal(err)
	}
	if !ed25519.Verify(ed25519.PublicKey(publicKey), canonical, signature) {
		t.Fatal("cross-runtime signature vector did not verify")
	}
}
