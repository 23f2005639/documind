# DocuMind Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the DocuMind multi-agent documentation system.

## Prerequisites

### Required Accounts (All Free Tier)
1. **GitHub Account** - For repository access and webhooks
2. **Ollama Cloud Account** - For LLM API access
3. **Pinecone Account** - For vector database (free tier: 1M vectors)
4. **Supabase Account** - For PostgreSQL with pgvector (free tier: 500MB)
5. **Notion Account** - For documentation storage (free tier)

### Development Environment
- Python 3.11+
- Node.js 18+ and npm
- Git
- Docker (optional, for local development)
- Code editor (VSCode recommended)

## Phase 1: Foundation Setup (Week 1-2)

### Step 1: Project Structure

```bash
documind/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration management
│   │   ├── models/                 # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── change_report.py
│   │   │   ├── documentation.py
│   │   │   └── query.py
│   │   ├── agents/                 # Agent implementations
│   │   │   ├── __init__.py
│   │   │   ├── watcher.py
│   │   │   ├── writer.py
│   │   │   └── query.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── git_parser.py
│   │   │   ├── embedding.py
│   │   │   ├── vector_store.py
│   │   │   ├── llm.py
│   │   │   └── notion.py
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── webhooks.py
│   │   │   ├── repositories.py
│   │   │   ├── documentation.py
│   │   │   └── query.py
│   │   ├── db/                     # Database
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── migrations/
│   │   └── utils/                  # Utilities
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── security.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   └── test_api/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── QueryInterface.tsx
│   │   │   ├── DocumentationList.tsx
│   │   │   └── RepositoryManager.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Step 2: Backend Dependencies

Create `backend/requirements.txt`:

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
supabase==2.3.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.25

# Vector Store
pinecone-client==3.0.0
sentence-transformers==2.3.1

# LLM & AI
langchain==0.1.0
langchain-community==0.0.13
langgraph==0.0.20
openai==1.10.0  # For Ollama Cloud API compatibility

# Git Operations
GitPython==3.1.41
tree-sitter==0.20.4
tree-sitter-python==0.20.4
tree-sitter-javascript==0.20.3

# Notion Integration
notion-client==2.2.1

# Search
rank-bm25==0.2.2

# Utilities
python-dotenv==1.0.0
httpx==0.26.0
tenacity==8.2.3
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Monitoring
structlog==24.1.0
```

Create `backend/requirements-dev.txt`:

```txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==24.1.1
ruff==0.1.14
mypy==1.8.0
httpx==0.26.0
```

### Step 3: Environment Configuration

Create `.env.example`:

```bash
# Application
APP_NAME=DocuMind
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
DATABASE_URL=postgresql://user:password@host:port/database

# Vector Store (Pinecone)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=documind-vectors

# LLM (Ollama Cloud)
OLLAMA_API_KEY=your-ollama-api-key
OLLAMA_BASE_URL=https://api.ollama.cloud
OLLAMA_MODEL=llama3.1:8b

# Notion
NOTION_API_KEY=your-notion-integration-token
NOTION_DATABASE_ID=your-notion-database-id

# GitHub
GITHUB_APP_ID=your-github-app-id
GITHUB_PRIVATE_KEY=your-github-private-key
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
NOTION_RATE_LIMIT=3  # requests per second

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Step 4: Configuration Management

Create `backend/app/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    app_name: str = "DocuMind"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    
    # Database
    supabase_url: str
    supabase_key: str
    database_url: str
    
    # Vector Store
    pinecone_api_key: str
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "documind-vectors"
    
    # LLM
    ollama_api_key: str
    ollama_base_url: str = "https://api.ollama.cloud"
    ollama_model: str = "llama3.1:8b"
    
    # Notion
    notion_api_key: str
    notion_database_id: str
    
    # GitHub
    github_app_id: str
    github_private_key: str
    github_webhook_secret: str
    
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    notion_rate_limit: int = 3
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

### Step 5: Database Setup

Create `backend/app/db/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
from app.config import settings

# SQLAlchemy setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
```

Create `backend/app/db/schema.sql`:

```sql
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

-- Documentation embeddings table
CREATE TABLE IF NOT EXISTS documentation_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    documentation_page_id UUID REFERENCES documentation_pages(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_repositories_github_url ON repositories(github_url);
CREATE INDEX idx_documentation_pages_repository_id ON documentation_pages(repository_id);
CREATE INDEX idx_documentation_pages_is_stale ON documentation_pages(is_stale);
CREATE INDEX idx_code_doc_mappings_doc_id ON code_doc_mappings(documentation_page_id);
CREATE INDEX idx_code_doc_mappings_file_path ON code_doc_mappings(file_path);
CREATE INDEX idx_change_reports_repository_id ON change_reports(repository_id);
CREATE INDEX idx_change_reports_processed ON change_reports(processed);
CREATE INDEX idx_query_history_repository_id ON query_history(repository_id);
CREATE INDEX idx_query_history_session_id ON query_history(session_id);

-- Create vector similarity search index
CREATE INDEX ON documentation_embeddings USING ivfflat (embedding vector_cosine_ops)
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
CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documentation_pages_updated_at BEFORE UPDATE ON documentation_pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Step 6: FastAPI Application Setup

Create `backend/app/main.py`:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import init_db
from app.api import webhooks, repositories, documentation, query
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    logger.info("Starting DocuMind application")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocuMind application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Multi-agent documentation system with natural language queries",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env
    }


# Include routers
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(documentation.router, prefix="/api/documentation", tags=["documentation"])
app.include_router(query.router, prefix="/api/query", tags=["query"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
```

### Step 7: Logging Setup

Create `backend/app/utils/logger.py`:

```python
import structlog
import logging
from app.config import settings


def setup_logging():
    """Configure structured logging"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.getLevelName(settings.log_level),
    )
```

### Step 8: Frontend Setup

Create `frontend/package.json`:

```json
{
  "name": "documind-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.5",
    "zustand": "^4.4.7",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "lucide-react": "^0.303.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11"
  }
}
```

### Step 9: Docker Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/documind
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0 --port 3000

  db:
    image: ankane/pgvector:latest
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=documind
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

After completing Phase 1 setup:

1. **Test the basic setup**:
   ```bash
   # Start services
   docker-compose up -d
   
   # Check health
   curl http://localhost:8000/health
   ```

2. **Set up external services**:
   - Create Pinecone index
   - Set up Supabase project and run schema
   - Create Notion integration
   - Configure GitHub App

3. **Move to Phase 2**: Implement the Watcher Agent and Writer Agent

## Troubleshooting

### Common Issues

**Database connection errors**:
- Verify DATABASE_URL is correct
- Check if PostgreSQL is running
- Ensure pgvector extension is installed

**Import errors**:
- Verify all dependencies are installed
- Check Python version (3.11+)
- Rebuild Docker containers

**CORS errors**:
- Update CORS_ORIGINS in .env
- Check frontend URL matches

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Notion API Documentation](https://developers.notion.com/)