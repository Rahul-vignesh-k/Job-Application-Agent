"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.config import get_settings
from backend.db.database import init_db
from backend.api.jobs import router as jobs_router
from backend.api.resumes import router as resumes_router
from backend.api.answers import router as answers_router
from backend.api.history import router as history_router
from backend.api.settings_api import router as settings_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI Job Application Agent",
    version="1.0.0",
    description="Automated job discovery, matching, and application system powered by Gemini + RAG.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix="/api")
app.include_router(resumes_router, prefix="/api")
app.include_router(answers_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve React build in production
if os.path.exists("./frontend/dist"):
    app.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="static")
