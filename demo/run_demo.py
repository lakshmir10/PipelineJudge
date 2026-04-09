"""Run all test queries through the pipeline and upload traces to PipelineJudge."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from demo.rag_pipeline import run_pipeline
from demo.test_queries.queries import get_test_queries

# Use FastAPI test client for self-contained demo
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.main import app
from app.config import init_db

# Ensure tables exist
init_db()


def run_demo():
    client = TestClient(app)
    queries = get_test_queries()
    run_ids = []

    print(f"Running {len(queries)} test queries through Nexus Cloud RAG Pipeline...\n")

    for q in queries:
        # Execute pipeline
        trace = run_pipeline(q["query"])

        # Upload to PipelineJudge
        response = client.post("/traces/upload", json=trace)
        result = response.json()
        run_id = result["run_id"]
        run_ids.append({"query_id": q["id"], "run_id": run_id, "failure_mode": q["failure_mode"]})

        status = "CLEAN" if not q["failure_mode"] else f"FAIL-{q['failure_mode'].upper()}"
        print(f"  [{status:16s}] {q['id']:10s} → run_id={run_id[:12]}.. | {q['query'][:50]}")

    print(f"\n{len(run_ids)} traces uploaded to PipelineJudge.")
    print("\nRun IDs for eval:")
    for r in run_ids:
        print(f"  {r['query_id']:10s} {r['run_id']}  ({r['failure_mode'] or 'clean'})")

    return run_ids


if __name__ == "__main__":
    results = run_demo()
