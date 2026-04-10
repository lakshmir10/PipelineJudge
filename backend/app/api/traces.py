"""Trace API — upload pipeline traces and retrieve them."""

import hashlib
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.models.db import Pipeline, PipelineRun, AgentExecution, HandoffEvent, gen_uuid
from app.models.schemas import TraceUpload

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("/upload")
def upload_trace(trace: TraceUpload, db: Session = Depends(get_db)):
    """Ingest a pipeline trace. Creates pipeline if new, stores run and all agent executions."""

    # Find or create pipeline
    pipeline = db.query(Pipeline).filter(
        Pipeline.name == trace.pipeline_name,
        Pipeline.version == trace.pipeline_version,
    ).first()

    if not pipeline:
        pipeline = Pipeline(
            id=gen_uuid(),
            name=trace.pipeline_name,
            version=trace.pipeline_version,
            topology={"agents": [a.name for a in trace.agents]},
        )
        db.add(pipeline)
        db.flush()

    # Create pipeline run
    input_hash = hashlib.sha256(
        json.dumps([a.input_payload for a in trace.agents], sort_keys=True).encode()
    ).hexdigest()[:16]

    run = PipelineRun(
        id=gen_uuid(),
        pipeline_id=pipeline.id,
        triggered_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        status="completed",
        input_hash=input_hash,
        run_metadata=trace.run_metadata,
    )
    db.add(run)
    db.flush()

    # Create agent executions
    exec_map = {}  # agent_name -> execution_id
    for i, agent in enumerate(trace.agents):
        exec_id = gen_uuid()
        parent_id = exec_map.get(agent.parent) if agent.parent else None

        execution = AgentExecution(
            id=exec_id,
            run_id=run.id,
            agent_name=agent.name,
            agent_type=agent.type,
            input_payload=agent.input_payload,
            output_payload=agent.output_payload,
            model_id=agent.model_id,
            prompt_template_hash=agent.prompt_template_hash,
            token_count_input=agent.token_count_input,
            token_count_output=agent.token_count_output,
            latency_ms=agent.latency_ms,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            parent_execution_id=parent_id,
            execution_order=agent.execution_order or i,
            metadata_=agent.metadata,
        )
        db.add(execution)
        exec_map[agent.name] = exec_id

    db.flush()

    # Create handoff events
    for handoff in trace.handoffs:
        source_id = exec_map.get(handoff.from_agent)
        target_id = exec_map.get(handoff.to_agent)
        if not source_id or not target_id:
            continue

        payload_hash = hashlib.sha256(
            json.dumps(handoff.payload, sort_keys=True).encode()
        ).hexdigest()[:16]

        event = HandoffEvent(
            id=gen_uuid(),
            run_id=run.id,
            source_execution_id=source_id,
            target_execution_id=target_id,
            payload=handoff.payload,
            payload_hash=payload_hash,
        )
        db.add(event)

    db.commit()

    return {
        "status": "ok",
        "run_id": run.id,
        "pipeline_id": pipeline.id,
        "agents_stored": len(trace.agents),
        "handoffs_stored": len(trace.handoffs),
    }


@router.get("/runs")
def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    """List recent pipeline runs."""
    runs = db.query(PipelineRun).order_by(
        PipelineRun.triggered_at.desc()
    ).limit(limit).all()

    results = []
    for run in runs:
        pipeline = db.query(Pipeline).filter(Pipeline.id == run.pipeline_id).first()
        agent_count = db.query(AgentExecution).filter(AgentExecution.run_id == run.id).count()
        results.append({
            "run_id": run.id,
            "pipeline_name": pipeline.name if pipeline else "unknown",
            "pipeline_version": pipeline.version if pipeline else "?",
            "triggered_at": run.triggered_at.isoformat() if run.triggered_at else None,
            "status": run.status,
            "agent_count": agent_count,
        })

    return results
@router.delete("/runs/{run_id}")
def delete_run(run_id: str, db: Session = Depends(get_db)):
    """Delete a pipeline run and all associated data."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Delete handoffs, executions, eval data
    db.query(HandoffEvent).filter(HandoffEvent.run_id == run_id).delete()
    db.query(AgentExecution).filter(AgentExecution.run_id == run_id).delete()
    db.query(PipelineRun).filter(PipelineRun.id == run_id).delete()
    db.commit()

    # Also remove from eval_results if saved
    import os, json
    results_dir = os.path.join(os.path.dirname(__file__), "..", "..", "eval_results")
    query_id = run_id[:8]
    result_file = os.path.join(results_dir, f"{query_id}.json")
    if os.path.exists(result_file):
        os.remove(result_file)
    index_path = os.path.join(results_dir, "index.json")
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
        index = [e for e in index if e.get("query_id") != query_id]
        with open(index_path, "w") as f:
            json.dump(index, f)

    return {"status": "deleted", "run_id": run_id}

@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get full trace for a pipeline run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    pipeline = db.query(Pipeline).filter(Pipeline.id == run.pipeline_id).first()
    executions = db.query(AgentExecution).filter(
        AgentExecution.run_id == run_id
    ).order_by(AgentExecution.execution_order).all()
    handoffs = db.query(HandoffEvent).filter(HandoffEvent.run_id == run_id).all()

    exec_id_to_name = {e.id: e.agent_name for e in executions}

    return {
        "run_id": run.id,
        "pipeline": {
            "name": pipeline.name if pipeline else "unknown",
            "version": pipeline.version if pipeline else "?",
        },
        "triggered_at": run.triggered_at.isoformat() if run.triggered_at else None,
        "status": run.status,
        "agents": [
            {
                "execution_id": e.id,
                "name": e.agent_name,
                "type": e.agent_type,
                "model_id": e.model_id,
                "prompt_template_hash": e.prompt_template_hash,
                "latency_ms": e.latency_ms,
                "token_count_input": e.token_count_input,
                "token_count_output": e.token_count_output,
                "input_payload": e.input_payload,
                "output_payload": e.output_payload,
            }
            for e in executions
        ],
        "handoffs": [
            {
                "handoff_id": h.id,
                "from": exec_id_to_name.get(h.source_execution_id, "?"),
                "to": exec_id_to_name.get(h.target_execution_id, "?"),
                "payload": h.payload,
            }
            for h in handoffs
        ],
    }
