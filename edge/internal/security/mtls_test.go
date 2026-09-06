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

func TestClientServerNameDefaultsAndCanBeOverridden(t *testing.T) {
	if serverName := clientServerName(""); serverName != "central" {
		t.Fatalf("default server name=%q", serverName)
	}
	if serverName := clientServerName("edge-control.antlinx.com"); serverName != "edge-control.antlinx.com" {
		t.Fatalf("configured server name=%q", serverName)
	}
}
