package security

import (
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
)

func LoadEd25519PrivateKey(path string) (ed25519.PrivateKey, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read journal signing key: %w", err)
	}
	block, _ := pem.Decode(data)
	if block == nil {
		return nil, fmt.Errorf("journal signing key is not PEM")
	}
	key, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse journal signing key: %w", err)
	}
	edKey, ok := key.(ed25519.PrivateKey)
	if !ok {
		return nil, fmt.Errorf("journal signing key is not Ed25519")
	}
	return edKey, nil
}

type MTLSFiles struct {
	CAFile          string
	CertificateFile string
	PrivateKeyFile  string
}

func loadCA(path string) (*x509.CertPool, error) {
	pem, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read CA file: %w", err)
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(pem) {
		return nil, fmt.Errorf("CA file contains no certificate")
	}
	return pool, nil
}

func loadCertificate(files MTLSFiles) (tls.Certificate, error) {
	cert, err := tls.LoadX509KeyPair(files.CertificateFile, files.PrivateKeyFile)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("load client certificate: %w", err)
	}
	return cert, nil
}

// ClientConfig requires mutual TLS and refuses insecure verification settings.
func ClientConfig(files MTLSFiles) (*tls.Config, error) {
	ca, err := loadCA(files.CAFile)
	if err != nil {
		return nil, err
	}
	cert, err := loadCertificate(files)
	if err != nil {
		return nil, err
	}
	return &tls.Config{MinVersion: tls.VersionTLS13, RootCAs: ca, Certificates: []tls.Certificate{cert}, ServerName: "central"}, nil
}

// ServerConfig requires a client certificate signed by the configured CA.
func ServerConfig(files MTLSFiles) (*tls.Config, error) {
	ca, err := loadCA(files.CAFile)
	if err != nil {
		return nil, err
	}
	cert, err := loadCertificate(files)
	if err != nil {
		return nil, err
	}
	return &tls.Config{MinVersion: tls.VersionTLS13, ClientCAs: ca, Certificates: []tls.Certificate{cert}, ClientAuth: tls.RequireAndVerifyClientCert}, nil
}
