"""Run cosign attestation verification with a hard process-group timeout."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading


def _kill_process_group(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_bounded(command: list[str], timeout_seconds: int) -> int:
    process = subprocess.Popen(command, start_new_session=(os.name != "nt"))
    watchdog = threading.Timer(args.timeout_seconds, _kill_process_group, args=(process,))
    watchdog.daemon = True
    watchdog.start()
    try:
        return_code = process.wait()
    finally:
        watchdog.cancel()

    if return_code == -signal.SIGKILL:
        print(
            f"command exceeded {timeout_seconds}s: {' '.join(command[:3])}",
            file=sys.stderr,
        )
        return 124
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="cosign-oci-") as layout:
        save_result = run_bounded(
            ["cosign", "save", "--dir", layout, args.image],
            args.timeout_seconds,
        )
        if save_result != 0:
            return save_result

        verify_command = [
            "cosign",
            "verify-attestation",
            "--local-image",
            layout,
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
        ]
        return run_bounded(verify_command, args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
