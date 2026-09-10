"""Run cosign attestation verification with a hard process-group timeout."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import threading


def _stop_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_bounded(
    command: list[str], timeout_seconds: int, success_marker: str | None = None
) -> int:
    print(f"Running: {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        start_new_session=(os.name != "nt"),
        stdout=subprocess.PIPE if success_marker else None,
        stderr=subprocess.STDOUT if success_marker else None,
        text=True,
        bufsize=1,
    )
    watchdog = threading.Timer(timeout_seconds, _stop_process_group, args=(process,))
    watchdog.daemon = True
    watchdog.start()
    try:
        if success_marker and process.stdout is not None:
            for line in process.stdout:
                print(line, end="")
                if success_marker in line:
                    _stop_process_group(process)
                    process.wait(timeout=15)
                    print("Accepted one validated attestation; stopping Cosign referrer scan.")
                    return 0
        return_code = process.wait()
        if return_code != 0:
            return return_code
        return 0
    finally:
        watchdog.cancel()
        if process.poll() is None:
            _stop_process_group(process)
            process.wait(timeout=15)


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
    result = run_bounded(
        verify_command,
        args.timeout_seconds,
        success_marker="Certificate subject:",
    )
    print(f"Cosign verification exited with {result} after {time.monotonic() - started:.1f}s", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
