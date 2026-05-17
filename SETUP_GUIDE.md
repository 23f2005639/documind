# DocuMind Setup Guide

## Quick Start

This guide will help you set up DocuMind locally for development.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose (recommended)
- Git

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd documind

# Copy environment file
cp .env.example .env
```

## Step 2: Configure Environment Variables

Edit `.env` and add your API keys:

### Required Services

1. **Groq API** (Free - 14,400 requests/day)
   - Sign up at https://console.groq.com
   - Create API key
   - Add to `.env`: `GROQ_API_KEY=your-key-here`

2. **Qdrant Cloud** (Free - 1GB storage)
   - Sign up at https://cloud.qdrant.io
   - Create cluster
   - Add to `.env`:
     ```
     QDRANT_URL=https://your-cluster.qdrant.io
     QDRANT_API_KEY=your-api-key
     ```

3. **Supabase** (Free - 500MB database)
   - Sign up at https://supabase.com
   - Create project
   - Get connection details from Settings > Database
   - Add to `.env`:
     ```
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your-anon-key
     DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
     ```

4. **Notion** (Free)
   - Go to https://www.notion.so/my-integrations
   - Create new integration
   - Get integration token
   - Create a database in Notion
   - Share database with your integration
   - Add to `.env`:
     ```
     NOTION_API_KEY=your-integration-token
     NOTION_DATABASE_ID=your-database-id
     ```

5. **GitHub** (Free)
   - Create GitHub App at https://github.com/settings/apps
   - Generate private key
   - Add to `.env`:
     ```
     GITHUB_APP_ID=your-app-id
     GITHUB_PRIVATE_KEY=your-private-key
     GITHUB_WEBHOOK_SECRET=your-webhook-secret
     ```

## Step 3: Option A - Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access services:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

## Step 3: Option B - Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations (if using local PostgreSQL)
# Make sure PostgreSQL with pgvector is installed
psql -U postgres -d documind -f app/db/schema.sql

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Step 4: Initialize Database

If using Supabase:

```bash
# Connect to Supabase and run schema
psql $DATABASE_URL -f backend/app/db/schema.sql
```

If using local PostgreSQL:

```bash
# Create database
createdb documind

# Run schema
psql -d documind -f backend/app/db/schema.sql
```

## Step 5: Verify Setup

1. **Check Backend Health**
   ```bash
   curl http://localhost:8000/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "app": "DocuMind",
     "environment": "development",
     "version": "0.1.0"
   }
   ```

2. **Check API Documentation**
   - Open http://localhost:8000/docs
   - You should see the FastAPI Swagger UI

3. **Check Frontend**
   - Open http://localhost:3000
   - You should see the DocuMind interface

## Step 6: Test with a Repository

1. **Register a Repository**
   ```bash
   curl -X POST http://localhost:8000/api/repositories \
     -H "Content-Type: application/json" \
     -d '{
       "github_url": "https://github.com/username/repo",
       "name": "Test Repo"
     }'
   ```

2. **Set up GitHub Webhook**
   - Go to your repository settings on GitHub
   - Navigate to Webhooks
   - Add webhook:
     - Payload URL: `https://your-domain.com/webhooks/github`
     - Content type: `application/json`
     - Secret: (use value from `.env`)
     - Events: Push events

## Troubleshooting

### Backend won't start

**Error: "Import errors"**
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**Error: "Database connection failed"**
- Check DATABASE_URL in `.env`
- Verify PostgreSQL is running
- Check credentials

### Frontend won't start

**Error: "Module not found"**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

**Error: "Port already in use"**
- Change port in `package.json` or kill process using port 3000

### Docker issues

**Error: "Cannot connect to Docker daemon"**
- Make sure Docker Desktop is running
- Check Docker service status

**Error: "Port already allocated"**
- Stop conflicting services or change ports in `docker-compose.yml`

### Database issues

**Error: "pgvector extension not found"**
- Use `ankane/pgvector` Docker image
- Or install pgvector manually: https://github.com/pgvector/pgvector

**Error: "Permission denied"**
- Check database user permissions
- Verify connection string format

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
cd backend
black app/
ruff check app/

# Frontend
cd frontend
npm run lint
```

### Database Migrations

```bash
# Create new migration
# (Add your migration tool commands here)

# Apply migrations
psql $DATABASE_URL -f backend/app/db/migrations/001_new_migration.sql
```

## Next Steps

1. **Read the Documentation**
   - [Architecture Guide](ARCHITECTURE.md)
   - [Implementation Guide](IMPLEMENTATION_GUIDE.md)
   - [MVP Roadmap](MVP_ROADMAP.md)

2. **Start Development**
   - Follow the [MVP Roadmap](MVP_ROADMAP.md) for implementation order
   - Check the [TODO list](#) for current tasks

3. **Join the Community**
   - Report issues on GitHub
   - Contribute improvements
   - Share feedback

## Useful Commands

```bash
# Docker
docker-compose up -d          # Start services
docker-compose down           # Stop services
docker-compose logs -f        # View logs
docker-compose restart        # Restart services

# Backend
uvicorn app.main:app --reload # Start with auto-reload
pytest                        # Run tests
black app/                    # Format code
ruff check app/               # Lint code

# Frontend
npm run dev                   # Start dev server
npm run build                 # Build for production
npm test                      # Run tests
npm run lint                  # Lint code

# Database
psql $DATABASE_URL            # Connect to database
psql $DATABASE_URL -f file.sql # Run SQL file
```

## Support

- **Documentation**: Check the docs/ directory
- **Issues**: https://github.com/yourusername/documind/issues
- **Discussions**: https://github.com/yourusername/documind/discussions

## License

MIT License - see [LICENSE](LICENSE) file for details