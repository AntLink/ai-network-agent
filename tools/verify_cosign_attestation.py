"""Run cosign attestation verification with a hard process-group timeout."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    command = [
        "cosign",
        "verify-attestation",
        "--timeout",
        f"{args.timeout_seconds}s",
        "--max-workers",
        "1",
        args.image,
        "--type",
        "cyclonedx",
        "--certificate-identity-regexp",
        "https://github.com/AntLink/ai-network-agent/.*",
        "--certificate-oidc-issuer",
        "https://token.actions.githubusercontent.com",
    ]

    process = subprocess.Popen(command, start_new_session=(os.name != "nt"))
    try:
        return process.wait(timeout=args.timeout_seconds + 15)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        print(
            f"cosign attestation verification exceeded {args.timeout_seconds}s",
            file=sys.stderr,
        )
        return 124


if __name__ == "__main__":
    raise SystemExit(main())
