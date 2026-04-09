# PipelineJudge

Evaluation framework for multi-agent AI pipelines. Measures product outcomes, not model metrics.

Most AI evaluation tools measure whether the model got the answer right. PipelineJudge measures whether the *pipeline* worked: Did the user achieve their goal? Which agent helped and which hurt? Is the system leaking data?

## What Makes This Different

Three capabilities no other eval framework offers together.

**Product-centric evaluation.** Task completion funnels, decision quality scoring, explanation alignment. A PM configures what "good" means for their product via a YAML file. Scores reflect whether users achieved their goals, not whether embeddings were similar.

**Multi-agent chain attribution.** For pipelines with 3, 4, or 10 agents, PipelineJudge computes a quality delta for each agent: how much did it improve or degrade the output compared to what it received? Produces a waterfall chart showing exactly where quality was gained or lost. No other tool does this.

**Compliance integrated into scoring.** PII scanning, audit trail completeness, regulatory rule checking — all in the same scoring framework as quality. With a hard compliance floor: if PII leaks anywhere in the pipeline, the overall score is capped regardless of how good the quality scores are.

## Quick Start

### Run the Demo

```bash
git clone https://github.com/lakshmir10/PipelineJudge
cd pipelinejudge

pip install fastapi uvicorn sqlalchemy pydantic pyyaml httpx

python run_full_demo.py
```

This runs a 4-agent RAG pipeline against 10 test queries (5 clean, 5 with planted failure modes), evaluates each run across 3 layers and 9 dimensions, and outputs scored results. Takes about 10 seconds.

### Start the API

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

Then:
- `GET /health` — service status
- `GET /evals/results` — list all evaluated runs
- `GET /evals/results/clean-01` — full eval result for a specific query
- `GET /evals/results/fail-D1` — a PII leakage failure (compliance-capped)

### Use the SDK (3 Lines)

```python
from sdk.evaluate import evaluate

result = evaluate(
    query="What is the refund policy?",
    steps=[
        {"name": "classifier", "output": {"intent": "refund", "category": "billing"}},
        {"name": "retriever", "output": {"chunks": [{"doc_id": "doc-1", "content": "..."}]}},
        {"name": "generator", "output": {"answer": "Refunds are available within 30 days...", "citations": ["doc-1"]}},
    ]
)

print(result["system"]["overall"])        # 71.8
print(result["system"]["compliance"])     # 78.1
```

Pass what your pipeline did as plain dicts. PipelineJudge auto-detects agent types, infers handoffs, runs all judges, and returns the full evaluation. No server needed.

## Architecture

### Three Evaluation Layers

```
+-------------------+     +-------------------+     +-------------------+
|   PRODUCT (35%)   |     |  PIPELINE (40%)   |     | COMPLIANCE (25%)  |
|                   |     |                   |     |                   |
| Task Completion   |     | Per-Agent Quality |     | PII Exposure      |
|   Fidelity (TCF)  |     |   (PAQS)          |     |   (PES)           |
|                   |     |                   |     |                   |
| Decision Quality  |     | Chain Attribution |     | Audit Trail       |
|   (DQS)           |     |   (CAS)           |     |   Completeness    |
|                   |     |                   |     |   (ATC)           |
| Explanation       |     | Handoff Integrity |     |                   |
|   Alignment (EOA) |     |   (HIS)           |     | Regulatory Rules  |
|                   |     |                   |     |   (RRC)           |
+-------------------+     +-------------------+     +-------------------+
         |                         |                         |
         v                         v                         v
    +---------------------------------------------------------+
    |              SYSTEM SCORE (weighted composite)           |
    |                                                          |
    |  Compliance Floor Rule: if compliance < 70,              |
    |  overall score is capped at 50 regardless of quality.    |
    +---------------------------------------------------------+
```

### Product Layer (35% weight)

Measures whether the pipeline achieved the user's goal. Not "was the retrieval good?" but "could the user act on this response?"

- **Task Completion Fidelity (TCF):** Intent capture, execution correctness, goal achievement. Scored by LLM judges with calibrated rubrics.
- **Decision Quality (DQS):** Retrieval relevance, ranking precision, actionability. Mix of programmatic and LLM judges.
- **Explanation Alignment (EOA):** Does the reasoning chain support the conclusion? Are citations complete? LLM judges check faithfulness against source documents.

### Pipeline Layer (40% weight)

Measures multi-agent pipeline health. Which agent is the bottleneck?

- **Per-Agent Quality Score (PAQS):** Each agent type has its own rubric. An analysis agent is judged on intent capture and reformulation quality. A retrieval agent on source authority, recency, coverage, and diversity. A synthesis agent on faithfulness, coherence, and info preservation. An adversarial agent on critique specificity and constructiveness.
- **Chain Attribution (CAS):** Quality delta per agent. PipelineJudge scores the quality of each agent's input and output separately, computes the delta, and normalizes to attribution weights. Produces a waterfall chart. Identifies the bottleneck.
- **Handoff Integrity (HIS):** Entity preservation across agent boundaries. Checks that key data (numbers, proper nouns, structured fields) survives from one agent to the next. Score is the weakest link across all handoffs.

### Compliance Layer (25% weight)

Measures safety and regulatory compliance, integrated into the same scoring framework.

- **PII Exposure (PES):** Scans all pipeline stages (agent inputs, outputs, handoff payloads) for personal data: names in context, emails, phone numbers, government IDs, credit cards. Includes false positive filtering (business emails excluded, name-blocklist for compound nouns).
- **Audit Trail Completeness (ATC):** Checks input traceability, model version pinning, prompt hash presence, timestamp integrity. Every AI decision should be reconstructable.
- **Regulatory Rules (RRC):** Configurable domain-specific rules. GDPR data residency disclosure, financial risk disclaimers, HR PII redaction, source attribution requirements.

### Compliance Floor Rule

If the compliance layer score drops below 70, the overall system score is capped at 50 regardless of how well the product and pipeline layers scored. A pipeline that leaks PII cannot score well.

## Demo Pipeline: Nexus Cloud RAG

The included demo is a 4-agent enterprise RAG pipeline for a fictional SaaS company (Nexus Cloud) with 14 knowledge base documents across billing, product, security, HR, and legal categories.

**Agents:** Query Analyst -> Retrieval -> Synthesis -> Verification

**10 test queries** with 3 planted failure modes:

| Failure Mode | Queries | What Goes Wrong | What PipelineJudge Catches |
|---|---|---|---|
| Ambiguity | fail-A1, fail-A2 | "data retention" is ambiguous (customer 90 days vs employee 7 years). Query Analyst picks only one interpretation. | Intent Capture drops to 25/100. Chain attribution identifies Query Analyst as the bottleneck. |
| Hallucination | fail-C1 | Synthesis invents "$5,000 per hour penalty" not in source documents. | Faithfulness judge flags unsupported claims. Explanation Alignment drops. |
| PII Leakage | fail-D1, fail-D2 | HR documents contain employee PII (name, personal email, phone). Retrieved content leaks through pipeline stages. | PII scanner detects 9-11 instances. Compliance drops to 39-44. Compliance floor caps overall score to 50. |

## Configuration

Evaluation dimensions, weights, judge types, prompts, and compliance rules are defined in `backend/eval_suites/enterprise_rag_v1.yaml`. A PM can modify this file to configure what matters for their product without writing Python.

```yaml
product:
  weight: 0.35
  dimensions:
    TCF:
      name: Task Completion Fidelity
      weight: 0.40
      subdimensions:
        intent_capture:
          judge_type: llm
          weight: 0.35
          prompt: |
            You are evaluating whether an AI system correctly
            understood the user's intent...

compliance:
  weight: 0.25
  floor_threshold: 70    # Below this, cap overall score
  floor_cap: 50          # Cap value when floor is active
  dimensions:
    PES:
      name: PII Exposure
      weight: 0.40
```

## Judge Types

**LLM Judges** (require API key or use built-in mock): Score dimensions that need reasoning — intent capture, faithfulness, actionability, explanation alignment. Each judge has a calibrated rubric with 1-5 scoring and specific criteria per level.

**Programmatic Judges** (zero cost, instant): Deterministic checks — PII regex scanning with false positive filtering, entity preservation counting, audit trail field validation, retrieval metrics (relevance, recency, coverage, diversity), regulatory rule evaluation.

The default mode uses content-aware mock judges that produce realistic, differentiated scores by analyzing actual pipeline content. Set `PIPELINEJUDGE_MOCK_LLM=false` and provide an API key to use real LLM judges via litellm.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service status |
| `/traces/upload` | POST | Upload a pipeline trace |
| `/traces/runs` | GET | List recent pipeline runs |
| `/traces/runs/{run_id}` | GET | Get full trace for a run |
| `/evals/run?run_id=X` | POST | Trigger evaluation on a run |
| `/evals/results` | GET | List all evaluated runs |
| `/evals/results/{query_id}` | GET | Get full eval result |

## File Structure

```
pipelinejudge/
  backend/
    app/
      api/              # FastAPI routes (traces, evals)
      engine/           # Eval engine, judges, attribution, scoring
        eval_engine.py      # Main orchestrator (3 layers, 9 dimensions)
        eval_config.py      # Full eval suite config (Python dict, mirrors YAML)
        llm_judge.py        # LLM + content-aware mock judges
        programmatic_judges.py  # 14 deterministic judges
        chain_attribution.py    # Quality delta + bottleneck identification
        compositor.py       # Weighted scoring + compliance floor
      models/           # SQLAlchemy models (9 tables)
    eval_results/       # Pre-computed eval results (10 runs)
    eval_suites/        # YAML configuration
  demo/
    knowledge_base/     # 14 Nexus Cloud KB documents
    rag_pipeline.py     # 4-agent demo pipeline with planted failures
    test_queries/       # 10 test queries with ground truth
  sdk/
    evaluate.py         # SDK: evaluate() function for developers
  frontend/
    evalforge_dashboard.jsx  # React dashboard (3 views)
  run_full_demo.py      # One command to run everything
```

## Tech Stack

Python 3.11+, FastAPI, SQLAlchemy, litellm (for real LLM judges), React + Recharts (dashboard).

## License

MIT
