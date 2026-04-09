"""Pydantic schemas — API request/response models matching the dashboard data contract."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── TRACE UPLOAD ────────────────────────────────────────────────────────────────

class AgentExecutionIn(BaseModel):
    name: str
    type: str  # retrieval, analysis, synthesis, adversarial, custom
    input_payload: dict
    output_payload: dict
    model_id: Optional[str] = None
    prompt_template_hash: Optional[str] = None
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    latency_ms: Optional[int] = None
    parent: Optional[str] = None  # parent agent name for DAG reconstruction
    execution_order: Optional[int] = None
    metadata: Optional[dict] = None


class HandoffIn(BaseModel):
    from_agent: str
    to_agent: str
    payload: dict


class TraceUpload(BaseModel):
    pipeline_name: str
    pipeline_version: str = "1.0.0"
    agents: list[AgentExecutionIn]
    handoffs: list[HandoffIn] = []
    run_metadata: Optional[dict] = None


# ─── EVAL TRIGGER ────────────────────────────────────────────────────────────────

class EvalRunRequest(BaseModel):
    run_id: str
    suite_name: str = "default"


# ─── DASHBOARD RESPONSE (matches frontend EVAL_DATA contract) ────────────────────

class SubScore(BaseModel):
    name: str
    score: float


class DimensionOut(BaseModel):
    code: str
    name: str
    score: float
    description: str
    subs: list[SubScore] = []


class LayerOut(BaseModel):
    score: float
    weight: float
    dimensions: list[DimensionOut]


class AgentOut(BaseModel):
    name: str
    type: str
    paqs: float
    attribution: float
    subs: dict[str, float]  # {subdimension_name: score}
    input_quality: float
    output_quality: float


class HandoffOut(BaseModel):
    from_agent: str = Field(alias="from")
    to_agent: str = Field(alias="to")
    his: float
    subs: dict[str, float]

    class Config:
        populate_by_name = True


class PIIFinding(BaseModel):
    entity: str
    type: str
    location: str
    severity: str


class AuditCheck(BaseModel):
    name: str
    passed: int
    total: int


class RuleResult(BaseModel):
    rule: str
    triggered: bool
    satisfied: bool
    severity: str


class ComplianceDetail(BaseModel):
    pii_findings: list[PIIFinding]
    audit_checks: list[AuditCheck]
    rule_results: list[RuleResult]


class EvalMeta(BaseModel):
    suite: str
    duration_sec: float
    tasks: int
    llm_calls: int
    cost_usd: float
    timestamp: str


class PipelineInfo(BaseModel):
    name: str
    version: str
    run_id: str


class SystemScoreOut(BaseModel):
    overall: float
    product: float
    pipeline: float
    compliance: float
    compliance_capped: bool


class DashboardResponse(BaseModel):
    """Full dashboard payload — matches the frontend EVAL_DATA contract exactly."""
    pipeline: PipelineInfo
    system: SystemScoreOut
    layers: dict[str, LayerOut]  # {product, pipeline, compliance}
    agents: list[AgentOut]
    handoffs: list[HandoffOut]
    compliance_detail: ComplianceDetail
    eval_meta: EvalMeta
