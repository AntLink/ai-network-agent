# PostgreSQL Evidence

Required evidence: migration application, concurrent lease claim, renewal,
expiry recovery, and restore test. No live evidence has been recorded yet.

Collection procedure:

1. Use an approved staging PostgreSQL database and set `RUN_LIVE_POSTGRES=1`
   plus `POSTGRES_DSN` only in the operator environment.
2. Apply `backend/migrations/001_task_attempts.sql` and record the migration
   result without recording the DSN or credentials.
3. Run `backend/tests/test_postgres_live.py`; retain the test output and
   database schema/version evidence here.
4. Perform a controlled backup, restore into an isolated database, and rerun
   the lease/recovery checks. Record timestamps, database identifiers, and
   results only—never passwords or connection strings.

Current evidence: `postgres-live-20260905.json` (`PASS` for migration,
concurrency, renewal, expiry recovery, and isolated restore).

The production gate remains `NOT READY` until the restore drill and all other
required evidence are independently reviewable.
