"""FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("starting_application", app_name=settings.app_name, env=settings.app_env)

    from app.services.vector_store import vector_store
    from app.services.embedding import embedding_service

    embedding_service._load_model()
    await vector_store.initialize_collection()

    yield

    # Shutdown
    logger.info("shutting_down_application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Multi-agent documentation system with natural language queries",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        "unhandled_exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DocuMind API",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
from app.api import query, streaming

app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(streaming.router, prefix="/api/query", tags=["streaming"])


@app.post("/api/index", tags=["index"])
async def index_project(path: str = "/home/shreyas/Desktop/bob_proj/documind"):
    """Index project files into the vector store"""
    import asyncio
    from pathlib import Path
    from app.services.vector_store import vector_store
    from app.services.embedding import embedding_service

    SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md"}
    SKIP_DIRS = {
        "node_modules", ".venv", "__pycache__", ".git",
        "qdrant_storage", ".mypy_cache", "dist", "build",
        ".next", "coverage", ".pytest_cache",
    }

    base_path = Path(path)
    documents = []

    for file_path in base_path.rglob("*"):
        if any(skip in file_path.parts for skip in SKIP_DIRS):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
            rel_path = str(file_path.relative_to(base_path))
            chunk_size = 1500
            overlap = 200
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if not chunk.strip():
                    continue
                documents.append({
                    "doc_id": f"{rel_path}:chunk{i // (chunk_size - overlap)}",
                    "content": chunk,
                    "metadata": {
                        "file_name": file_path.name,
                        "file_path": rel_path,
                        "chunk_index": i // (chunk_size - overlap),
                        "type": "code" if file_path.suffix != ".md" else "documentation",
                        "language": file_path.suffix.lstrip("."),
                    }
                })
        except Exception:
            continue

    logger.info("indexing_project", chunks=len(documents))

    batch_size = 32
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        await vector_store.index_documents_batch(batch)

    return {"indexed": len(documents), "path": path}

# TODO: Add remaining routers when implemented
# from app.api import webhooks, repositories, documentation
# app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
# app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
# app.include_router(documentation.router, prefix="/api/documentation", tags=["documentation"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

# Made with Bob
