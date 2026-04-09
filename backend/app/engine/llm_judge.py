"""LLM Judge — evaluation via any LLM model with BYOK/BYOM support.

Supports 100+ models via litellm:
  - Anthropic: claude-sonnet-4-20250514, claude-haiku-4-5-20251001
  - OpenAI: gpt-4o, gpt-4o-mini
  - Google: gemini-2.0-flash, gemini-2.5-pro
  - Groq: groq/llama-3.3-70b-versatile
  - Together: together_ai/meta-llama/Llama-3.3-70B
  - DeepSeek: deepseek/deepseek-chat
  - Local: ollama/llama3.2

Users provide:
  - API key for their chosen provider (env var or BYOK via API)
  - Model string (default or per-dimension overrides)

Falls back to content-aware mock when no API key is available.
"""

import json
import asyncio
import os
import re
import hashlib
import time

try:
    import litellm
    litellm.set_verbose = False
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

from app.config import LLM_MODEL, LLM_MODEL_CHEAP, LLM_TIMEOUT, LLM_MAX_RETRIES


# ─── Judge Configuration ─────────────────────────────────────────────────────

class JudgeConfig:
    """Configuration for which models to use for LLM judges.

    Can be set globally via env vars, or per-eval via the API.
    """
    def __init__(
        self,
        default_model: str = None,
        overrides: dict = None,
        api_keys: dict = None,
        use_mock: bool = None,
    ):
        self.default_model = default_model or os.getenv(
            "PIPELINEJUDGE_JUDGE_MODEL", LLM_MODEL_CHEAP
        )
        self.overrides = overrides or {}  # {dimension_name: model_string}
        self.api_keys = api_keys or {}    # {provider: key} for BYOK

        # Auto-detect mock mode: use mock if explicitly set OR if no API keys available
        if use_mock is not None:
            self.use_mock = use_mock
        else:
            env_mock = os.getenv("PIPELINEJUDGE_MOCK_LLM", "").lower()
            if env_mock == "false":
                self.use_mock = False
            elif env_mock == "true":
                self.use_mock = True
            else:
                # Auto-detect: check if any LLM API key is available
                self.use_mock = not self._has_any_api_key()

    def _has_any_api_key(self) -> bool:
        """Check if any LLM provider API key is available."""
        providers = [
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY",
            "GROQ_API_KEY", "TOGETHER_API_KEY", "DEEPSEEK_API_KEY",
            "COHERE_API_KEY", "MISTRAL_API_KEY",
        ]
        # Check env vars
        if any(os.getenv(k) for k in providers):
            return True
        # Check BYOK keys
        if self.api_keys:
            return True
        return False

    def get_model_for_dimension(self, dimension: str) -> str:
        """Get the model to use for a specific eval dimension."""
        return self.overrides.get(dimension, self.default_model)

    def apply_byok(self):
        """Set BYOK API keys as env vars so litellm picks them up."""
        key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "cohere": "COHERE_API_KEY",
            "mistral": "MISTRAL_API_KEY",
        }
        for provider, key in self.api_keys.items():
            env_var = key_map.get(provider.lower())
            if env_var and key:
                os.environ[env_var] = key

    def to_dict(self) -> dict:
        """Serialize for inclusion in eval results."""
        return {
            "default_model": self.default_model,
            "overrides": self.overrides,
            "use_mock": self.use_mock,
            "has_api_key": self._has_any_api_key(),
        }


# Global default config (used when no per-eval config is provided)
_default_config = None

def get_judge_config() -> JudgeConfig:
    global _default_config
    if _default_config is None:
        _default_config = JudgeConfig()
    return _default_config

def set_judge_config(config: JudgeConfig):
    global _default_config
    _default_config = config


# ─── Core Judge Function ──────────────────────────────────────────────────────

def _truncate(text: str, max_len: int = 2000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"... [truncated, {len(text) - max_len} chars omitted]"


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and preamble."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


async def llm_judge(
    prompt_template: str,
    variables: dict,
    model: str = None,
    dimension: str = None,
    config: JudgeConfig = None,
) -> dict:
    """Execute an LLM judge evaluation.

    Args:
        prompt_template: Prompt with {variable} placeholders
        variables: Dict of values to fill into the template
        model: Explicit model override (highest priority)
        dimension: Eval dimension name (for per-dimension model routing)
        config: JudgeConfig for BYOK/BYOM (uses global default if None)

    Returns:
        {"score": float, "reasoning": str, "model": str, ...}
    """
    cfg = config or get_judge_config()

    # Fill template
    prompt = prompt_template
    for key, value in variables.items():
        text_val = _truncate(str(value)) if isinstance(value, (dict, list)) else str(value)
        prompt = prompt.replace("{" + key + "}", text_val)

    # Determine if we should use mock
    if cfg.use_mock or not HAS_LITELLM:
        result = _mock_judge(prompt, variables)
        result["model"] = "mock"
        result["mock"] = True
        return result

    # Apply BYOK keys
    if cfg.api_keys:
        cfg.apply_byok()

    # Resolve model: explicit > dimension override > default
    target_model = model or cfg.get_model_for_dimension(dimension or "") or cfg.default_model

    for attempt in range(LLM_MAX_RETRIES):
        try:
            start_time = time.time()
            response = await asyncio.to_thread(
                litellm.completion,
                model=target_model,
                messages=[
                    {"role": "system", "content": "You are an AI evaluation judge. Respond ONLY with valid JSON. No preamble."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.1,
                timeout=LLM_TIMEOUT,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            text = response.choices[0].message.content
            parsed = _parse_json_response(text)

            if parsed and "score" in parsed:
                return {
                    "score": parsed["score"],
                    "reasoning": parsed.get("reasoning", ""),
                    "raw_response": text,
                    "model": target_model,
                    "mock": False,
                    "latency_ms": latency_ms,
                    "tokens": {
                        "input": getattr(response.usage, "prompt_tokens", 0),
                        "output": getattr(response.usage, "completion_tokens", 0),
                    },
                    **{k: v for k, v in parsed.items() if k not in ("score", "reasoning")},
                }

            if attempt < LLM_MAX_RETRIES - 1:
                await asyncio.sleep(1)
                continue

        except Exception as e:
            if attempt < LLM_MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            # Final attempt failed — fall back to mock with warning
            result = _mock_judge(prompt, variables)
            result["model"] = "mock (fallback)"
            result["mock"] = True
            result["error"] = f"LLM call failed after {LLM_MAX_RETRIES} attempts: {str(e)}"
            return result

    result = _mock_judge(prompt, variables)
    result["model"] = "mock (parse failure)"
    result["mock"] = True
    return result


# ─── Content-Aware Mock Judge ─────────────────────────────────────────────────

def _content_hash(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def _has_specific_numbers(text: str) -> bool:
    return bool(re.search(r'\b\d+[,.]?\d*\s*(%|GB|MB|days?|hours?|minutes?|requests?|seats?|users?)\b', text, re.IGNORECASE))


def _has_structured_answer(text: str) -> bool:
    return len(text) > 200 and ('"answer"' in text or '"citations"' in text or any(w in text.lower() for w in ["first,", "second,", "step 1", "1)", "additionally"]))


def _count_citations(text: str) -> int:
    explicit = len(re.findall(r'(?:source:|doc_id|citation|\[Source:)', text, re.IGNORECASE))
    doc_ids = len(re.findall(r'\b[a-z]+-\d{3}\b', text))
    return max(explicit, doc_ids)


def _detect_ambiguity_signals(query: str, output: str) -> dict:
    ambiguous_terms = {
        "retention": ("customer data retention vs employee data retention", ["security", "hr"]),
        "data after someone leaves": ("customer churn vs employee termination", ["security", "hr"]),
        "keep data": ("deletion timeline vs archival policy", ["security", "hr"]),
    }
    for term, (description, expected_cats) in ambiguous_terms.items():
        if term in query.lower():
            output_lower = output.lower()
            cats_covered = sum(1 for cat in expected_cats if cat in output_lower)
            return {"is_ambiguous": True, "description": description, "expected_categories": expected_cats, "categories_covered": cats_covered, "fully_handled": cats_covered >= len(expected_cats)}
    return {"is_ambiguous": False}


def _detect_hallucination(output: str, context: str) -> list:
    hallucination_markers = [
        ("$5,000", "Specific dollar penalty not in source documents"),
        ("per hour of downtime", "Hourly penalty rate not stated in any source"),
        ("10x the downtime cost", "10x multiplier is fabricated"),
        ("penalty of", "Penalty amounts not specified in SLA terms"),
    ]
    return [{"claim": m, "problem": e} for m, e in hallucination_markers if m in output and m not in context]


def _mock_judge(prompt: str, variables: dict) -> dict:
    """Content-aware mock that produces realistic, differentiated scores."""
    prompt_lower = prompt.lower()
    query = str(variables.get("query", ""))
    agent_output = str(variables.get("agent_output", variables.get("agent_input", "")))
    final_answer = str(variables.get("final_answer", variables.get("synthesis_output", agent_output)))
    retrieval_output = str(variables.get("retrieval_output", variables.get("context", "")))
    variation = (_content_hash(query + agent_output) % 5) * 0.1

    # ── INTENT CAPTURE
    if "intent" in prompt_lower and ("understood" in prompt_lower or "correctly" in prompt_lower or "user's intent" in prompt_lower):
        ambiguity = _detect_ambiguity_signals(query, agent_output)
        if ambiguity["is_ambiguous"] and not ambiguity["fully_handled"]:
            return {"score": 2, "reasoning": f"Query is ambiguous ({ambiguity['description']}). The analyst only addressed {ambiguity['categories_covered']} of {len(ambiguity['expected_categories'])} possible interpretations."}
        if ambiguity["is_ambiguous"] and ambiguity["fully_handled"]:
            return {"score": 5, "reasoning": f"Despite the ambiguous query ({ambiguity['description']}), the analyst correctly identified both interpretations."}
        has_terms = "search_terms" in agent_output
        has_category = '"category"' in agent_output and '"null"' not in agent_output
        if has_terms and has_category:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Query has a clear single intent. The analyst correctly identified relevant search terms and applied an appropriate category filter."}
        elif has_terms:
            return {"score": 3, "reasoning": "Search terms extracted but no category filter applied, which may reduce retrieval precision."}
        return {"score": 2, "reasoning": "Minimal query analysis. Neither structured search terms nor category filtering detected."}

    # ── EXECUTION CORRECTNESS
    if "executed" in prompt_lower or "correct operations" in prompt_lower or "execution" in prompt_lower:
        has_docs = "chunks" in retrieval_output or "doc_id" in retrieval_output
        has_answer = len(final_answer) > 100
        answer_has_numbers = _has_specific_numbers(final_answer)
        if has_docs and has_answer and answer_has_numbers:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Pipeline retrieved relevant documents and produced an answer with specific quantitative details."}
        elif has_docs and has_answer:
            return {"score": 4, "reasoning": "Relevant documents were retrieved and a substantive answer was generated."}
        elif has_docs:
            return {"score": 3, "reasoning": "Documents were retrieved but the synthesized answer is thin or generic."}
        return {"score": 2, "reasoning": "Retrieval returned limited results and the answer lacks supporting evidence."}

    # ── GOAL ACHIEVEMENT
    if "accomplish" in prompt_lower or "goal" in prompt_lower or "act on" in prompt_lower:
        answer_len = len(final_answer)
        has_numbers = _has_specific_numbers(final_answer)
        has_structure = _has_structured_answer(final_answer)
        if answer_len > 300 and has_numbers and has_structure:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Comprehensive answer with specific figures the user can act on."}
        elif answer_len > 200 and (has_numbers or has_structure):
            return {"score": 4, "reasoning": "Answer provides enough information for the user to take action."}
        elif answer_len > 100:
            return {"score": 3, "reasoning": "Answer addresses the query at a surface level but lacks specificity for confident action."}
        return {"score": 2, "reasoning": "Answer is too brief or vague for the user to act on."}

    # ── ACTIONABILITY
    if "actionab" in prompt_lower:
        answer = final_answer
        has_steps = any(w in answer.lower() for w in ["step", "navigate to", "go to", "click", "contact", "submit", "configure"])
        has_numbers = _has_specific_numbers(answer)
        if has_steps and has_numbers and len(answer) > 200:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Answer includes concrete next steps, specific figures, and enough detail for immediate action."}
        elif has_steps or (has_numbers and len(answer) > 150):
            return {"score": 4, "reasoning": "Answer provides actionable guidance with some specific details."}
        elif len(answer) > 100:
            return {"score": 3, "reasoning": "Answer provides general direction but lacks specific steps or figures."}
        return {"score": 2, "reasoning": "Answer is too generic to be actionable."}

    # ── FAITHFULNESS / LOGICAL CONSISTENCY
    if "faithful" in prompt_lower or "logically consistent" in prompt_lower or "supported" in prompt_lower or "claims" in prompt_lower:
        hallucinations = _detect_hallucination(agent_output or final_answer, retrieval_output)
        if hallucinations:
            claims = [h["claim"] for h in hallucinations]
            return {"score": 2, "reasoning": f"Found {len(hallucinations)} unsupported claim(s): {'; '.join(h['problem'] for h in hallucinations)}.", "hallucinations": claims, "unsupported_claims": claims}
        citations_count = _count_citations(final_answer + str(variables.get("citations", "")))
        if citations_count >= 2:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": f"Answer cites {citations_count} sources and all major claims trace back to retrieved documents."}
        elif citations_count >= 1:
            return {"score": 4, "reasoning": "Most claims are supported by sources. Some claims could use additional attribution."}
        return {"score": 3, "reasoning": "Answer appears consistent with sources but lacks explicit citations."}

    # ── CITATION COMPLETENESS
    if "cite" in prompt_lower or "citation" in prompt_lower or "attributed" in prompt_lower:
        citations_str = str(variables.get("citations", ""))
        num_citations = len(re.findall(r'[\w]+-\d+', citations_str))
        if num_citations >= 3:
            return {"score": 5, "reasoning": f"Answer cites {num_citations} sources, providing comprehensive attribution."}
        elif num_citations >= 1:
            return {"score": round(min(5, 3 + variation * 0.5), 1), "reasoning": f"Answer includes {num_citations} citation(s). Some claims lack explicit source attribution."}
        return {"score": 2, "reasoning": "No source citations provided."}

    # ── REFORMULATION QUALITY (PAQS - analysis)
    if "reformulat" in prompt_lower:
        terms_count = len(re.findall(r'"[^"]{3,}"', agent_output))
        if "search_terms" in agent_output and terms_count >= 3:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": f"Reformulation produced {terms_count} specific search terms targeting the core intent."}
        elif "search_terms" in agent_output:
            return {"score": 3, "reasoning": "Search terms generated but are too generic for precise retrieval."}
        return {"score": 2, "reasoning": "No structured search term reformulation detected."}

    # ── FILTER ACCURACY (PAQS - analysis)
    if "filter" in prompt_lower and "category" in prompt_lower:
        ambiguity = _detect_ambiguity_signals(query, agent_output)
        if ambiguity["is_ambiguous"] and not ambiguity["fully_handled"]:
            return {"score": 2, "reasoning": f"Set a single category filter for an ambiguous query ({ambiguity['description']})."}
        if '"category"' in agent_output and '"null"' not in agent_output.replace("None", "null"):
            return {"score": round(min(5, 4 + variation * 0.3), 1), "reasoning": "Appropriate category filter applied, narrowing retrieval to relevant documents."}
        return {"score": 3, "reasoning": "No category filter applied."}

    # ── INFO PRESERVATION (PAQS - synthesis)
    if "preserv" in prompt_lower:
        retrieval_nums = set(re.findall(r'\d+(?:\.\d+)?%?', retrieval_output))
        output_nums = set(re.findall(r'\d+(?:\.\d+)?%?', agent_output + final_answer))
        if retrieval_nums:
            preserved = len(retrieval_nums & output_nums) / len(retrieval_nums)
            if preserved > 0.6:
                return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": f"Synthesis preserved {preserved:.0%} of key data points from sources."}
            elif preserved > 0.3:
                return {"score": 3, "reasoning": f"Synthesis retained {preserved:.0%} of key figures. Some important details dropped."}
            return {"score": 2, "reasoning": f"Most quantitative information from sources was lost. Only {preserved:.0%} preserved."}
        return {"score": round(min(5, 4 + variation * 0.3), 1), "reasoning": "No numeric data to track. Qualitative information appears preserved."}

    # ── COHERENCE
    if "coheren" in prompt_lower:
        length = len(agent_output or final_answer)
        if length > 300:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Output is well-structured with logical flow. No contradictions detected."}
        elif length > 100:
            return {"score": 4, "reasoning": "Output is coherent and readable, though relatively brief."}
        return {"score": 3, "reasoning": "Output is too brief to fully assess coherence."}

    # ── CRITIQUE SPECIFICITY (PAQS - adversarial)
    if "critique" in prompt_lower or ("specific" in prompt_lower and "verif" in prompt_lower):
        issues = re.findall(r'"claim":|"problem":', agent_output)
        if len(issues) >= 2:
            return {"score": 5, "reasoning": f"Verification identified {len(issues)} specific issues with concrete explanations."}
        elif len(issues) >= 1:
            return {"score": 4, "reasoning": "Verification identified at least one specific issue."}
        if "issues" in agent_output and "[]" not in agent_output:
            return {"score": 3, "reasoning": "Verification flagged potential issues but lacks claim-level detail."}
        return {"score": 3, "reasoning": "No specific issues identified."}

    # ── WEAKNESS COVERAGE (PAQS - adversarial)
    if "weakness" in prompt_lower or ("coverage" in prompt_lower and "verif" in prompt_lower):
        checked = sum(1 for t in ["verified", "confidence", "issues", "unsupported"] if t in agent_output.lower())
        if checked >= 3:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": f"Verification checked {checked} distinct quality dimensions."}
        elif checked >= 2:
            return {"score": 4, "reasoning": "Verification covered multiple quality aspects."}
        return {"score": 3, "reasoning": "Verification was superficial."}

    # ── CONSTRUCTIVENESS (PAQS - adversarial)
    if "constructive" in prompt_lower:
        has_issues = "issues" in agent_output and "[]" not in agent_output
        has_confidence = "confidence" in agent_output
        if has_issues and has_confidence:
            return {"score": round(min(5, 4 + variation * 0.5), 1), "reasoning": "Verification provides actionable feedback with issue identification and confidence assessment."}
        elif has_issues or has_confidence:
            return {"score": 3, "reasoning": "Verification provides some useful signals but is missing either specific issues or confidence."}
        return {"score": 2, "reasoning": "Verification output is not constructive."}

    # ── CONTEXT COMPRESSION (handoff)
    if "compress" in prompt_lower or ("context" in prompt_lower and "handoff" in prompt_lower):
        input_len = len(str(variables.get("agent_input", variables.get("source_output", ""))))
        output_len = len(agent_output or str(variables.get("handoff_payload", "")))
        if input_len > 0 and output_len > 0:
            ratio = output_len / max(input_len, 1)
            if 0.3 < ratio < 3.0:
                return {"score": 4, "reasoning": f"Handoff data appropriately sized ({ratio:.1f}x ratio)."}
            return {"score": 3, "reasoning": f"Handoff payload ratio is {ratio:.1f}x, may need optimization."}
        return {"score": 3, "reasoning": "Unable to assess compression ratio."}

    # ── INSTRUCTION FIDELITY (handoff)
    if "instruction" in prompt_lower and "fidelity" in prompt_lower:
        return {"score": round(min(5, 4 + variation * 0.3), 1), "reasoning": "Downstream agent acted upon upstream structured output correctly."}

    # ── DEFAULT
    base = 3 + variation * 0.8
    return {"score": round(min(5, base), 1), "reasoning": "Evaluated based on general output quality signals."}
