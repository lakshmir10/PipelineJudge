"""Eval Engine — main orchestrator.

Given a pipeline run, executes all eval dimensions across three layers,
computes chain attribution, applies compliance rules, and produces the
dashboard data contract (DashboardResponse).
"""

import asyncio
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.db import (
    PipelineRun, Pipeline, AgentExecution, HandoffEvent,
    EvalJob, EvalTask, DimensionScore, LayerScore, SystemScore, gen_uuid,
)
from app.engine.eval_config import EVAL_SUITE
from app.engine.llm_judge import llm_judge, JudgeConfig, get_judge_config, set_judge_config
from app.engine.programmatic_judges import (
    JUDGE_REGISTRY, pii_scan, pii_channel_scan, entity_preservation,
    check_regulatory_rules,
)
from app.engine.chain_attribution import compute_chain_attribution
from app.engine.compositor import (
    compute_layer_score, compute_system_score,
    normalize_llm_score, compute_subdimension_composite,
)


async def run_eval(run_id: str, db: Session, judge_config: dict = None) -> dict:
    """Execute a full evaluation against a pipeline run.

    Args:
        run_id: Pipeline run ID to evaluate
        db: Database session
        judge_config: Optional dict with keys:
            - default_model: model string (e.g. "gpt-4o-mini")
            - overrides: {dimension: model_string}
            - api_keys: {provider: key} for BYOK

    Returns the DashboardResponse-shaped dict.
    """
    start_time = time.time()
    suite = EVAL_SUITE

    # Apply judge configuration if provided
    if judge_config:
        cfg = JudgeConfig(
            default_model=judge_config.get("default_model"),
            overrides=judge_config.get("overrides", {}),
            api_keys=judge_config.get("api_keys", {}),
            use_mock=judge_config.get("use_mock"),
        )
        set_judge_config(cfg)
    else:
        cfg = get_judge_config()

    # Load trace
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    pipeline = db.query(Pipeline).filter(Pipeline.id == run.pipeline_id).first()
    executions = db.query(AgentExecution).filter(
        AgentExecution.run_id == run_id
    ).order_by(AgentExecution.execution_order).all()
    handoff_records = db.query(HandoffEvent).filter(HandoffEvent.run_id == run_id).all()

    exec_id_to_name = {e.id: e.agent_name for e in executions}

    # Convert to dicts for judge functions
    agents = [
        {
            "agent_name": e.agent_name,
            "agent_type": e.agent_type,
            "input_payload": e.input_payload or {},
            "output_payload": e.output_payload or {},
            "model_id": e.model_id,
            "prompt_template_hash": e.prompt_template_hash,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "latency_ms": e.latency_ms,
        }
        for e in executions
    ]

    handoffs = [
        {
            "id": h.id,
            "_source_name": exec_id_to_name.get(h.source_execution_id, "?"),
            "_target_name": exec_id_to_name.get(h.target_execution_id, "?"),
            "payload": h.payload or {},
        }
        for h in handoff_records
    ]

    # Create eval job
    job = EvalJob(
        id=gen_uuid(), run_id=run_id, suite_name=suite["name"],
        status="running", started_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()

    # Extract pipeline-level context — works for ANY pipeline shape
    query = run.run_metadata.get("query", "") if run.run_metadata else ""

    # Find the best "answer" across all agents — not necessarily the last one.
    # Search backwards: prefer later agents, but skip verification/adversarial outputs
    # that contain metadata (verified, issues) rather than actual answers.
    final_answer = ""
    citations = []

    # First try: run_metadata might have the final answer
    if run.run_metadata and "final_answer" in run.run_metadata:
        fa = run.run_metadata["final_answer"]
        if isinstance(fa, dict):
            final_answer = fa.get("answer", fa.get("text", str(fa)))
            citations = fa.get("citations", [])
        else:
            final_answer = str(fa)

    # Second try: search agents for the best answer (prefer synthesis, then last non-adversarial)
    _answer_is_real = final_answer and len(final_answer) > 50 and "verified" not in final_answer[:100] and "issues" not in final_answer[:100]
    if not _answer_is_real:
        for agent in reversed(agents):
            out = agent.get("output_payload", {})
            if not isinstance(out, dict):
                continue
            # Skip verification outputs (they have "verified" key, not "answer")
            if "verified" in out or "issues" in out:
                continue
            # Found an agent with an actual answer
            candidate = out.get("answer", out.get("text", out.get("output", "")))
            if candidate and len(str(candidate)) > len(final_answer):
                final_answer = str(candidate)
                citations = out.get("citations", out.get("sources", []))

    # Third try: stringify the last agent's output
    if not final_answer:
        last_output = agents[-1].get("output_payload", {}) if agents else {}
        final_answer = str(last_output)

    # Gather all intermediate outputs for faithfulness/alignment checks
    all_outputs = " ".join(str(a.get("output_payload", "")) for a in agents)

    # Find retrieval-like output if any agent produced chunks
    retrieval_output = ""
    for a in agents:
        out = a.get("output_payload", {})
        if isinstance(out, dict) and ("chunks" in out or "documents" in out or "results" in out):
            retrieval_output = str(out)
            break
    if not retrieval_output:
        retrieval_output = all_outputs

    # First agent's output (for intent capture checks)
    first_agent_output = str(agents[0].get("output_payload", "")) if agents else ""

    synthesis_output = final_answer

    llm_call_count = 0
    total_cost = 0.0
    all_dimension_scores = {}  # {layer: {dim_code: score}}
    all_sub_scores = {}  # {layer: {dim_code: {sub_name: score}}}
    all_descriptions = {}  # {dim_code: {name, description}}

    # ─── LAYER 1: PRODUCT ────────────────────────────────────────────────────

    product_config = suite["layers"]["product"]
    product_scores = {}
    product_subs = {}

    for dim_code, dim_config in product_config["dimensions"].items():
        dim_subs = {}
        all_descriptions[dim_code] = {"name": dim_config["name"], "description": dim_config["description"]}

        for sub_name, sub_config in dim_config.get("subdimensions", {}).items():
            if sub_config["judge_type"] == "llm":
                variables = {
                    "query": query,
                    "agent_output": first_agent_output,
                    "retrieval_output": retrieval_output,
                    "synthesis_output": synthesis_output,
                    "final_answer": final_answer,
                    "citations": str(citations),
                }
                result = await llm_judge(sub_config["prompt"], variables)
                llm_call_count += 1
                score = normalize_llm_score(result.get("score", 3))
            else:
                func = JUDGE_REGISTRY.get(sub_config["function"])
                if func:
                    result = func(agents=agents, handoffs=handoffs, query_data={"query": query})
                    score = result.get("score", 50)
                else:
                    score = 50

            dim_subs[sub_name] = score

        # Compute dimension composite
        sub_weights = {name: cfg.get("weight", 1.0) for name, cfg in dim_config.get("subdimensions", {}).items()}
        dim_score = compute_subdimension_composite(dim_subs, sub_weights)
        product_scores[dim_code] = dim_score
        product_subs[dim_code] = dim_subs

    product_dim_weights = {code: cfg["weight"] for code, cfg in product_config["dimensions"].items()}
    product_layer_score = compute_layer_score(product_scores, product_dim_weights)

    all_dimension_scores["product"] = product_scores
    all_sub_scores["product"] = product_subs

    # ─── LAYER 2: PIPELINE ───────────────────────────────────────────────────

    pipeline_config = suite["layers"]["pipeline"]
    pipeline_scores = {}
    pipeline_subs = {}

    # PAQS — per-agent quality scoring
    paqs_config = pipeline_config["dimensions"]["PAQS"]
    all_descriptions["PAQS"] = {"name": paqs_config["name"], "description": paqs_config["description"]}
    agent_paqs = {}
    agent_paqs_subs = {}

    for agent in agents:
        agent_type = agent["agent_type"]
        rubric = paqs_config.get("agent_rubrics", {}).get(agent_type)
        # Fall back to "custom" rubric for unknown agent types
        if not rubric:
            rubric = paqs_config.get("agent_rubrics", {}).get("custom", {})
        agent_sub_scores = {}

        for sub_name, sub_config in rubric.get("subdimensions", {}).items():
            if sub_config["judge_type"] == "llm":
                variables = {
                    "agent_input": str(agent["input_payload"]),
                    "agent_output": str(agent["output_payload"]),
                    "query": query,
                    "context": retrieval_output,
                }
                result = await llm_judge(sub_config["prompt"], variables)
                llm_call_count += 1
                score = normalize_llm_score(result.get("score", 3))
            else:
                func = JUDGE_REGISTRY.get(sub_config["function"])
                if func:
                    result = func(agents=agents, handoffs=handoffs)
                    score = result.get("score", 50)
                else:
                    score = 50

            agent_sub_scores[sub_name] = score

        sub_weights = {name: cfg.get("weight", 1.0) for name, cfg in rubric.get("subdimensions", {}).items()}
        agent_score = compute_subdimension_composite(agent_sub_scores, sub_weights) if agent_sub_scores else 50
        agent_paqs[agent["agent_name"]] = agent_score
        agent_paqs_subs[agent["agent_name"]] = agent_sub_scores

    # Average PAQS across agents
    paqs_score = round(sum(agent_paqs.values()) / max(len(agent_paqs), 1), 1)
    pipeline_scores["PAQS"] = paqs_score

    # CAS — chain attribution
    cas_config = pipeline_config["dimensions"]["CAS"]
    all_descriptions["CAS"] = {"name": cas_config["name"], "description": cas_config["description"]}
    attribution_result = await compute_chain_attribution(agents, handoffs)
    llm_call_count += len(agents) * 2  # input + output quality per agent

    # CAS score: inverse of how much quality degraded (100 = no degradation, 0 = total collapse)
    max_degradation = sum(abs(a["delta"]) for a in attribution_result["agents"] if a["delta"] < 0)
    cas_score = max(0, round(100 - max_degradation))
    pipeline_scores["CAS"] = cas_score

    # HIS — handoff integrity
    his_config = pipeline_config["dimensions"]["HIS"]
    all_descriptions["HIS"] = {"name": his_config["name"], "description": his_config["description"]}
    handoff_scores = {}

    for i, handoff in enumerate(handoffs):
        source_agent = next((a for a in agents if a["agent_name"] == handoff["_source_name"]), None)
        target_agent = next((a for a in agents if a["agent_name"] == handoff["_target_name"]), None)
        if not source_agent or not target_agent:
            continue

        h_subs = {}

        # Entity preservation (programmatic)
        ep_result = entity_preservation(
            source_output=source_agent["output_payload"],
            handoff_payload=handoff["payload"],
            target_input=target_agent["input_payload"],
        )
        h_subs["Entity Preservation"] = ep_result["score"]

        # Context compression (LLM)
        cc_config = his_config["subdimensions"]["context_compression"]
        cc_result = await llm_judge(cc_config["prompt"], {
            "source_output": str(source_agent["output_payload"]),
            "handoff_payload": str(handoff["payload"]),
            "target_input": str(target_agent["input_payload"]),
        })
        llm_call_count += 1
        h_subs["Context Compression"] = normalize_llm_score(cc_result.get("score", 3))

        # Instruction fidelity (LLM)
        if_config = his_config["subdimensions"]["instruction_fidelity"]
        if_result = await llm_judge(if_config["prompt"], {
            "source_output": str(source_agent["output_payload"]),
            "target_output": str(target_agent["output_payload"]),
        })
        llm_call_count += 1
        h_subs["Instruction Fidelity"] = normalize_llm_score(if_result.get("score", 3))

        sub_weights = {
            "Entity Preservation": 0.40,
            "Context Compression": 0.35,
            "Instruction Fidelity": 0.25,
        }
        his_composite = compute_subdimension_composite(h_subs, sub_weights)
        handoff_key = f"{handoff['_source_name']} → {handoff['_target_name']}"
        handoff_scores[handoff_key] = {"his": his_composite, "subs": h_subs}

    # HIS = minimum across handoffs (weakest link)
    his_values = [h["his"] for h in handoff_scores.values()]
    his_score = min(his_values) if his_values else 50
    pipeline_scores["HIS"] = his_score

    pipeline_dim_weights = {code: cfg["weight"] for code, cfg in pipeline_config["dimensions"].items()}
    pipeline_layer_score = compute_layer_score(pipeline_scores, pipeline_dim_weights)

    all_dimension_scores["pipeline"] = pipeline_scores

    # ─── LAYER 3: COMPLIANCE ─────────────────────────────────────────────────

    compliance_config = suite["layers"]["compliance"]
    compliance_scores = {}
    compliance_subs = {}

    # PII Exposure
    pes_config = compliance_config["dimensions"]["PES"]
    all_descriptions["PES"] = {"name": pes_config["name"], "description": pes_config["description"]}
    pii_result = pii_scan(agents=agents, handoffs=handoffs)
    pii_channel_result = pii_channel_scan(agents=agents, handoffs=handoffs)
    pes_subs = {
        "Detection Coverage": pii_result["score"],
        "Leakage Channels": pii_channel_result["score"],
    }
    pes_score = compute_subdimension_composite(pes_subs, {"Detection Coverage": 0.6, "Leakage Channels": 0.4})
    compliance_scores["PES"] = pes_score
    compliance_subs["PES"] = pes_subs

    # Audit Trail
    atc_config = compliance_config["dimensions"]["ATC"]
    all_descriptions["ATC"] = {"name": atc_config["name"], "description": atc_config["description"]}
    atc_subs = {}
    atc_checks = []
    for sub_name, sub_config in atc_config["subdimensions"].items():
        func = JUDGE_REGISTRY.get(sub_config["function"])
        if func:
            result = func(agents=agents)
            atc_subs[sub_name] = result["score"]
            atc_checks.append({
                "name": sub_name.replace("_", " ").title(),
                "passed": result.get("passed", 0),
                "total": result.get("total", 0),
            })
        else:
            atc_subs[sub_name] = 50

    atc_weights = {name: cfg["weight"] for name, cfg in atc_config["subdimensions"].items()}
    atc_score = compute_subdimension_composite(atc_subs, atc_weights)
    compliance_scores["ATC"] = atc_score
    compliance_subs["ATC"] = atc_subs

    # Regulatory Rules
    rrc_config = compliance_config["dimensions"]["RRC"]
    all_descriptions["RRC"] = {"name": rrc_config["name"], "description": rrc_config["description"]}
    rules_result = check_regulatory_rules(
        rules=rrc_config["rules"],
        query=query,
        final_answer=final_answer,
        pii_findings=pii_result.get("findings", []),
        citations=citations,
    )
    compliance_scores["RRC"] = rules_result["score"]

    compliance_dim_weights = {code: cfg["weight"] for code, cfg in compliance_config["dimensions"].items()}
    compliance_layer_score = compute_layer_score(compliance_scores, compliance_dim_weights)

    all_dimension_scores["compliance"] = compliance_scores

    # ─── SYSTEM SCORE ────────────────────────────────────────────────────────

    layer_scores_map = {
        "product": product_layer_score,
        "pipeline": pipeline_layer_score,
        "compliance": compliance_layer_score,
    }
    layer_weights = {name: cfg["weight"] for name, cfg in suite["layers"].items()}

    system_result = compute_system_score(
        layer_scores_map, layer_weights,
        compliance_floor_threshold=compliance_config.get("floor_threshold", 70),
        compliance_floor_cap=compliance_config.get("floor_cap", 50),
    )

    duration = round(time.time() - start_time, 1)

    # ─── BUILD DASHBOARD RESPONSE ────────────────────────────────────────────

    # Build agents array for dashboard
    dashboard_agents = []
    for agent in agents:
        name = agent["agent_name"]
        attr_data = next((a for a in attribution_result["agents"] if a["name"] == name), {})
        dashboard_agents.append({
            "name": name,
            "type": agent["agent_type"],
            "paqs": agent_paqs.get(name, 50),
            "attribution": attr_data.get("attribution", 0),
            "subs": agent_paqs_subs.get(name, {}),
            "input_quality": attr_data.get("input_quality", 50),
            "output_quality": attr_data.get("output_quality", 50),
        })

    # Build handoffs array
    dashboard_handoffs = []
    for handoff in handoffs:
        key = f"{handoff['_source_name']} → {handoff['_target_name']}"
        h_data = handoff_scores.get(key, {"his": 50, "subs": {}})
        dashboard_handoffs.append({
            "from": handoff["_source_name"],
            "to": handoff["_target_name"],
            "his": h_data["his"],
            "subs": h_data["subs"],
        })

    # Build layers
    dashboard_layers = {}
    for layer_name, layer_config in suite["layers"].items():
        dims = []
        for dim_code, dim_conf in layer_config.get("dimensions", {}).items():
            subs_list = []
            if layer_name in all_sub_scores and dim_code in all_sub_scores[layer_name]:
                for sub_name, sub_score in all_sub_scores[layer_name][dim_code].items():
                    subs_list.append({"name": sub_name.replace("_", " ").title(), "score": sub_score})
            elif layer_name == "compliance" and dim_code in compliance_subs:
                for sub_name, sub_score in compliance_subs[dim_code].items():
                    subs_list.append({"name": sub_name.replace("_", " ").title(), "score": sub_score})

            dims.append({
                "code": dim_code,
                "name": dim_conf.get("name", dim_code),
                "score": all_dimension_scores.get(layer_name, {}).get(dim_code, 50),
                "description": dim_conf.get("description", ""),
                "subs": subs_list,
            })

        dashboard_layers[layer_name] = {
            "score": layer_scores_map[layer_name],
            "weight": layer_config["weight"],
            "dimensions": dims,
        }

    # Store scores in DB
    job.status = "completed"
    job.completed_at = datetime.utcnow()
    job.total_tasks = llm_call_count
    job.completed_tasks = llm_call_count
    job.total_cost_usd = total_cost

    sys_score = SystemScore(
        id=gen_uuid(), job_id=job.id, run_id=run_id,
        overall_score=system_result["overall"],
        product_health=product_layer_score,
        pipeline_health=pipeline_layer_score,
        compliance_health=compliance_layer_score,
        compliance_capped=system_result["compliance_capped"],
    )
    db.add(sys_score)
    db.commit()

    return {
        "pipeline": {
            "name": pipeline.name if pipeline else "unknown",
            "version": pipeline.version if pipeline else "?",
            "run_id": run_id,
        },
        "system": {
            "overall": system_result["overall"],
            "product": product_layer_score,
            "pipeline": pipeline_layer_score,
            "compliance": compliance_layer_score,
            "compliance_capped": system_result["compliance_capped"],
        },
        "layers": dashboard_layers,
        "agents": dashboard_agents,
        "handoffs": dashboard_handoffs,
        "compliance_detail": {
            "pii_findings": [
                {
                    "entity": f["entity"],
                    "type": f["type"],
                    "location": f["location"],
                    "severity": f["severity"],
                }
                for f in pii_result.get("findings", [])
            ],
            "audit_checks": atc_checks,
            "rule_results": rules_result.get("results", []),
        },
        "eval_meta": {
            "suite": suite["name"],
            "duration_sec": duration,
            "tasks": llm_call_count,
            "llm_calls": llm_call_count,
            "cost_usd": round(total_cost, 4),
            "timestamp": datetime.utcnow().isoformat(),
            "judge_config": cfg.to_dict(),
        },
    }
