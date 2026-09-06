-- V5 TaskAttempt durable lease state. Apply through the deployment migration tool.
CREATE TABLE IF NOT EXISTS task_attempts (
    attempt_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    edge_id TEXT,
    lease_owner TEXT NOT NULL DEFAULT 'CENTRAL',
    status TEXT NOT NULL,
    retry_class TEXT NOT NULL,
    execution_fingerprint TEXT,
    accepted_at TIMESTAMPTZ NOT NULL,
    deadline_at TIMESTAMPTZ NOT NULL,
    lease_expires_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    heartbeat_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    result JSONB,
    error_code TEXT,
    device_id TEXT,
    capability TEXT,
    credential_ref TEXT,
    execution_location TEXT,
    retry_decision TEXT,
    retry_reason TEXT,
    retry_evaluated_at TIMESTAMPTZ,
    retry_operator TEXT,
    operator_approval_ref TEXT,
    operator_approval_token_hash TEXT,
    replay_parent_attempt_id TEXT,
    execution_status TEXT,
    CONSTRAINT task_attempts_lease_owner_central CHECK (lease_owner = 'CENTRAL')
);

ALTER TABLE task_attempts
    ADD COLUMN IF NOT EXISTS replay_parent_attempt_id TEXT,
    ADD COLUMN IF NOT EXISTS execution_status TEXT,
    ADD COLUMN IF NOT EXISTS credential_ref TEXT;

CREATE INDEX IF NOT EXISTS idx_task_attempts_lease_expiry
    ON task_attempts (lease_expires_at)
    WHERE status IN ('QUEUED', 'DISPATCHING', 'RUNNING');

CREATE UNIQUE INDEX IF NOT EXISTS uq_task_attempts_idempotency_key
    ON task_attempts (idempotency_key);
