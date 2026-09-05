package credentials

import (
	"os"
	"path/filepath"
	"testing"
)

func TestKeystoreRequiresExplicitReference(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "credentials.json")
	if err := os.WriteFile(path, []byte(`{"cred-1":{"username":"lab"}}`), 0600); err != nil {
		t.Fatal(err)
	}
	k, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := k.Resolve(""); err == nil {
		t.Fatal("expected missing ref error")
	}
	if _, err := k.Resolve("cred-missing"); err == nil {
		t.Fatal("expected unknown ref error")
	}
	entry, err := k.Resolve("cred-1")
	if err != nil || entry.Username != "lab" {
		t.Fatalf("resolve failed: %#v %v", entry, err)
	}
}

func TestKeystoreLoadsPinnedHostKeyMetadata(t *testing.T) {
	path := filepath.Join(t.TempDir(), "credentials.json")
	if err := os.WriteFile(path, []byte(`{"cred-1":{"username":"lab","host_key":"ssh-rsa AAAA"}}`), 0600); err != nil {
		t.Fatal(err)
	}
	k, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	entry, err := k.Resolve("cred-1")
	if err != nil || entry.HostKey != "ssh-rsa AAAA" {
		t.Fatalf("pinned host key metadata not loaded: %#v %v", entry, err)
	}
}
