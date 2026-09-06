"""Keep unit/API tests deterministic when the developer .env enables Postgres.

Live PostgreSQL tests must opt in explicitly rather than changing the shared
unit-test contract or writing test attempts into a developer database.
"""
import os


if os.getenv("RUN_LIVE_POSTGRES") != "1":
    os.environ["TASK_ATTEMPT_BACKEND"] = "memory"
