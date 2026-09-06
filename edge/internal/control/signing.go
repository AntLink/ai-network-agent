package control

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"fmt"
)

func canonicalSummary(summary JournalAttemptSummary) ([]byte, error) {
	payload := map[string]interface{}{
		"attempt_id":       summary.AttemptID,
		"idempotency_key":  summary.IdempotencyKey,
		"status":           summary.Status,
		"result_available": summary.ResultAvailable,
	}
	if summary.AttemptID == "" || summary.IdempotencyKey == "" || summary.Status == "" {
		return nil, fmt.Errorf("journal summary identity/status is required")
	}
	return json.Marshal(payload)
}

func signSummary(summary JournalAttemptSummary, key ed25519.PrivateKey) (JournalAttemptSummary, error) {
	canonical, err := canonicalSummary(summary)
	if err != nil {
		return JournalAttemptSummary{}, err
	}
	signed := summary
	signed.Signature = base64.RawURLEncoding.EncodeToString(ed25519.Sign(key, canonical))
	return signed, nil
}
