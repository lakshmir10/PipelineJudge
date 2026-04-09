"""Nexus Cloud RAG Pipeline — 4-agent demo system for EvalForge.

Agents: Query Analyst → Retrieval → Synthesis → Verification
Uses LiteLLM for LLM calls. Falls back to mock responses if no API key is set.
"""

import os
import json
import time
import hashlib
from typing import Optional

try:
    import litellm
    litellm.set_verbose = False
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from demo.knowledge_base.nexus_cloud_kb import search_kb

MODEL = os.getenv("PIPELINEJUDGE_LLM_MODEL", "claude-sonnet-4-20250514")
USE_MOCK = os.getenv("PIPELINEJUDGE_MOCK_LLM", "true").lower() == "true"


def _llm_call(system_prompt: str, user_prompt: str, model: str = None) -> str:
    """Call LLM via LiteLLM, or return a structured mock for demo."""
    if USE_MOCK or not HAS_LITELLM:
        return None  # Signal to caller to use mock logic
    try:
        response = litellm.completion(
            model=model or MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}, using mock")
        return None


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


# ─── AGENT 1: QUERY ANALYST ─────────────────────────────────────────────────────

def query_analyst(user_query: str) -> dict:
    """Analyze query, produce reformulated search terms and filters."""
    start = time.time()

    system_prompt = (
        "You are a query analyst for an enterprise knowledge base. Given a user query, "
        "produce: 1) reformulated search terms (keywords that will find relevant docs), "
        "2) category filter if applicable (billing, product, security, hr, legal), "
        "3) whether the query is ambiguous and might match multiple topics. "
        "Respond in JSON: {\"search_terms\": [...], \"category\": \"...\" or null, "
        "\"is_ambiguous\": bool, \"interpretations\": [...]}"
    )

    llm_result = _llm_call(system_prompt, user_query)

    if llm_result:
        try:
            parsed = json.loads(llm_result)
        except json.JSONDecodeError:
            parsed = None

    # Mock / fallback logic — intentionally imperfect for demo
    if not llm_result or not parsed:
        query_lower = user_query.lower()
        search_terms = user_query.lower().replace("?", "").split()
        # Remove stop words
        stop = {"what", "is", "the", "how", "do", "i", "for", "a", "an", "to", "of", "my", "our", "does", "can", "should", "who", "you", "about"}
        search_terms = [t for t in search_terms if t not in stop]

        category = None
        if any(w in query_lower for w in ["price", "billing", "refund", "cost", "tier", "plan"]):
            category = "billing"
        elif any(w in query_lower for w in ["api", "sso", "export", "integration", "configure"]):
            category = "product"
        elif any(w in query_lower for w in ["security", "compliance", "soc", "gdpr", "data stored", "data residency"]):
            category = "security"
        elif any(w in query_lower for w in ["leave", "expense", "remote", "hr", "employee"]):
            category = "hr"
        elif any(w in query_lower for w in ["sla", "contract", "agreement", "dpa", "legal"]):
            category = "legal"

        # INTENTIONAL WEAKNESS: ambiguous queries get a single category, not both
        # This is the planted failure mode for query ambiguity
        is_ambiguous = "retention" in query_lower or ("data" in query_lower and "leave" not in query_lower and category is None)
        if is_ambiguous and category is None:
            # Picks security by default — misses HR interpretation
            category = "security"

        parsed = {
            "search_terms": search_terms,
            "category": category,
            "is_ambiguous": is_ambiguous,
            "interpretations": ["customer data context"] if is_ambiguous else [],
        }

    latency = int((time.time() - start) * 1000)

    return {
        "agent_name": "Query Analyst",
        "agent_type": "analysis",
        "input": {"query": user_query},
        "output": parsed,
        "model_id": MODEL if not USE_MOCK else "mock",
        "prompt_hash": _hash(system_prompt),
        "latency_ms": latency,
    }


# ─── AGENT 2: RETRIEVAL ─────────────────────────────────────────────────────────

def retrieval_agent(analyst_output: dict) -> dict:
    """Retrieve relevant documents from the knowledge base."""
    start = time.time()

    search_terms = analyst_output.get("search_terms", [])
    category = analyst_output.get("category")
    filters = {"category": category} if category else {}

    chunks = search_kb(search_terms, filters=filters, top_k=4)

    # Format for downstream
    retrieved = []
    for doc in chunks:
        retrieved.append({
            "doc_id": doc["id"],
            "title": doc["title"],
            "content": doc["content"],
            "category": doc["category"],
            "updated": doc["updated"],
            "relevance_score": round(doc.get("_score", 0), 2),
        })

    latency = int((time.time() - start) * 1000)

    return {
        "agent_name": "Retrieval",
        "agent_type": "retrieval",
        "input": {"search_terms": search_terms, "category": category},
        "output": {"chunks": retrieved, "total_found": len(retrieved)},
        "model_id": "keyword-search-v1",
        "prompt_hash": None,
        "latency_ms": latency,
    }


# ─── AGENT 3: SYNTHESIS ─────────────────────────────────────────────────────────

def synthesis_agent(user_query: str, retrieval_output: dict) -> dict:
    """Generate an answer from retrieved chunks with citations."""
    start = time.time()

    chunks = retrieval_output.get("chunks", [])
    context = "\n\n".join(
        f"[Source: {c['title']} ({c['doc_id']})]\n{c['content']}"
        for c in chunks
    )

    system_prompt = (
        "You are an enterprise knowledge assistant. Given retrieved documents, answer the "
        "user's question with specific citations. Be precise. Do not invent information "
        "not present in the sources. If the sources don't contain enough information to "
        "fully answer, say so explicitly. "
        "Respond in JSON: {\"answer\": \"...\", \"citations\": [...], \"confidence\": 0.0-1.0}"
    )
    user_prompt = f"Question: {user_query}\n\nRetrieved documents:\n{context}"

    llm_result = _llm_call(system_prompt, user_prompt)

    if llm_result:
        try:
            parsed = json.loads(llm_result)
        except json.JSONDecodeError:
            parsed = None

    if not llm_result or not parsed:
        # Mock synthesis — generates reasonable answers from chunks
        if not chunks:
            parsed = {
                "answer": "I could not find relevant information to answer this question.",
                "citations": [],
                "confidence": 0.1,
            }
        else:
            # Use first chunk as primary answer source
            primary = chunks[0]
            # Truncate content for answer
            answer_text = primary["content"][:300]
            if len(primary["content"]) > 300:
                answer_text += "..."

            citations = [c["doc_id"] for c in chunks[:3]]

            # INTENTIONAL WEAKNESS for hallucination failure mode:
            # If query mentions "penalties" or "financial" and SLA doc is retrieved,
            # inject a hallucinated specific dollar amount
            query_lower = user_query.lower()
            if ("penalt" in query_lower or "financial" in query_lower) and any("legal-001" == c["doc_id"] for c in chunks):
                answer_text = (
                    "Nexus Cloud's SLA guarantees 99.9% uptime for Enterprise customers. "
                    "When uptime falls below this threshold, financial penalties apply: "
                    "10% credit for 99.0-99.9%, 25% credit for 95.0-99.0%, and 50% credit "
                    "for uptime below 95.0%. Additionally, for critical outages exceeding "
                    "4 hours, Nexus Cloud pays a penalty of $5,000 per hour of downtime "
                    "directly to affected enterprise customers."
                )
                # The "$5,000 per hour" part is HALLUCINATED — not in the source docs

            parsed = {
                "answer": answer_text,
                "citations": citations,
                "confidence": 0.82 if len(chunks) >= 2 else 0.65,
            }

    latency = int((time.time() - start) * 1000)

    return {
        "agent_name": "Synthesis",
        "agent_type": "synthesis",
        "input": {"query": user_query, "chunks": [{"doc_id": c["doc_id"], "title": c["title"]} for c in chunks]},
        "output": parsed,
        "model_id": MODEL if not USE_MOCK else "mock",
        "prompt_hash": _hash(system_prompt),
        "latency_ms": latency,
        # Keep full chunk content in metadata for PII scanning
        "_intermediate_context": context,
    }


# ─── AGENT 4: VERIFICATION ──────────────────────────────────────────────────────

def verification_agent(synthesis_output: dict, chunks: list) -> dict:
    """Fact-check the synthesized answer against source chunks."""
    start = time.time()

    answer = synthesis_output.get("answer", "")
    context = "\n\n".join(c.get("content", "") for c in chunks)

    system_prompt = (
        "You are a fact-checker. Given an answer and source documents, verify that every "
        "claim in the answer is supported by the sources. Flag any claims that are not "
        "directly stated in the sources. "
        "Respond in JSON: {\"verified\": bool, \"confidence\": 0.0-1.0, "
        "\"issues\": [{\"claim\": \"...\", \"problem\": \"...\"}], "
        "\"unsupported_claims\": [...]}"
    )
    user_prompt = f"Answer to verify:\n{answer}\n\nSource documents:\n{context}"

    llm_result = _llm_call(system_prompt, user_prompt)

    if llm_result:
        try:
            parsed = json.loads(llm_result)
        except json.JSONDecodeError:
            parsed = None

    if not llm_result or not parsed:
        # Mock verification — intentionally weak to demonstrate eval value
        issues = []

        # Check for obvious hallucination markers
        hallucination_phrases = ["$5,000", "per hour of downtime", "10x the downtime cost"]
        for phrase in hallucination_phrases:
            if phrase in answer and phrase not in context:
                issues.append({
                    "claim": phrase,
                    "problem": "Not found in source documents",
                })

        # INTENTIONAL WEAKNESS: doesn't catch all hallucinations
        # Only checks exact phrase matches, misses paraphrased hallucinations
        parsed = {
            "verified": len(issues) == 0,
            "confidence": 0.75 if len(issues) == 0 else 0.4,
            "issues": issues,
            "unsupported_claims": [i["claim"] for i in issues],
        }

    latency = int((time.time() - start) * 1000)

    return {
        "agent_name": "Verification",
        "agent_type": "adversarial",
        "input": {"answer": answer, "num_source_chunks": len(chunks)},
        "output": parsed,
        "model_id": MODEL if not USE_MOCK else "mock",
        "prompt_hash": _hash(system_prompt),
        "latency_ms": latency,
    }


# ─── PIPELINE ORCHESTRATOR ──────────────────────────────────────────────────────

def run_pipeline(user_query: str) -> dict:
    """Execute the full 4-agent RAG pipeline and return a trace."""

    # Agent 1: Query Analyst
    analyst_result = query_analyst(user_query)

    # Agent 2: Retrieval
    retrieval_result = retrieval_agent(analyst_result["output"])

    # Agent 3: Synthesis
    synthesis_result = synthesis_agent(user_query, retrieval_result["output"])

    # Agent 4: Verification
    verification_result = verification_agent(
        synthesis_result["output"],
        retrieval_result["output"]["chunks"],
    )

    # Build trace in EvalForge upload format
    trace = {
        "pipeline_name": "Nexus Cloud RAG Pipeline",
        "pipeline_version": "1.2.0",
        "agents": [
            {
                "name": r["agent_name"],
                "type": r["agent_type"],
                "input_payload": r["input"],
                "output_payload": r["output"],
                "model_id": r["model_id"],
                "prompt_template_hash": r.get("prompt_hash"),
                "latency_ms": r["latency_ms"],
            }
            for r in [analyst_result, retrieval_result, synthesis_result, verification_result]
        ],
        "handoffs": [
            {
                "from_agent": "Query Analyst",
                "to_agent": "Retrieval",
                "payload": analyst_result["output"],
            },
            {
                "from_agent": "Retrieval",
                "to_agent": "Synthesis",
                "payload": retrieval_result["output"],
            },
            {
                "from_agent": "Synthesis",
                "to_agent": "Verification",
                "payload": {
                    "answer": synthesis_result["output"].get("answer", ""),
                    "citations": synthesis_result["output"].get("citations", []),
                    # Include intermediate context — this is where PII leaks
                    "_intermediate_context": synthesis_result.get("_intermediate_context", ""),
                },
            },
        ],
        "run_metadata": {
            "query": user_query,
            "final_answer": verification_result["output"] if verification_result["output"].get("verified") else synthesis_result["output"],
        },
    }

    return trace


# ─── CLI ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from demo.test_queries.queries import get_test_queries

    queries = get_test_queries()

    for q in queries:
        print(f"\n{'='*70}")
        print(f"[{q['id']}] {q['query']}")
        print(f"  Failure mode: {q['failure_mode'] or 'none'}")

        trace = run_pipeline(q["query"])

        # Summary
        agents = trace["agents"]
        print(f"  Agents: {' → '.join(a['name'] for a in agents)}")
        print(f"  Total latency: {sum(a['latency_ms'] for a in agents)}ms")

        synth = agents[2]["output_payload"]
        print(f"  Answer preview: {synth.get('answer', '')[:100]}...")
        print(f"  Citations: {synth.get('citations', [])}")

        verif = agents[3]["output_payload"]
        print(f"  Verified: {verif.get('verified')}, Issues: {len(verif.get('issues', []))}")
