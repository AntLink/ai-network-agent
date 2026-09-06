"""Run the live PostgreSQL gate using the backend-local environment safely."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    values = dotenv_values(ROOT / "backend" / ".env")
    dsn = str(values.get("POSTGRES_DSN") or "")
    if not dsn:
        print("LIVE_POSTGRES=FAIL missing backend/.env POSTGRES_DSN")
        return 2
    # The application container uses host.docker.internal; this gate runs on
    # Windows host, where the local PostgreSQL listener is 127.0.0.1.
    dsn = dsn.replace("@host.docker.internal:", "@127.0.0.1:")
    env = os.environ.copy()
    env.update({"RUN_LIVE_POSTGRES": "1", "POSTGRES_DSN": dsn, "PYTHONPATH": "backend"})
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests/test_postgres_live.py", "-q"],
        cwd=ROOT,
        env=env,
        text=True,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
