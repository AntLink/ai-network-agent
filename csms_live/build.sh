#!/bin/bash
set -e

VERSION=${VERSION:-$(git describe --tags --always 2>/dev/null || echo "0.2.0")}
LDFLAGS="-s -w -X main.version=${VERSION}"

export GOOS=linux
export GOARCH=arm
export GOARM=7
export CGO_ENABLED=0

go build -trimpath -o csms-bridge-armv7 -ldflags="${LDFLAGS}" .
echo "Build complete: csms-bridge-armv7 (${VERSION})"
