package credentials

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

type Entry struct {
	Username string `json:"username"`
	Password string `json:"password"`
	// HostKey is an SSH authorized-key line used for strict host verification.
	// It is provisioned with the credential and is never sent in task payloads.
	HostKey string `json:"host_key"`
}

type KeyStore struct{ entries map[string]Entry }

func Load(path string) (*KeyStore, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read local keystore: %w", err)
	}
	var entries map[string]Entry
	if err := json.Unmarshal(data, &entries); err != nil {
		return nil, fmt.Errorf("decode local keystore: %w", err)
	}
	return &KeyStore{entries: entries}, nil
}

func (k *KeyStore) Resolve(ref string) (Entry, error) {
	if ref == "" {
		return Entry{}, errors.New("credential_ref is required")
	}
	e, ok := k.entries[ref]
	if !ok || e.Username == "" {
		return Entry{}, errors.New("credential_ref is not provisioned")
	}
	return e, nil
}
