"""Configuration and database session management.

Supports two database backends:
  - SQLite (default, local dev): DATABASE_URL=sqlite:///./pipelinejudge.db
  - PostgreSQL (production):     DATABASE_URL=postgresql://user:pass@host:5432/pipelinejudge

Set DATABASE_URL env var to switch. PostgreSQL gets connection pooling automatically.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pipelinejudge.db")

# PostgreSQL connection pooling for production; SQLite needs check_same_thread=False
_is_sqlite = "sqlite" in DATABASE_URL

engine_kwargs = {
    "echo": os.getenv("PIPELINEJUDGE_DB_ECHO", "false").lower() == "true",
}

if _is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL production settings
    engine_kwargs["pool_size"] = int(os.getenv("PIPELINEJUDGE_DB_POOL_SIZE", "10"))
    engine_kwargs["max_overflow"] = int(os.getenv("PIPELINEJUDGE_DB_MAX_OVERFLOW", "20"))
    engine_kwargs["pool_pre_ping"] = True  # verify connections are alive before using
    engine_kwargs["pool_recycle"] = 300  # recycle connections every 5 minutes

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables. For production, use Alembic migrations instead."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injection for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# LLM config — which models to use for LLM judges
LLM_MODEL = os.getenv("PIPELINEJUDGE_LLM_MODEL", "claude-sonnet-4-20250514")
LLM_MODEL_CHEAP = os.getenv("PIPELINEJUDGE_LLM_MODEL_CHEAP", "claude-haiku-4-5-20251001")
LLM_TIMEOUT = int(os.getenv("PIPELINEJUDGE_LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("PIPELINEJUDGE_LLM_MAX_RETRIES", "3"))
EVAL_CONCURRENCY = int(os.getenv("PIPELINEJUDGE_EVAL_CONCURRENCY", "5"))
