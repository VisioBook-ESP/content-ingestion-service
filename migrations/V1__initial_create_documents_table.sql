-- V1: Initial create documents table
-- Equivalent to alembic revision f5a76b96de87

CREATE TABLE IF NOT EXISTS documents (
    id          UUID PRIMARY KEY,
    file_id     VARCHAR(255) NOT NULL,
    project_id  VARCHAR(255),
    file_name   VARCHAR(500),
    file_type   VARCHAR(50),
    status      VARCHAR(50),
    processed_at TIMESTAMPTZ,
    data        JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_file_id       ON documents (file_id);
CREATE        INDEX IF NOT EXISTS ix_documents_project_id    ON documents (project_id);
CREATE        INDEX IF NOT EXISTS ix_documents_status        ON documents (status);
CREATE        INDEX IF NOT EXISTS ix_documents_project_status ON documents (project_id, status);
