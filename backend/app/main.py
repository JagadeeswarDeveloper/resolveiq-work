"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import api_router

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler."""
    # Startup
    print(f"🚀 ResolveIQ started in {settings.environment} mode")
    yield
    # Shutdown
    print("🛑 ResolveIQ shutting down")


# Create FastAPI app
app = FastAPI(
    title="ResolveIQ API",
    description="Multi-agent Customer Complaint Intelligence & Resolution Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "ResolveIQ",
        "environment": settings.environment,
    }


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="ResolveIQ API",
        version="0.1.0",
        description="Multi-agent Customer Complaint Intelligence & Resolution Platform",
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
