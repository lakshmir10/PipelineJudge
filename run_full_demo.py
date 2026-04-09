"""PipelineJudge Full Demo — runs pipeline, evals, and serves dashboard.

Usage: python run_full_demo.py
Then open http://localhost:8000 in your browser.
"""

import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.environ.setdefault("PIPELINEJUDGE_MOCK_LLM", "true")

from app.config import init_db, SessionLocal
from app.models.db import Base, PipelineRun, SystemScore
from app.engine.eval_engine import run_eval


def setup_db():
    """Fresh database for the demo."""
    db_path = os.path.join(os.path.dirname(__file__), "backend", "pipelinejudge.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()


def upload_traces():
    """Run all test queries and upload traces."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    sys.path.insert(0, os.path.dirname(__file__))
    from demo.rag_pipeline import run_pipeline
    from demo.test_queries.queries import get_test_queries

    queries = get_test_queries()
    results = []

    print(f"\n  Running {len(queries)} test queries...\n")
    for q in queries:
        trace = run_pipeline(q["query"])
        r = client.post("/traces/upload", json=trace)
        run_id = r.json()["run_id"]
        status = "CLEAN" if not q["failure_mode"] else f"FAIL-{q['failure_mode'].upper()}"
        print(f"    [{status:18s}] {q['id']:10s} → {run_id[:12]}.. | {q['query'][:50]}")
        results.append({
            "query_id": q["id"],
            "run_id": run_id,
            "query": q["query"],
            "failure_mode": q["failure_mode"],
        })

    return results


def run_evals(trace_results):
    """Run eval on each trace."""
    db = SessionLocal()
    eval_results = []

    print(f"\n  Running evaluations on {len(trace_results)} traces...\n")
    for tr in trace_results:
        try:
            result = asyncio.run(run_eval(tr["run_id"], db))
            overall = result["system"]["overall"]
            capped = result["system"]["compliance_capped"]
            cap_str = " [CAPPED]" if capped else ""
            print(f"    {tr['query_id']:10s} → overall={overall}{cap_str}")
            eval_results.append({
                **tr,
                "eval_data": result,
            })
        except Exception as e:
            print(f"    {tr['query_id']:10s} → ERROR: {e}")
            eval_results.append({**tr, "eval_data": None})

    db.close()
    return eval_results


def save_results(eval_results):
    """Save all eval results as JSON for the frontend to consume."""
    output_dir = os.path.join(os.path.dirname(__file__), "backend")

    # Save individual results
    results_dir = os.path.join(output_dir, "eval_results")
    os.makedirs(results_dir, exist_ok=True)

    index = []
    for er in eval_results:
        if er["eval_data"]:
            filepath = os.path.join(results_dir, f"{er['query_id']}.json")
            with open(filepath, "w") as f:
                json.dump(er["eval_data"], f, indent=2)
            index.append({
                "query_id": er["query_id"],
                "run_id": er["run_id"],
                "query": er["query"],
                "failure_mode": er["failure_mode"],
                "overall": er["eval_data"]["system"]["overall"],
                "compliance_capped": er["eval_data"]["system"]["compliance_capped"],
            })

    # Save index
    with open(os.path.join(results_dir, "index.json"), "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n  Saved {len(index)} eval results to {results_dir}/")
    return results_dir


def main():
    print("=" * 60)
    print("  PipelineJudge — Full Demo")
    print("=" * 60)

    print("\n[1/3] Setting up database...")
    setup_db()

    print("\n[2/3] Running pipeline & uploading traces...")
    trace_results = upload_traces()

    print("\n[3/3] Running evaluations...")
    eval_results = run_evals(trace_results)

    results_dir = save_results(eval_results)

    # Print summary
    print("\n" + "=" * 60)
    print("  DEMO SUMMARY")
    print("=" * 60)
    for er in eval_results:
        if er["eval_data"]:
            s = er["eval_data"]["system"]
            pii_count = len(er["eval_data"]["compliance_detail"]["pii_findings"])
            cap = " ⚠ CAPPED" if s["compliance_capped"] else ""
            print(f"  {er['query_id']:10s} | overall={s['overall']:5.1f} | product={s['product']:5.1f} | pipeline={s['pipeline']:5.1f} | compliance={s['compliance']:5.1f} | PII={pii_count}{cap}")

    print(f"\n  Results saved to: {results_dir}/")
    print(f"  To serve the dashboard, run:")
    print(f"    cd {os.path.dirname(__file__)}/backend && uvicorn app.main:app --reload")
    print(f"  Then open:")
    print(f"    http://localhost:8000/evals/dashboard     — all results (dashboard data)")
    print(f"    http://localhost:8000/evals/results       — result index")
    print(f"    http://localhost:8000/evals/results/clean-01  — single result")
    print()


if __name__ == "__main__":
    main()
