"""PipelineJudge database models — traces, evals, scores."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


# ─── ENUMS ───────────────────────────────────────────────────────────────────────

class AgentType(str, enum.Enum):
    retrieval = "retrieval"
    analysis = "analysis"
    synthesis = "synthesis"
    adversarial = "adversarial"
    custom = "custom"


class EvalJobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JudgeType(str, enum.Enum):
    llm = "llm"
    programmatic = "programmatic"


class LayerName(str, enum.Enum):
    product = "product"
    pipeline = "pipeline"
    compliance = "compliance"


# ─── TRACE MODELS ────────────────────────────────────────────────────────────────

class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    topology = Column(JSON)  # DAG definition: nodes and edges
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON)

    runs = relationship("PipelineRun", back_populates="pipeline")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String, default="completed")  # completed, failed, timeout
    input_hash = Column(String)
    run_metadata = Column(JSON)

    pipeline = relationship("Pipeline", back_populates="runs")
    executions = relationship("AgentExecution", back_populates="run")
    handoffs = relationship("HandoffEvent", back_populates="run")
    eval_jobs = relationship("EvalJob", back_populates="run")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=gen_uuid)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)  # retrieval, analysis, synthesis, adversarial, custom
    input_payload = Column(JSON)
    output_payload = Column(JSON)
    model_id = Column(String)  # exact model version
    prompt_template_hash = Column(String)
    token_count_input = Column(Integer)
    token_count_output = Column(Integer)
    latency_ms = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    parent_execution_id = Column(String, ForeignKey("agent_executions.id"), nullable=True)
    execution_order = Column(Integer)  # position in pipeline
    metadata_ = Column("metadata", JSON)

    run = relationship("PipelineRun", back_populates="executions")
    parent = relationship("AgentExecution", remote_side=[id])


class HandoffEvent(Base):
    __tablename__ = "handoff_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    source_execution_id = Column(String, ForeignKey("agent_executions.id"), nullable=False)
    target_execution_id = Column(String, ForeignKey("agent_executions.id"), nullable=False)
    payload = Column(JSON)  # what was passed between agents
    payload_hash = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    run = relationship("PipelineRun", back_populates="handoffs")
    source = relationship("AgentExecution", foreign_keys=[source_execution_id])
    target = relationship("AgentExecution", foreign_keys=[target_execution_id])


# ─── EVAL MODELS ─────────────────────────────────────────────────────────────────

class EvalJob(Base):
    __tablename__ = "eval_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    suite_name = Column(String, nullable=False)
    status = Column(String, default="queued")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    error_message = Column(Text)

    run = relationship("PipelineRun", back_populates="eval_jobs")
    tasks = relationship("EvalTask", back_populates="job")
    dimension_scores = relationship("DimensionScore", back_populates="job")
    layer_scores = relationship("LayerScore", back_populates="job")
    system_score = relationship("SystemScore", back_populates="job", uselist=False)


class EvalTask(Base):
    __tablename__ = "eval_tasks"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("eval_jobs.id"), nullable=False)
    layer = Column(String, nullable=False)  # product, pipeline, compliance
    dimension_code = Column(String, nullable=False)
    subdimension_name = Column(String, nullable=False)
    agent_name = Column(String)  # nullable — some evals are pipeline-level
    handoff_id = Column(String, ForeignKey("handoff_events.id"), nullable=True)
    judge_type = Column(String, nullable=False)  # llm, programmatic
    judge_model = Column(String)  # model used if llm judge
    judge_input = Column(JSON)
    judge_output = Column(JSON)  # raw response
    raw_score = Column(Float)
    normalized_score = Column(Float)  # 0-100
    reasoning = Column(Text)
    status = Column(String, default="queued")
    latency_ms = Column(Integer)
    cost_usd = Column(Float, default=0.0)

    job = relationship("EvalJob", back_populates="tasks")


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("eval_jobs.id"), nullable=False)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    layer = Column(String, nullable=False)
    dimension_code = Column(String, nullable=False)
    dimension_name = Column(String, nullable=False)
    description = Column(String)
    agent_name = Column(String)  # nullable — for pipeline-level dims
    composite_score = Column(Float, nullable=False)
    sub_scores = Column(JSON)  # {subdimension_name: score}
    computed_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("EvalJob", back_populates="dimension_scores")


class LayerScore(Base):
    __tablename__ = "layer_scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("eval_jobs.id"), nullable=False)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    layer = Column(String, nullable=False)
    composite_score = Column(Float, nullable=False)
    dimension_scores_json = Column(JSON)  # {dim_code: score}
    computed_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("EvalJob", back_populates="layer_scores")


class SystemScore(Base):
    __tablename__ = "system_scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("eval_jobs.id"), nullable=False, unique=True)
    run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    product_health = Column(Float)
    pipeline_health = Column(Float)
    compliance_health = Column(Float)
    compliance_capped = Column(Boolean, default=False)
    computed_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("EvalJob", back_populates="system_score")
