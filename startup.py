"""Startup script — initializes database and seeds demo data if empty.

Run this before starting the server, or as part of the deploy command.
Idempotent: skips seeding if data already exists.
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.config import init_db, SessionLocal
from app.models.db import PipelineRun


def seed_demo_data():
    """Load demo pipeline traces and eval results if the database is empty."""
    db = SessionLocal()
    try:
        existing = db.query(PipelineRun).first()
        if existing:
            print("[startup] Database already has data, skipping seed.")
            return

        print("[startup] Empty database. Seeding demo data...")

        # Import and run the demo pipeline
        demo_dir = os.path.join(os.path.dirname(__file__), "demo")
        sys.path.insert(0, os.path.dirname(__file__))

        from demo.rag_pipeline import run_pipeline
        from demo.test_queries.queries import get_test_queries

        # Use FastAPI TestClient to upload traces via the API
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        queries = get_test_queries()
        trace_results = []

        for q in queries:
            trace = run_pipeline(q["query"])
            r = client.post("/traces/upload", json=trace)
            if r.status_code == 200:
                run_id = r.json()["run_id"]
                trace_results.append({
                    "query_id": q["id"],
                    "run_id": run_id,
                    "query": q["query"],
                    "failure_mode": q["failure_mode"],
                })
                print(f"  [seed] {q['id']:10s} -> {run_id[:12]}")

        # Run evaluations
        import asyncio
        from app.engine.eval_engine import run_eval

        results_dir = os.path.join(os.path.dirname(__file__), "backend", "eval_results")
        os.makedirs(results_dir, exist_ok=True)
        index = []

        for tr in trace_results:
            try:
                result = asyncio.run(run_eval(tr["run_id"], db))
                overall = result["system"]["overall"]
                capped = result["system"]["compliance_capped"]

                # Save result JSON
                filepath = os.path.join(results_dir, f"{tr['query_id']}.json")
                with open(filepath, "w") as f:
                    json.dump(result, f, indent=2)

                index.append({
                    "query_id": tr["query_id"],
                    "run_id": tr["run_id"],
                    "query": tr["query"],
                    "failure_mode": tr["failure_mode"],
                    "overall": overall,
                    "compliance_capped": capped,
                })
                print(f"  [eval] {tr['query_id']:10s} -> overall={overall}")
            except Exception as e:
                print(f"  [eval] {tr['query_id']:10s} -> ERROR: {e}")

        # Save index
        with open(os.path.join(results_dir, "index.json"), "w") as f:
            json.dump(index, f, indent=2)

        # Regenerate the dashboard HTML with fresh data
        _rebuild_dashboard(index, results_dir)

        print(f"[startup] Seeded {len(index)} eval results.")

    finally:
        db.close()


def _rebuild_dashboard(index, results_dir):
    """Rebuild the static dashboard HTML with the latest eval data."""
    data = {}
    for entry in index:
        filepath = os.path.join(results_dir, f"{entry['query_id']}.json")
        if os.path.exists(filepath):
            with open(filepath) as f:
                data[entry["query_id"]] = json.load(f)

    data_json = json.dumps({"index": index, "data": data}, separators=(",", ":"))

    static_dir = os.path.join(os.path.dirname(__file__), "backend", "static")
    html_path = os.path.join(static_dir, "index.html")

    if os.path.exists(html_path):
        with open(html_path) as f:
            html = f.read()

        # Replace the ALL_RESULTS data blob using string find/replace (not regex — JSON contains backslashes)
        marker_start = "var ALL_RESULTS="
        marker_end = "};"
        start_idx = html.find(marker_start)
        if start_idx >= 0:
            # Find the matching end — the data ends with }; followed by </script> or newline
            search_from = start_idx + len(marker_start)
            # Find the last }; before the next function/var declaration
            end_idx = html.find(";\nvar ", search_from)
            if end_idx < 0:
                end_idx = html.find(";\n\nvar ", search_from)
            if end_idx < 0:
                end_idx = html.find(";</script>", search_from)
            if end_idx >= 0:
                new_html = html[:start_idx] + f"var ALL_RESULTS={data_json};" + html[end_idx+1:]
                with open(html_path, "w") as f:
                    f.write(new_html)
                print(f"[startup] Dashboard HTML updated with fresh data.")
            else:
                print("[startup] Warning: could not find end marker in dashboard HTML.")
        else:
            print("[startup] Warning: could not find ALL_RESULTS in dashboard HTML.")


if __name__ == "__main__":
    print("[startup] Initializing database...")
    init_db()
    seed_demo_data()
    print("[startup] Done.")
