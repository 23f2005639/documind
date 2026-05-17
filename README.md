# DocuMind 🧠📚

> **Production-grade multi-agent system for automatic codebase documentation with natural language queries**

DocuMind automatically generates and maintains comprehensive, contextually-aware documentation for your codebases. It monitors code changes in real-time, understands architectural relationships, and produces living documentation that evolves with your code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Watcher Agent**: Monitors repository changes via GitHub webhooks
- **Writer Agent**: Generates context-aware documentation using AI
- **Query Agent**: Answers questions about your codebase in natural language

### 📝 Intelligent Documentation
- **Automatic Generation**: Creates documentation from code changes
- **Context-Aware**: Understands architectural relationships
- **Living Documentation**: Updates automatically with code changes
- **Rich Formatting**: Notion-compatible with syntax highlighting

### 🔍 Natural Language Queries
- **Semantic Search**: Find information using natural language
- **Source Citations**: Direct links to code and documentation
- **Conversation Context**: Follow-up questions with memory
- **Multi-Source**: Searches both code and documentation

### 🎯 Advanced Intelligence
- **Impact Analysis**: Traces how changes propagate through codebase
- **Staleness Detection**: Flags outdated documentation
- **Quality Scoring**: Evaluates documentation completeness
- **Dependency Tracking**: Maps code relationships

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Docker (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/documind.git
cd documind
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start with Docker Compose** (Recommended)
```bash
docker-compose up -d
```

Or **manual setup**:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📖 Documentation

- [**Architecture Guide**](ARCHITECTURE.md) - System design and components
- [**Implementation Guide**](IMPLEMENTATION_GUIDE.md) - Step-by-step setup
- [**Free Tier Strategy**](FREE_TIER_STRATEGY.md) - Zero-cost deployment
- [**Ollama Integration**](OLLAMA_INTEGRATION.md) - LLM setup and optimization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DocuMind System                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  GitHub Repository                                           │
│         ↓ (webhooks)                                         │
│  Watcher Agent → Change Detection → Classification          │
│         ↓                                                     │
│  Writer Agent → Context Retrieval → Documentation           │
│         ↓                                                     │
│  Notion Workspace ← Rich Formatting ← Version Control       │
│                                                               │
│  User Query → Query Agent → Hybrid Search → Answer          │
│         ↑                        ↓                            │
│  React Frontend ← WebSocket ← FastAPI Backend               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM**: Groq API (free tier) with Ollama fallback
- **Vector DB**: Qdrant Cloud (free tier)
- **Database**: Supabase PostgreSQL with pgvector
- **Embeddings**: sentence-transformers
- **Code Analysis**: tree-sitter

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Styling**: Tailwind CSS
- **UI Components**: Custom + Lucide icons

### Infrastructure
- **Hosting**: Railway (backend) + Vercel (frontend)
- **Documentation**: Notion API
- **Version Control**: GitHub
- **Caching**: Upstash Redis
- **Monitoring**: Better Stack

## 💰 Cost Structure

### Free Tier (Recommended for MVP)
- **LLM**: Groq (14,400 requests/day) - $0
- **Vector DB**: Qdrant Cloud (1GB) - $0
- **Database**: Supabase (500MB) - $0
- **Hosting**: Railway + Vercel - $0
- **Documentation**: Notion - $0
- **Total**: **$0/month**

**Capacity**: 10-20 repositories, 500+ queries/day, 10-50 users

See [FREE_TIER_STRATEGY.md](FREE_TIER_STRATEGY.md) for details.

## 📊 Use Cases

### For Development Teams
- **Onboarding**: New developers understand codebase faster
- **Knowledge Sharing**: Automatic documentation of architectural decisions
- **Code Reviews**: Context-aware documentation for reviewers
- **Maintenance**: Track what changed and why

### For Open Source Projects
- **Contributor Docs**: Auto-generated guides for contributors
- **API Documentation**: Always up-to-date API references
- **Architecture Docs**: Living system design documentation
- **Change Logs**: Automatic generation from commits

### For Technical Writers
- **Draft Generation**: AI-generated first drafts
- **Consistency**: Standardized documentation format
- **Coverage**: Identify undocumented areas
- **Updates**: Automatic refresh on code changes

## 🎯 Roadmap

### Phase 1: Foundation ✅ (Weeks 1-2)
- [x] Project structure and setup
- [x] GitHub webhook integration
- [x] Basic change detection
- [x] Database schema
- [x] Vector store setup

### Phase 2: Writer Agent 🚧 (Weeks 3-4)
- [ ] LLM integration (Groq)
- [ ] Context-aware generation
- [ ] Notion API integration
- [ ] Documentation versioning
- [ ] Code-doc mapping

### Phase 3: Query Interface (Weeks 5-6)
- [ ] RAG implementation
- [ ] Hybrid search
- [ ] React frontend
- [ ] Streaming responses
- [ ] Conversation context

### Phase 4: Advanced Features (Weeks 7-8)
- [ ] Dependency analysis
- [ ] Staleness detection
- [ ] Quality scoring
- [ ] Coverage metrics
- [ ] Access control

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` for backend, `npm test` for frontend)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangChain](https://python.langchain.com/) - LLM application framework
- [Groq](https://groq.com/) - Fast LLM inference
- [Qdrant](https://qdrant.tech/) - Vector similarity search
- [Supabase](https://supabase.com/) - Open source Firebase alternative
- [Notion](https://www.notion.so/) - Documentation platform

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/documind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/documind/discussions)
- **Email**: your.email@example.com

## 🌟 Star History

If you find DocuMind useful, please consider giving it a star! ⭐

---

**Built with ❤️ by developers, for developers**