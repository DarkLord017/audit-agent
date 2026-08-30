CREATE TABLE IF NOT EXISTS jobs (
    id            uuid PRIMARY KEY,
    status        TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','timed_out')),
    model         TEXT NOT NULL,
    upload_path   TEXT NOT NULL,
    container_id  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    error         TEXT,
    report        JSONB,
    input_tokens  BIGINT NOT NULL DEFAULT 0,
    output_tokens BIGINT NOT NULL DEFAULT 0,
    cost_usd      NUMERIC(12,6) NOT NULL DEFAULT 0,
    budget_usd    NUMERIC(12,6) NOT NULL DEFAULT 15.0
);

CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at DESC);
