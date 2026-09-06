package control

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"math/big"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClientConnectUsesVerifiedMutualTLS(t *testing.T) {
	caCert, caKey := makeTestCA(t)
	serverCert, serverKey := signTestCertificate(t, "central", caCert, caKey, x509.ExtKeyUsageServerAuth)
	clientCert, clientKey := signTestCertificate(t, "edge-001", caCert, caKey, x509.ExtKeyUsageClientAuth)
	caPool := x509.NewCertPool()
	caPool.AddCert(caCert)
	serverTLS := tls.Certificate{Certificate: [][]byte{serverCert.Raw, caCert.Raw}, PrivateKey: serverKey}
	clientTLS := tls.Certificate{Certificate: [][]byte{clientCert.Raw, caCert.Raw}, PrivateKey: clientKey}

	server := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if len(r.TLS.PeerCertificates) != 2 || r.Header.Get("X-Client-Edge-ID") != "edge-001" {
			http.Error(w, "client identity missing", http.StatusUnauthorized)
			return
		}
		if r.URL.Path == "/v1/control/hello" {
			w.Header().Set("Content-Type", "application/json")
			_, _ = w.Write([]byte(`{"session_id":"session-mtls","reconciliation":{}}`))
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	server.TLS = &tls.Config{MinVersion: tls.VersionTLS13, Certificates: []tls.Certificate{serverTLS}, ClientCAs: caPool, ClientAuth: tls.RequireAndVerifyClientCert}
	server.StartTLS()
	defer server.Close()

	tlsConfig := &tls.Config{MinVersion: tls.VersionTLS13, RootCAs: caPool, Certificates: []tls.Certificate{clientTLS}, ServerName: "central"}
	client := &Client{BaseURL: server.URL, TLSConfig: tlsConfig, EdgeID: "edge-001", BootID: "boot-001"}
	if err := client.Connect(context.Background()); err != nil {
		t.Fatal(err)
	}
	if client.SessionID != "session-mtls" {
		t.Fatalf("session=%q", client.SessionID)
	}
}

func makeTestCA(t *testing.T) (*x509.Certificate, *rsa.PrivateKey) {
	t.Helper()
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	serial, _ := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 120))
	tmpl := &x509.Certificate{SerialNumber: serial, Subject: pkix.Name{CommonName: "test-ca"}, NotBefore: time.Now().Add(-time.Minute), NotAfter: time.Now().Add(time.Hour), BasicConstraintsValid: true, IsCA: true, KeyUsage: x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	raw, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := x509.ParseCertificate(raw)
	if err != nil {
		t.Fatal(err)
	}
	return cert, key
}

func signTestCertificate(t *testing.T, commonName string, ca *x509.Certificate, caKey *rsa.PrivateKey, usage x509.ExtKeyUsage) (*x509.Certificate, *rsa.PrivateKey) {
	t.Helper()
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	serial, _ := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 120))
	tmpl := &x509.Certificate{SerialNumber: serial, Subject: pkix.Name{CommonName: commonName}, DNSNames: []string{commonName}, NotBefore: time.Now().Add(-time.Minute), NotAfter: time.Now().Add(time.Hour), BasicConstraintsValid: true, KeyUsage: x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment, ExtKeyUsage: []x509.ExtKeyUsage{usage}}
	raw, err := x509.CreateCertificate(rand.Reader, tmpl, ca, &key.PublicKey, caKey)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := x509.ParseCertificate(raw)
	if err != nil {
		t.Fatal(err)
	}
	return cert, key
}
