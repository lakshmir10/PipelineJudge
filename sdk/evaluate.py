"""PipelineJudge SDK — evaluate multi-agent pipelines in 3 lines.

Usage:
    from pipelinejudge import evaluate

    result = evaluate(
        query="What is the refund policy?",
        steps=[
            {"name": "classifier", "type": "analysis", "output": classifier_result},
            {"name": "retriever", "type": "retrieval", "output": retriever_result},
            {"name": "generator", "type": "synthesis", "output": generator_result},
        ]
    )

    print(result["system"]["overall"])        # 73.2
    print(result["system"]["compliance"])      # 44.1
    print(result["system"]["compliance_capped"])  # True

    # Which agent is the bottleneck?
    for agent in result["agents"]:
        print(f'{agent["name"]}: attribution={agent["attribution"]:+.3f}')

The SDK runs the full evaluation engine locally. No server, no API key,
no database required. Pass in what your pipeline did, get scores back.

For the hosted version (dashboard, history, trend tracking), see the
API integration docs at https://github.com/YOUR_USERNAME/pipelinejudge
"""

import os
import sys
import json
import asyncio
import hashlib
import tempfile
from datetime import datetime
from typing import Any, Optional


def evaluate(
    query: str,
    steps: list[dict],
    handoffs: Optional[list[dict]] = None,
    pipeline_name: str = "unnamed",
    pipeline_version: str = "1.0",
    mock_llm: bool = True,
) -> dict:
    """Evaluate a multi-agent pipeline run.

    Args:
        query: The user's input query that triggered the pipeline.
        steps: List of agent execution dicts, each containing:
            - name (str, required): Agent name (e.g. "retriever", "classifier")
            - type (str, optional): Agent archetype. One of: analysis, retrieval,
              synthesis, adversarial, custom. If omitted, auto-detected from name.
            - output (dict|str, required): What the agent produced.
            - input (dict|str, optional): What the agent received. Auto-inferred
              from previous step's output if omitted.
            - model_id (str, optional): Model used (e.g. "claude-sonnet-4-20250514")
            - latency_ms (int, optional): Execution time in milliseconds.
        handoffs: Optional list of explicit handoff dicts:
            - from_agent (str): Source agent name
            - to_agent (str): Target agent name
            - payload (dict): Data transferred
            If omitted, handoffs are inferred from step order.
        pipeline_name: Name for this pipeline (used in results).
        pipeline_version: Version string.
        mock_llm: If True (default), uses content-aware mock judges.
            Set to False and provide ANTHROPIC_API_KEY or OPENAI_API_KEY
            env var to use real LLM judges.

    Returns:
        Full evaluation result dict with:
        - system: {overall, product, pipeline, compliance, compliance_capped}
        - layers: {product: {...}, pipeline: {...}, compliance: {...}}
        - agents: [{name, type, paqs, attribution, input_quality, output_quality, ...}]
        - handoffs: [{from, to, his, subs}]
        - compliance_detail: {pii_findings, audit_checks, rule_results}
        - eval_meta: {suite, duration_sec, tasks, llm_calls, cost_usd}
    """
    # Set mock mode
    os.environ["PIPELINEJUDGE_MOCK_LLM"] = "true" if mock_llm else "false"

    # Ensure backend is importable
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
    if os.path.exists(backend_dir) and backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Also handle the case where SDK is used standalone
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_alt = os.path.join(parent, "backend")
    if os.path.exists(backend_alt) and backend_alt not in sys.path:
        sys.path.insert(0, backend_alt)

    from app.config import init_db, SessionLocal, engine
    from app.models.db import Base, PipelineRun, Pipeline, AgentExecution, HandoffEvent, gen_uuid
    from app.engine.eval_engine import run_eval

    # Use a temporary database
    tmp_db = os.path.join(tempfile.gettempdir(), f"pipelinejudge_{os.getpid()}.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"

    # Reinitialize engine with temp db (needed because config module caches)
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker
    temp_engine = ce(f"sqlite:///{tmp_db}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=temp_engine)
    TempSession = sessionmaker(bind=temp_engine)
    db = TempSession()

    try:
        # Normalize steps
        normalized = _normalize_steps(steps, query)

        # Build trace
        trace = _build_trace(query, normalized, handoffs, pipeline_name, pipeline_version)

        # Upload trace to temp DB
        pipeline_obj = Pipeline(
            id=gen_uuid(), name=pipeline_name, version=pipeline_version,
            topology={"agents": [s["name"] for s in normalized]},
        )
        db.add(pipeline_obj)
        db.flush()

        run = PipelineRun(
            id=gen_uuid(), pipeline_id=pipeline_obj.id,
            triggered_at=datetime.utcnow(), completed_at=datetime.utcnow(),
            status="completed",
            run_metadata={"query": query},
        )
        db.add(run)
        db.flush()

        exec_map = {}
        for i, step in enumerate(normalized):
            exec_id = gen_uuid()
            execution = AgentExecution(
                id=exec_id, run_id=run.id,
                agent_name=step["name"], agent_type=step["type"],
                input_payload=step["input"], output_payload=step["output"],
                model_id=step.get("model_id", "sdk-local"),
                prompt_template_hash=step.get("prompt_hash"),
                latency_ms=step.get("latency_ms", 0),
                started_at=datetime.utcnow(), completed_at=datetime.utcnow(),
                execution_order=i,
            )
            db.add(execution)
            exec_map[step["name"]] = exec_id

        db.flush()

        # Create handoffs
        actual_handoffs = handoffs or _infer_handoffs(normalized)
        for h in actual_handoffs:
            src = exec_map.get(h["from_agent"])
            tgt = exec_map.get(h["to_agent"])
            if src and tgt:
                event = HandoffEvent(
                    id=gen_uuid(), run_id=run.id,
                    source_execution_id=src, target_execution_id=tgt,
                    payload=h.get("payload", {}),
                )
                db.add(event)

        db.commit()

        # Run evaluation
        result = asyncio.run(run_eval(run.id, db))
        return result

    finally:
        db.close()
        temp_engine.dispose()
        # Clean up temp db
        try:
            os.unlink(tmp_db)
        except OSError:
            pass


def _detect_type(name: str, output: Any = None) -> str:
    """Auto-detect agent archetype from name and output content."""
    name_lower = name.lower()
    output_str = str(output).lower()[:500] if output else ""

    if any(kw in name_lower for kw in ["analy", "classif", "parse", "intent", "query"]):
        return "analysis"
    if any(kw in name_lower for kw in ["retriev", "search", "fetch", "rag", "index", "vector"]):
        return "retrieval"
    if any(kw in name_lower for kw in ["synth", "generat", "write", "answer", "respond", "compose"]):
        return "synthesis"
    if any(kw in name_lower for kw in ["verif", "valid", "check", "audit", "review", "adversar"]):
        return "adversarial"

    # Output-based detection
    if "chunks" in output_str or "documents found" in output_str:
        return "retrieval"
    if "answer" in output_str and "citation" in output_str:
        return "synthesis"

    return "custom"


def _normalize_steps(steps: list[dict], query: str) -> list[dict]:
    """Normalize user-provided steps into the internal format."""
    normalized = []
    prev_output = None

    for i, step in enumerate(steps):
        name = step.get("name", f"agent_{i}")
        agent_type = step.get("type") or _detect_type(name, step.get("output"))

        # Normalize output
        output = step.get("output", {})
        if isinstance(output, str):
            output = {"text": output}

        # Normalize input — use explicit input, or previous agent's output, or the query
        input_data = step.get("input")
        if input_data is None:
            if i == 0:
                input_data = {"query": query}
            elif prev_output is not None:
                input_data = prev_output
            else:
                input_data = {"query": query}
        elif isinstance(input_data, str):
            input_data = {"text": input_data}

        normalized.append({
            "name": name,
            "type": agent_type,
            "input": input_data,
            "output": output,
            "model_id": step.get("model_id"),
            "latency_ms": step.get("latency_ms", 0),
            "prompt_hash": step.get("prompt_hash"),
        })

        prev_output = output

    return normalized


def _infer_handoffs(steps: list[dict]) -> list[dict]:
    """Infer handoffs from sequential step order."""
    handoffs = []
    for i in range(1, len(steps)):
        handoffs.append({
            "from_agent": steps[i-1]["name"],
            "to_agent": steps[i]["name"],
            "payload": steps[i-1]["output"],
        })
    return handoffs


def _build_trace(query, steps, handoffs, name, version):
    """Build a trace dict (for reference/debugging)."""
    return {
        "pipeline_name": name,
        "pipeline_version": version,
        "agents": [
            {
                "name": s["name"], "type": s["type"],
                "input_payload": s["input"], "output_payload": s["output"],
                "model_id": s.get("model_id"), "latency_ms": s.get("latency_ms", 0),
            }
            for s in steps
        ],
        "handoffs": handoffs or _infer_handoffs(steps),
        "run_metadata": {"query": query},
    }
