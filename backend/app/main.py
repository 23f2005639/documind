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
