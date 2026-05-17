-- DocuMind Database Schema
-- PostgreSQL with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    default_branch TEXT DEFAULT 'main',
    webhook_secret TEXT,
    notion_workspace_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documentation pages table
CREATE TABLE IF NOT EXISTS documentation_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    notion_page_id TEXT UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    version INTEGER DEFAULT 1,
    quality_score FLOAT,
    is_stale BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code-documentation mappings
CREATE TABLE IF NOT EXISTS code_doc_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    documentation_page_id UUID REFERENCES documentation_pages(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    symbol_name TEXT,
    symbol_type TEXT,
    commit_sha TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(documentation_page_id, file_path, symbol_name)
);

-- Change reports table
CREATE TABLE IF NOT EXISTS change_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    author TEXT,
    message TEXT,
    change_type TEXT,
    impact_score FLOAT,
    files_changed JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repository_id, commit_sha)
);

-- Query history table
CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    session_id TEXT,
    question TEXT NOT NULL,
    answer TEXT,
    sources JSONB,
    feedback INTEGER CHECK (feedback IN (-1, 0, 1)),
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documentation embeddings table (for pgvector fallback)
CREATE TABLE IF NOT EXISTS documentation_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    documentation_page_id UUID REFERENCES documentation_pages(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_repositories_github_url ON repositories(github_url);
CREATE INDEX IF NOT EXISTS idx_repositories_is_active ON repositories(is_active);

CREATE INDEX IF NOT EXISTS idx_documentation_pages_repository_id ON documentation_pages(repository_id);
CREATE INDEX IF NOT EXISTS idx_documentation_pages_is_stale ON documentation_pages(is_stale);
CREATE INDEX IF NOT EXISTS idx_documentation_pages_notion_page_id ON documentation_pages(notion_page_id);

CREATE INDEX IF NOT EXISTS idx_code_doc_mappings_doc_id ON code_doc_mappings(documentation_page_id);
CREATE INDEX IF NOT EXISTS idx_code_doc_mappings_file_path ON code_doc_mappings(file_path);
CREATE INDEX IF NOT EXISTS idx_code_doc_mappings_commit_sha ON code_doc_mappings(commit_sha);

CREATE INDEX IF NOT EXISTS idx_change_reports_repository_id ON change_reports(repository_id);
CREATE INDEX IF NOT EXISTS idx_change_reports_processed ON change_reports(processed);
CREATE INDEX IF NOT EXISTS idx_change_reports_commit_sha ON change_reports(commit_sha);

CREATE INDEX IF NOT EXISTS idx_query_history_repository_id ON query_history(repository_id);
CREATE INDEX IF NOT EXISTS idx_query_history_session_id ON query_history(session_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at);

-- Create vector similarity search index (IVFFlat)
CREATE INDEX IF NOT EXISTS idx_documentation_embeddings_vector 
ON documentation_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
DROP TRIGGER IF EXISTS update_repositories_updated_at ON repositories;
CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_documentation_pages_updated_at ON documentation_pages;
CREATE TRIGGER update_documentation_pages_updated_at 
    BEFORE UPDATE ON documentation_pages
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- View: Repository statistics
CREATE OR REPLACE VIEW repository_stats AS
SELECT 
    r.id,
    r.name,
    r.github_url,
    COUNT(DISTINCT dp.id) as total_docs,
    COUNT(DISTINCT CASE WHEN dp.is_stale THEN dp.id END) as stale_docs,
    AVG(dp.quality_score) as avg_quality_score,
    COUNT(DISTINCT cr.id) as total_commits,
    COUNT(DISTINCT CASE WHEN cr.processed THEN cr.id END) as processed_commits
FROM repositories r
LEFT JOIN documentation_pages dp ON r.id = dp.repository_id
LEFT JOIN change_reports cr ON r.id = cr.repository_id
GROUP BY r.id, r.name, r.github_url;

-- View: Documentation coverage
CREATE OR REPLACE VIEW documentation_coverage AS
SELECT 
    r.id as repository_id,
    r.name as repository_name,
    COUNT(DISTINCT cdm.file_path) as documented_files,
    COUNT(DISTINCT dp.id) as total_docs,
    AVG(dp.quality_score) as avg_quality
FROM repositories r
LEFT JOIN documentation_pages dp ON r.id = dp.repository_id
LEFT JOIN code_doc_mappings cdm ON dp.id = cdm.documentation_page_id
GROUP BY r.id, r.name;

-- Comments
COMMENT ON TABLE repositories IS 'Stores registered GitHub repositories';
COMMENT ON TABLE documentation_pages IS 'Stores generated documentation pages';
COMMENT ON TABLE code_doc_mappings IS 'Maps code locations to documentation pages';
COMMENT ON TABLE change_reports IS 'Stores parsed commit change reports';
COMMENT ON TABLE query_history IS 'Stores user query history and feedback';
COMMENT ON TABLE documentation_embeddings IS 'Stores vector embeddings for semantic search';

-- Made with Bob
