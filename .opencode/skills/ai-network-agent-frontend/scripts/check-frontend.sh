#!/usr/bin/env bash
set -euo pipefail

if [ ! -f package.json ]; then
  echo "package.json not found. Run this from the frontend project root." >&2
  exit 1
fi

npm run lint
npm run build
