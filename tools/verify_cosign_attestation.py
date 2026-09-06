"""Run cosign attestation verification with a hard process-group timeout."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time


def run_bounded(command: list[str], timeout_seconds: int) -> int:
    print(f"Running: {' '.join(command)}", flush=True)
    process = subprocess.Popen(command, start_new_session=(os.name != "nt"))
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print(
            f"command exceeded {timeout_seconds}s: {' '.join(command[:3])}",
            file=sys.stderr,
        )
        return 124


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    verify_command = [
        "cosign",
        "verify-attestation",
        "--timeout",
        f"{args.timeout_seconds}s",
        "--max-workers",
        "1",
        "--type",
        "cyclonedx",
        "--certificate-identity-regexp",
        "https://github.com/AntLink/ai-network-agent/.*",
        "--certificate-oidc-issuer",
        "https://token.actions.githubusercontent.com",
        args.image,
    ]
    started = time.monotonic()
    result = run_bounded(verify_command, args.timeout_seconds)
    print(f"Cosign verification exited with {result} after {time.monotonic() - started:.1f}s", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
