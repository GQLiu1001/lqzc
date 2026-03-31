-- Tao AI demo schema for PostgreSQL + pgvector
-- Usage:
--   createdb tao_ai_demo
--   psql -h localhost -p 5432 -U postgres -d tao_ai_demo -f sql/tao_ai_pgvector_demo.sql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ai_files (
    id UUID PRIMARY KEY,
    session_id TEXT,
    original_name TEXT NOT NULL,
    saved_name TEXT NOT NULL,
    local_path TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT,
    sha256 CHAR(64),
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_file_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id UUID NOT NULL REFERENCES ai_files(id) ON DELETE CASCADE,
    chunk_no INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(file_id, chunk_no)
);

CREATE INDEX IF NOT EXISTS idx_ai_files_session_id ON ai_files(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_files_status ON ai_files(status);
CREATE INDEX IF NOT EXISTS idx_ai_file_chunks_file_id ON ai_file_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_ai_file_chunks_metadata ON ai_file_chunks USING GIN(metadata);

DROP INDEX IF EXISTS idx_ai_chunks_embedding_ivfflat;
ALTER TABLE ai_file_chunks
ALTER COLUMN embedding TYPE vector
USING embedding::vector;

