-- Reconstructed backend schema (PostgreSQL). Matches backend/models/*.py.
CREATE TABLE IF NOT EXISTS submissions (
    id          SERIAL PRIMARY KEY,
    form_slug   VARCHAR(120) NOT NULL,
    data        JSON NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_submissions_form_slug ON submissions (form_slug);

CREATE TABLE IF NOT EXISTS app_users (
    id             SERIAL PRIMARY KEY,
    identity       VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES app_users (id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_auth_tokens_user_id ON auth_tokens (user_id);

CREATE TABLE IF NOT EXISTS api_snapshots (
    id            SERIAL PRIMARY KEY,
    path          VARCHAR(512) NOT NULL,
    query         VARCHAR(1024) NOT NULL DEFAULT '',
    status        INTEGER NOT NULL DEFAULT 200,
    content_type  VARCHAR(120) NOT NULL DEFAULT 'application/json',
    body          JSON NOT NULL,
    source_url    VARCHAR(1024),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_api_snapshots_path_query UNIQUE (path, query)
);
CREATE INDEX IF NOT EXISTS ix_api_snapshots_path ON api_snapshots (path);
