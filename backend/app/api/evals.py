"""Eval API — trigger evaluations, retrieve results, export reports."""

import os
import io
import json
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_db
from app.engine.eval_engine import run_eval
from app.engine.llm_judge import JudgeConfig, set_judge_config

router = APIRouter(prefix="/evals", tags=["evals"])

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "eval_results")


# ─── Request Models ──────────────────────────────────────────────────────────

class EvalRunRequest(BaseModel):
    run_id: str
    judge_model: Optional[str] = None  # e.g. "claude-haiku-4-5-20251001"
    model_overrides: Optional[dict] = None  # {"task_completion": "claude-sonnet-4-20250514"}
    use_mock: Optional[bool] = None  # Force mock mode (for demo)
    api_keys: Optional[dict] = None  # BYOK: {"anthropic": "sk-ant-..."}


@router.post("/run")
async def trigger_eval(request: EvalRunRequest, db: Session = Depends(get_db)):
    """Trigger evaluation with optional model selection.

    Examples:
        # Default (mock judges):
        POST /evals/run {"run_id": "abc-123"}

        # Real judges with Haiku (cheap, fast):
        POST /evals/run {"run_id": "abc-123", "judge_model": "claude-haiku-4-5-20251001"}

        # Real judges with per-dimension overrides:
        POST /evals/run {
            "run_id": "abc-123",
            "judge_model": "claude-haiku-4-5-20251001",
            "model_overrides": {"task_completion": "claude-sonnet-4-20250514"}
        }

        # BYOK (bring your own key):
        POST /evals/run {
            "run_id": "abc-123",
            "api_keys": {"anthropic": "sk-ant-..."}
        }
    """
    # Configure judges for this eval run
    if request.judge_model or request.model_overrides or request.api_keys or request.use_mock is not None:
        config = JudgeConfig(
            default_model=request.judge_model,
            overrides=request.model_overrides or {},
            api_keys=request.api_keys or {},
            use_mock=request.use_mock,
        )
        set_judge_config(config)

    try:
        result = await run_eval(request.run_id, db)

        # Add judge config info to result metadata
        result.setdefault("eval_meta", {})
        result["eval_meta"]["judge_model"] = request.judge_model or os.getenv("PIPELINEJUDGE_JUDGE_MODEL", "mock")
        result["eval_meta"]["model_overrides"] = request.model_overrides or {}
        result["eval_meta"]["use_mock"] = request.use_mock if request.use_mock is not None else "auto"

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval failed: {str(e)}")


# ─── PDF Export ──────────────────────────────────────────────────────────────

@router.get("/export/{query_id}")
def export_pdf(query_id: str):
    """Export eval result as a one-page PDF report.

    Returns a downloadable PDF with:
    - System score + layer breakdown
    - Per-dimension scores
    - Chain attribution summary
    - Compliance findings
    - Top recommendation
    """
    filepath = os.path.join(RESULTS_DIR, f"{query_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No eval result for {query_id}")

    with open(filepath) as f:
        data = json.load(f)

    pdf_bytes = _generate_pdf_report(data, query_id)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=pipelinejudge_{query_id}.pdf"},
    )


def _generate_pdf_report(data: dict, query_id: str) -> bytes:
    """Generate a PDF report from eval results.

    Uses only stdlib + basic text layout. No ReportLab dependency.
    Generates a simple but clean text-based PDF.
    """
    sys_data = data.get("system", {})
    pipeline = data.get("pipeline", {})
    agents = data.get("agents", [])
    compliance = data.get("compliance_detail", {})

    # Build PDF content as simple text-based PDF (no external deps)
    lines = []
    lines.append(f"PIPELINEJUDGE EVALUATION REPORT")
    lines.append(f"=" * 50)
    lines.append(f"Pipeline: {pipeline.get('name', 'Unknown')} v{pipeline.get('version', '?')}")
    lines.append(f"Query ID: {query_id}")
    lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # System Score
    lines.append(f"SYSTEM SCORE: {sys_data.get('overall', 0)}")
    if sys_data.get("compliance_capped"):
        lines.append(f"  !! COMPLIANCE FLOOR ACTIVE - Score capped at 50")
    lines.append("")

    # Layer Breakdown
    lines.append(f"LAYER SCORES")
    lines.append(f"-" * 40)
    lines.append(f"  Product (35% weight):    {sys_data.get('product', 0)}")
    lines.append(f"  Pipeline (40% weight):   {sys_data.get('pipeline', 0)}")
    lines.append(f"  Compliance (25% weight): {sys_data.get('compliance', 0)}")
    lines.append("")

    # Dimensions
    for layer_name in ["product", "pipeline", "compliance"]:
        layer = data.get("layers", {}).get(layer_name, {})
        dims = layer.get("dimensions", [])
        if dims:
            lines.append(f"{layer_name.upper()} DIMENSIONS")
            lines.append(f"-" * 40)
            for d in dims:
                lines.append(f"  {d['code']:6s} {d['name']:35s} {d['score']}")
                for s in d.get("subs", []):
                    lines.append(f"         {s['name']:33s} {s['score']}")
            lines.append("")

    # Chain Attribution
    if agents:
        lines.append(f"CHAIN ATTRIBUTION")
        lines.append(f"-" * 40)
        for a in agents:
            delta = (a.get("output_quality", 50) - a.get("input_quality", 50))
            sign = "+" if delta >= 0 else ""
            lines.append(f"  {a['name']:20s} PAQS={a.get('paqs',0):5.1f}  delta={sign}{delta:.0f}  attr={a.get('attribution',0):+.3f}")

        # Find bottleneck
        bottleneck = min(agents, key=lambda a: a.get("attribution", 0))
        lines.append(f"")
        lines.append(f"  Bottleneck: {bottleneck['name']} (attribution: {bottleneck.get('attribution',0):+.3f})")
        lines.append("")

    # Compliance
    pii = compliance.get("pii_findings", [])
    rules = compliance.get("rule_results", [])
    if pii or rules:
        lines.append(f"COMPLIANCE DETAIL")
        lines.append(f"-" * 40)
        if pii:
            lines.append(f"  PII Findings: {len(pii)}")
            for f in pii[:5]:
                lines.append(f"    [{f.get('type','?'):8s}] {f.get('entity','?')[:20]:20s} @ {f.get('location','?')}")
            if len(pii) > 5:
                lines.append(f"    ... and {len(pii)-5} more")
        if rules:
            triggered = [r for r in rules if r.get("triggered")]
            failed = [r for r in triggered if not r.get("satisfied")]
            lines.append(f"  Regulatory Rules: {len(triggered)} triggered, {len(failed)} failed")
            for r in failed:
                lines.append(f"    FAIL: {r['rule']}")
        lines.append("")

    # Recommendation
    lines.append(f"RECOMMENDATION")
    lines.append(f"-" * 40)
    if sys_data.get("compliance_capped"):
        lines.append(f"  URGENT: Compliance floor violated. Address PII leakage and")
        lines.append(f"  regulatory rule failures before any other quality improvements.")
    elif agents:
        bottleneck = min(agents, key=lambda a: a.get("attribution", 0))
        if bottleneck.get("attribution", 0) < -0.1:
            lines.append(f"  Focus engineering effort on the {bottleneck['name']} agent.")
            lines.append(f"  It has the most negative attribution ({bottleneck.get('attribution',0):+.3f}),")
            lines.append(f"  meaning it degrades pipeline quality more than any other step.")
        else:
            lines.append(f"  Pipeline is performing reasonably. Look for improvements in")
            lines.append(f"  the lowest-scoring product dimension for the next iteration.")

    text = "\n".join(lines)

    # Generate minimal valid PDF
    return _text_to_pdf(text)


def _text_to_pdf(text: str) -> bytes:
    """Generate a minimal PDF from plain text. No external dependencies."""
    lines = text.split("\n")
    # PDF structure
    objects = []

    # Object 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")

    # Object 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")

    # Object 4: Font
    objects.append("4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj")

    # Build content stream
    content_lines = ["BT", "/F1 9 Tf", "50 780 Td", "11 TL"]
    for line in lines:
        # Replace unicode chars that Courier can't render
        safe = line.replace("\u2014", "--").replace("\u2192", "->").replace("\u2713", "[ok]").replace("\u2717", "[X]")
        # Escape PDF special characters
        safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        # Truncate long lines
        if len(safe) > 90:
            safe = safe[:87] + "..."
        content_lines.append(f"({safe}) '")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines)

    # Object 5: Content stream
    objects.append(f"5 0 obj\n<< /Length {len(content_stream)} >>\nstream\n{content_stream}\nendstream\nendobj")

    # Object 3: Page
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>\nendobj")

    # Build PDF
    pdf = "%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj + "\n"

    xref_offset = len(pdf)
    pdf += "xref\n"
    pdf += f"0 {len(objects)+1}\n"
    pdf += "0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n"

    pdf += "trailer\n"
    pdf += f"<< /Size {len(objects)+1} /Root 1 0 R >>\n"
    pdf += "startxref\n"
    pdf += f"{xref_offset}\n"
    pdf += "%%EOF\n"

    return pdf.encode("latin-1")


# ─── Results Endpoints ───────────────────────────────────────────────────────

@router.get("/results")
def list_results():
    """List all saved eval results."""
    index_path = os.path.join(RESULTS_DIR, "index.json")
    if not os.path.exists(index_path):
        return []
    with open(index_path) as f:
        return json.load(f)


@router.get("/results/{query_id}")
def get_result(query_id: str):
    """Get saved eval result by query ID."""
    filepath = os.path.join(RESULTS_DIR, f"{query_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No eval result for {query_id}")
    with open(filepath) as f:
        return json.load(f)


@router.get("/dashboard")
def get_dashboard_all():
    """Serve ALL eval results for the dashboard. No run_id needed."""
    index_path = os.path.join(RESULTS_DIR, "index.json")
    if not os.path.exists(index_path):
        return {"index": [], "data": {}}

    with open(index_path) as f:
        index = json.load(f)

    data = {}
    for entry in index:
        filepath = os.path.join(RESULTS_DIR, f"{entry['query_id']}.json")
        if os.path.exists(filepath):
            with open(filepath) as f:
                data[entry["query_id"]] = json.load(f)

    return {"index": index, "data": data}


@router.get("/dashboard/{run_id}")
async def get_dashboard_single(run_id: str, db: Session = Depends(get_db)):
    """Get dashboard data for a single run."""
    if os.path.exists(RESULTS_DIR):
        index_path = os.path.join(RESULTS_DIR, "index.json")
        if os.path.exists(index_path):
            with open(index_path) as f:
                index = json.load(f)
            match = next((r for r in index if r["run_id"] == run_id), None)
            if match:
                filepath = os.path.join(RESULTS_DIR, f"{match['query_id']}.json")
                if os.path.exists(filepath):
                    with open(filepath) as f:
                        return json.load(f)

    try:
        result = await run_eval(run_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval failed: {str(e)}")
