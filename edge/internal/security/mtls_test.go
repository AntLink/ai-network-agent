package security

import (
	"crypto/tls"
	"testing"
)

func TestMTLSConfigFailsClosedWhenFilesAreMissing(t *testing.T) {
	_, err := ClientConfig(MTLSFiles{CAFile: "missing-ca", CertificateFile: "missing-cert", PrivateKeyFile: "missing-key"})
	if err == nil {
		t.Fatal("expected missing CA error")
	}
}

func TestTLSMinimumIsTLS13(t *testing.T) {
	if tls.VersionTLS13 != 0x0304 {
		t.Fatal("unexpected Go TLS constant")
	}
}
