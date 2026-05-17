# DocuMind - Multi-Agent Documentation System Architecture

## Executive Summary

DocuMind is a production-grade multi-agent system that automatically generates and maintains comprehensive, contextually-aware documentation for codebases with natural language query capabilities. The system monitors code changes in real-time, understands architectural relationships, and produces living documentation that evolves with the codebase.

## Technology Stack (Free Tier Focus)

### Core Infrastructure
- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18+ with TypeScript
- **LLM Provider**: Ollama Cloud API (free tier)
- **Vector Database**: Pinecone (free tier - 1M vectors, 1 index)
- **Relational Database**: Supabase PostgreSQL with pgvector (free tier - 500MB)
- **Documentation Platform**: Notion API (free tier)
- **Version Control**: GitHub (webhooks + API)
- **Hosting**: Railway/Render (free tier) or self-hosted

### Key Libraries
- **LLM Orchestration**: LangChain, LangGraph
- **Code Analysis**: tree-sitter, ast (Python), esprima (JavaScript)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Git Operations**: GitPython
- **API Framework**: FastAPI, Pydantic
- **Vector Operations**: pinecone-client, pgvector
- **Search**: rank-bm25 (keyword search)
- **Frontend**: React, TanStack Query, Tailwind CSS

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Systems                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────────────┐      │
│  │  GitHub  │      │  Notion  │      │  Developer/User  │      │
│  │Repository│      │Workspace │      │                  │      │
│  └────┬─────┘      └────▲─────┘      └────────┬─────────┘      │
└───────┼─────────────────┼───────────────────────┼───────────────┘
        │                 │                       │
        │ Webhooks        │ API                   │ Queries
        │                 │                       │
┌───────▼─────────────────┴───────────────────────▼───────────────┐
│                      DocuMind Core System                        │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Ingestion Layer                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────────────┐       │   │
│  │  │ Webhook  │→ │   Git    │→ │    Change       │       │   │
│  │  │ Receiver │  │  Parser  │  │  Classifier     │       │   │
│  │  └──────────┘  └──────────┘  └─────────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Agent Layer                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │   │
│  │  │ Watcher  │→ │  Writer  │  │     Query        │      │   │
│  │  │  Agent   │  │  Agent   │  │     Agent        │      │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Intelligence Layer                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │   │
│  │  │  Ollama  │  │Embedding │  │     Pinecone     │      │   │
│  │  │  Cloud   │  │ Service  │  │  Vector Store    │      │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘      │   │
│  │                 ┌──────────────────────────────┐        │   │
│  │                 │  Supabase PostgreSQL         │        │   │
│  │                 │  with pgvector               │        │   │
│  │                 └──────────────────────────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Knowledge Layer                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │   │
│  │  │Code-Doc  │  │Staleness │  │   Dependency     │      │   │
│  │  │ Mapper   │  │ Detector │  │    Analyzer      │      │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Interface Layer                              │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐        │   │
│  │  │  FastAPI Backend │  │   React Frontend     │        │   │
│  │  │   REST + WS      │  │   Query Interface    │        │   │
│  │  └──────────────────┘  └──────────────────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Watcher Agent

**Purpose**: Monitor repository changes and generate structured change reports

**Responsibilities**:
- Receive GitHub webhook events (push, pull request)
- Parse Git commits to extract metadata
- Identify modified files, functions, classes, and dependencies
- Generate structured change reports with context
- Filter non-code changes intelligently
- Classify change types (feature, bugfix, refactor, breaking)

**Key Features**:
- AST-based code parsing using tree-sitter
- Multi-language support (Python, JavaScript, TypeScript, Go, Rust)
- Diff analysis with context extraction
- Import/dependency tracking
- Change impact scoring

**Data Flow**:
```
GitHub Push → Webhook → Parse Commit → Extract Changes → 
Classify Type → Generate Report → Queue for Writer Agent
```

### 2. Writer Agent

**Purpose**: Generate contextually-aware documentation from change reports

**Responsibilities**:
- Receive change reports from Watcher Agent
- Query vector store for related code context
- Perform impact analysis across codebase
- Generate comprehensive documentation
- Update existing documentation pages
- Maintain documentation versioning
- Publish to Notion with rich formatting

**Key Features**:
- Context-aware generation using RAG
- Multi-granularity embeddings (file, function, class)
- Semantic similarity for related code discovery
- Diff-based updates to preserve manual edits
- Documentation quality scoring
- Template-based generation for consistency

**Documentation Structure**:
```markdown
# [Component/Feature Name]

## Overview
Brief description of what changed and why

## Changes Made
- Detailed list of modifications
- Added/removed functionality
- Breaking changes (if any)

## Architecture Context
How this fits into the larger system

## Dependencies
- Upstream dependencies (what this relies on)
- Downstream dependencies (what relies on this)

## Usage Examples
```language
// Realistic code examples
```

## Edge Cases & Gotchas
Important considerations for developers

## Performance Implications
Impact on system performance (if relevant)

## Security Considerations
Security-related notes (if applicable)

## Related Documentation
Links to related pages and code files
```

### 3. Query Agent

**Purpose**: Provide natural language interface for documentation and code queries

**Responsibilities**:
- Accept natural language questions
- Perform hybrid search (semantic + keyword)
- Retrieve relevant code and documentation
- Synthesize coherent answers with citations
- Handle follow-up questions with context
- Provide direct links to source code and docs

**Key Features**:
- RAG-powered question answering
- Conversation history management
- Multi-source retrieval (code + docs)
- Citation with file paths and line numbers
- Streaming responses for better UX
- Query intent classification

**Query Flow**:
```
User Question → Intent Classification → Hybrid Search →
Context Retrieval → LLM Synthesis → Answer with Citations
```

## Data Models

### Change Report Schema

```python
class ChangeReport(BaseModel):
    commit_sha: str
    author: str
    timestamp: datetime
    message: str
    change_type: ChangeType  # feature, bugfix, refactor, breaking
    files_changed: List[FileChange]
    impact_score: float
    
class FileChange(BaseModel):
    path: str
    change_type: FileChangeType  # create, update, delete
    language: str
    diff: str
    symbols_added: List[Symbol]
    symbols_modified: List[Symbol]
    symbols_removed: List[Symbol]
    dependencies_changed: List[str]
    
class Symbol(BaseModel):
    name: str
    type: SymbolType  # function, class, method, variable
    line_start: int
    line_end: int
    signature: Optional[str]
```

### Documentation Page Schema

```python
class DocumentationPage(BaseModel):
    id: str
    notion_page_id: Optional[str]
    title: str
    content: str
    version: int
    created_at: datetime
    updated_at: datetime
    linked_code: List[CodeLink]
    tags: List[str]
    quality_score: float
    
class CodeLink(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    symbol_name: str
    commit_sha: str
```

### Vector Store Schema

```python
class CodeEmbedding(BaseModel):
    id: str
    content: str
    embedding: List[float]
    metadata: EmbeddingMetadata
    
class EmbeddingMetadata(BaseModel):
    type: str  # file, function, class, documentation
    file_path: str
    language: str
    symbol_name: Optional[str]
    line_range: Optional[Tuple[int, int]]
    commit_sha: str
    timestamp: datetime
```

## Database Schema (Supabase PostgreSQL)

```sql
-- Repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    default_branch TEXT DEFAULT 'main',
    webhook_secret TEXT,
    notion_workspace_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documentation pages table
CREATE TABLE documentation_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id),
    notion_page_id TEXT UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    version INTEGER DEFAULT 1,
    quality_score FLOAT,
    is_stale BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Code-documentation mappings
CREATE TABLE code_doc_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_page_id UUID REFERENCES documentation_pages(id),
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    symbol_name TEXT,
    commit_sha TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Change reports table
CREATE TABLE change_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id),
    commit_sha TEXT NOT NULL,
    author TEXT,
    message TEXT,
    change_type TEXT,
    impact_score FLOAT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query history table
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id),
    question TEXT NOT NULL,
    answer TEXT,
    sources JSONB,
    feedback INTEGER,  -- -1, 0, 1 for negative, neutral, positive
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documentation embeddings table
CREATE TABLE documentation_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documentation_page_id UUID REFERENCES documentation_pages(id),
    content TEXT NOT NULL,
    embedding vector(384),  -- all-MiniLM-L6-v2 dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX ON documentation_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## API Endpoints

### Webhook Endpoints

```
POST /webhooks/github
- Receive GitHub webhook events
- Verify signature
- Queue for processing

POST /webhooks/github/setup
- Setup webhook for a repository
- Generate webhook secret
- Configure webhook URL
```

### Repository Management

```
POST /api/repositories
- Register new repository
- Initialize vector store
- Create Notion workspace

GET /api/repositories
- List all registered repositories

GET /api/repositories/{id}
- Get repository details
- Show documentation coverage

DELETE /api/repositories/{id}
- Remove repository
- Clean up resources
```

### Documentation Endpoints

```
GET /api/documentation
- List all documentation pages
- Filter by repository, tags, staleness

GET /api/documentation/{id}
- Get specific documentation page
- Include linked code references

POST /api/documentation/regenerate
- Manually trigger documentation regeneration
- For specific files or entire repository

GET /api/documentation/coverage
- Get documentation coverage metrics
- Show undocumented code areas
```

### Query Endpoints

```
POST /api/query
- Submit natural language question
- Get answer with citations

GET /api/query/history
- Get query history
- Filter by repository

POST /api/query/feedback
- Submit feedback on query answer
- Used for improvement
```

### Analytics Endpoints

```
GET /api/analytics/coverage
- Documentation coverage percentage
- By module, file type, etc.

GET /api/analytics/staleness
- Staleness metrics
- Average time to update

GET /api/analytics/quality
- Documentation quality scores
- Identify low-quality docs
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Set up core infrastructure and basic change detection

**Tasks**:
1. Initialize project structure
2. Set up FastAPI backend with basic endpoints
3. Configure Supabase database with schema
4. Implement GitHub webhook receiver
5. Build Git commit parser
6. Create basic change report generation
7. Set up Pinecone vector database
8. Implement embedding service

**Deliverables**:
- Working webhook receiver
- Change detection for Python files
- Basic database schema
- Vector store integration

### Phase 2: Writer Agent (Weeks 3-4)

**Goal**: Implement documentation generation with context awareness

**Tasks**:
1. Integrate Ollama Cloud API
2. Build vector store query system
3. Implement RAG pipeline for context retrieval
4. Create documentation generation prompts
5. Integrate Notion API
6. Build documentation versioning
7. Implement diff-based updates
8. Add code-doc mapping system

**Deliverables**:
- Working Writer Agent
- Documentation generation for code changes
- Notion integration
- Basic context awareness

### Phase 3: Query Interface (Weeks 5-6)

**Goal**: Build natural language query system with frontend

**Tasks**:
1. Implement Query Agent with RAG
2. Build hybrid search system
3. Create React frontend
4. Implement streaming responses
5. Add conversation context management
6. Build citation system
7. Create query history tracking
8. Add feedback mechanism

**Deliverables**:
- Working query interface
- React frontend
- Natural language Q&A
- Source citations

### Phase 4: Advanced Features (Weeks 7-8)

**Goal**: Add intelligence and production-ready features

**Tasks**:
1. Implement dependency graph analyzer
2. Build staleness detection
3. Add documentation quality scoring
4. Implement intelligent scoping
5. Create conflict resolution
6. Add coverage metrics
7. Build monitoring and logging
8. Implement access control
9. Add multiple output formats
10. Create comprehensive tests

**Deliverables**:
- Production-ready system
- Advanced intelligence features
- Monitoring and metrics
- Complete test coverage

## Free Tier Limits & Optimization

### Ollama Cloud API
- **Limit**: Research needed (assumed rate limits)
- **Optimization**: 
  - Cache LLM responses for similar queries
  - Batch documentation generation
  - Use smaller models for simple tasks
  - Implement request queuing

### Pinecone Free Tier
- **Limit**: 1M vectors, 1 index, 1 pod
- **Optimization**:
  - Use efficient embedding model (384 dimensions)
  - Implement vector pruning for old code
  - Combine related embeddings
  - Use metadata filtering to reduce queries

### Supabase Free Tier
- **Limit**: 500MB database, 2GB bandwidth/month
- **Optimization**:
  - Store large content in Notion/files
  - Implement data archival
  - Use efficient indexing
  - Compress stored content

### Notion API Free Tier
- **Limit**: Rate limits (3 requests/second)
- **Optimization**:
  - Implement rate limiting
  - Batch updates where possible
  - Cache Notion content locally
  - Use exponential backoff

### GitHub API
- **Limit**: 5000 requests/hour (authenticated)
- **Optimization**:
  - Use webhooks instead of polling
  - Cache repository data
  - Implement conditional requests
  - Use GraphQL for efficient queries

## Monitoring & Observability

### Key Metrics

**System Health**:
- Webhook processing latency
- Documentation generation time
- Query response time
- Error rates by component
- API rate limit usage

**Documentation Quality**:
- Coverage percentage
- Average staleness time
- Quality scores distribution
- Manual edit frequency
- User feedback scores

**User Engagement**:
- Query volume
- Query success rate
- Documentation page views
- Feedback submission rate
- Time to find information

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "documentation_generated",
    extra={
        "commit_sha": commit_sha,
        "files_changed": len(files),
        "generation_time_ms": elapsed_ms,
        "quality_score": score,
        "notion_page_id": page_id
    }
)
```

### Alerting

- Webhook processing failures
- LLM API errors
- Vector store connection issues
- Documentation generation failures
- High staleness rates
- Low quality scores

## Security Considerations

### Webhook Security
- Verify GitHub webhook signatures
- Use HTTPS only
- Implement rate limiting
- Validate payload structure

### API Security
- JWT-based authentication
- API key management
- Rate limiting per user
- Input validation and sanitization

### Data Security
- Encrypt sensitive data at rest
- Use environment variables for secrets
- Implement access control
- Audit logging for sensitive operations

### Repository Access
- Respect GitHub permissions
- Use OAuth for user authentication
- Implement repository-level access control
- Validate user permissions before queries

## Deployment Strategy

### Development Environment
```bash
# Local development with Docker Compose
docker-compose up -d

# Services:
# - FastAPI backend (port 8000)
# - React frontend (port 3000)
# - PostgreSQL (port 5432)
# - Redis for caching (port 6379)
```

### Production Deployment

**Option 1: Railway (Free Tier)**
- Deploy FastAPI backend
- Deploy React frontend as static site
- Use Railway PostgreSQL
- Configure environment variables
- Set up custom domain

**Option 2: Render (Free Tier)**
- Web service for FastAPI
- Static site for React
- PostgreSQL database
- Background workers for agents

**Option 3: Self-Hosted**
- Docker Compose on VPS
- Nginx reverse proxy
- Let's Encrypt SSL
- Systemd for process management

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        run: railway up
```

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external services
- Test edge cases
- Aim for 80%+ coverage

### Integration Tests
- Test agent workflows
- Database operations
- API endpoints
- External service integration

### End-to-End Tests
- Full workflow testing
- Webhook to documentation
- Query to answer
- UI interaction tests

### Performance Tests
- Load testing for API
- Vector search performance
- Documentation generation speed
- Concurrent user handling

## Future Enhancements

### Short-term (3-6 months)
- Support for more programming languages
- Advanced code analysis (complexity, patterns)
- Documentation templates per project type
- Slack/Discord integration for notifications
- CLI tool for local usage

### Long-term (6-12 months)
- Multi-repository documentation
- Team collaboration features
- Custom LLM fine-tuning
- Advanced analytics dashboard
- IDE plugins (VSCode, JetBrains)
- Automated documentation testing
- Documentation translation
- Video documentation generation

## Success Metrics

### Primary Metrics
- **Time to Understanding**: Reduce onboarding time by 50%
- **Documentation Coverage**: Achieve 80%+ coverage of public APIs
- **Query Accuracy**: 90%+ relevant answers
- **Staleness**: Average update time < 1 hour
- **User Satisfaction**: 4.5+ rating out of 5

### Secondary Metrics
- Number of documentation pages generated
- Query volume and trends
- Manual edit frequency
- System uptime and reliability
- Cost per repository (should remain $0)

## Conclusion

DocuMind represents a comprehensive solution for automated documentation generation and maintenance. By leveraging free-tier services and intelligent design, the system provides enterprise-grade capabilities while remaining cost-effective. The phased implementation approach ensures steady progress with working deliverables at each stage.

The architecture is designed for scalability, allowing easy upgrades to paid tiers as usage grows, while maintaining the core functionality on free tiers for small to medium projects.