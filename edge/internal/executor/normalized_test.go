package executor

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestNormalizeCiscoFacts(t *testing.T) {
	_, currentFile, _, _ := runtime.Caller(0)
	vectorPath := filepath.Join(filepath.Dir(currentFile), "..", "..", "..", "docs", "contracts", "cisco-facts-vector.json")
	data, err := os.ReadFile(vectorPath)
	if err != nil {
		t.Fatal(err)
	}
	var vector struct {
		Raw      string                 `json:"raw"`
		Expected map[string]interface{} `json:"expected"`
	}
	if err := json.Unmarshal(data, &vector); err != nil {
		t.Fatal(err)
	}
	got := NormalizeCiscoFacts(vector.Raw)
	for key, expected := range vector.Expected {
		if got[key] != expected {
			t.Fatalf("field %s: got %#v, want %#v", key, got[key], expected)
		}
	}
}
