"""PipelineJudge API — main entry point."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import init_db
from app.api.traces import router as traces_router
from app.api.evals import router as evals_router

app = FastAPI(
    title="PipelineJudge",
    description="Evaluation framework for production AI systems — product outcomes, pipeline health, compliance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traces_router)
app.include_router(evals_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "pipelinejudge", "version": "0.1.0"}


STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


@app.get("/")
def serve_dashboard():
    """Serve the PipelineJudge dashboard at the root URL."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Dashboard not found. Run 'python run_full_demo.py' first."}
