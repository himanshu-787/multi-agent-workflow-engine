from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as workflows_router, memory_router, tools_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Stateful, cyclic multi-agent autonomous workflow orchestrator using LangGraph, FastAPI, and ChromaDB.",
    version="1.0.0",
)

# CORS middleware for open integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(workflows_router)
app.include_router(memory_router)
app.include_router(tools_router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "model_name": settings.model_name,
    }
