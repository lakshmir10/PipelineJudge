"""Programmatic judges — deterministic evaluation functions.

These run without LLM calls: PII scanning, entity preservation,
audit trail checks, retrieval quality metrics.
"""

import re
import json
from typing import Any


# ─── PII DETECTION ───────────────────────────────────────────────────────────────

# Regex patterns for PII
PII_PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "PHONE": r'[\+]\d[\d\s\-\(\)]{8,15}\d',  # must start with + to avoid date false positives
    "GOV_ID": r'\b\d{3}-\d{2}-\d{4}\b',  # SSN only
    "CREDIT_CARD": r'\b(?:\d{4}[-\s]){3}\d{4}\b',
}

# Words that look like person names but aren't
NAME_BLOCKLIST = {
    "nexus cloud", "leave policy", "remote work", "expense policy", "employee data",
    "retention policy", "data governance", "business partners", "enterprise refund",
    "source authority", "incident response", "security overview", "processing agreement",
    "account management", "rate limit",
}

# Business/team email patterns — not personal PII
BUSINESS_EMAIL_PATTERNS = [
    r'.*-billing@', r'.*support@', r'.*-data@', r'.*security@', r'.*info@',
    r'.*admin@', r'.*team@', r'.*noreply@', r'.*help@',
]


def _extract_text(obj: Any) -> str:
    """Recursively extract all text content from a nested dict/list."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(_extract_text(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(_extract_text(v) for v in obj)
    return str(obj) if obj is not None else ""


def _find_pii(text: str) -> list[dict]:
    """Find PII instances in text using regex patterns and name detection."""
    findings = []

    for pii_type, pattern in PII_PATTERNS.items():
        for match in re.finditer(pattern, text):
            entity = match.group()
            # Filter out false positives
            if pii_type == "PHONE" and len(entity.replace("-", "").replace(" ", "").replace("+", "")) < 8:
                continue
            # Skip business/team emails
            if pii_type == "EMAIL" and any(re.match(bp, entity) for bp in BUSINESS_EMAIL_PATTERNS):
                continue
            findings.append({
                "entity": entity,
                "type": pii_type,
                "position": match.start(),
            })

    # Name detection — look for patterns like "Name Surname" near PII context words
    name_contexts = ["contact", "reach", "case of", "employee", "assigned to", "manager", "report to"]
    name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
    for match in re.finditer(name_pattern, text):
        name = match.group()
        # Filter out common compound nouns that aren't names
        if name.lower() in NAME_BLOCKLIST:
            continue
        # Check if near a PII context
        start = max(0, match.start() - 100)
        surrounding = text[start:match.start() + len(name) + 100].lower()
        if any(ctx in surrounding for ctx in name_contexts):
            findings.append({
                "entity": name,
                "type": "PERSON",
                "position": match.start(),
            })

    return findings


def pii_scan(agents: list[dict], handoffs: list[dict], **kwargs) -> dict:
    """Scan all pipeline stages for PII. Returns score and findings."""
    all_findings = []

    # Scan each agent's input and output
    for agent in agents:
        for field_name in ["input_payload", "output_payload"]:
            text = _extract_text(agent.get(field_name, {}))
            findings = _find_pii(text)
            for f in findings:
                f["location"] = f"{agent['agent_name']} → {field_name.replace('_payload', '')}"
                f["severity"] = "high" if f["type"] in ("PERSON", "GOV_ID", "CREDIT_CARD") else "medium"
            all_findings.extend(findings)

    # Scan handoff payloads
    for handoff in handoffs:
        text = _extract_text(handoff.get("payload", {}))
        findings = _find_pii(text)
        source_name = handoff.get("_source_name", "?")
        target_name = handoff.get("_target_name", "?")
        for f in findings:
            f["location"] = f"{source_name} → {target_name} handoff"
            f["severity"] = "high" if f["type"] in ("PERSON", "GOV_ID", "CREDIT_CARD") else "medium"
        all_findings.extend(findings)

    # Deduplicate by entity
    seen = set()
    unique_findings = []
    for f in all_findings:
        key = (f["entity"], f["location"])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    # Score: 100 if no PII, decreasing with findings weighted by severity
    severity_weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
    penalty = sum(severity_weights.get(f["severity"], 5) for f in unique_findings)
    score = max(0, 100 - penalty)

    return {
        "score": score,
        "findings": unique_findings,
        "reasoning": f"Found {len(unique_findings)} PII instances across pipeline stages.",
    }


def pii_channel_scan(agents: list[dict], handoffs: list[dict], **kwargs) -> dict:
    """Check which pipeline channels contain PII (more granular than pii_scan)."""
    channels_with_pii = set()
    total_channels = 0

    for agent in agents:
        for field in ["input_payload", "output_payload"]:
            total_channels += 1
            text = _extract_text(agent.get(field, {}))
            if _find_pii(text):
                channels_with_pii.add(f"{agent['agent_name']}.{field}")

    for i, handoff in enumerate(handoffs):
        total_channels += 1
        text = _extract_text(handoff.get("payload", {}))
        if _find_pii(text):
            channels_with_pii.add(f"handoff_{i}")

    clean_ratio = (total_channels - len(channels_with_pii)) / max(total_channels, 1)
    score = round(clean_ratio * 100)

    return {
        "score": score,
        "reasoning": f"{len(channels_with_pii)} of {total_channels} channels contain PII.",
        "channels_with_pii": list(channels_with_pii),
    }


# ─── AUDIT TRAIL ─────────────────────────────────────────────────────────────────

def input_traceability(agents: list[dict], **kwargs) -> dict:
    """Check that every agent has non-empty input_payload."""
    total = len(agents)
    passed = sum(1 for a in agents if a.get("input_payload") and len(str(a["input_payload"])) > 2)
    return {
        "score": round((passed / max(total, 1)) * 100),
        "passed": passed,
        "total": total,
        "reasoning": f"{passed}/{total} agents have non-empty input payloads.",
    }


def model_version_check(agents: list[dict], **kwargs) -> dict:
    """Check that model_id is specific (not just a family name)."""
    total = len(agents)
    passed = 0
    for a in agents:
        mid = a.get("model_id") or ""
        # Must contain a version indicator (date, version number, or specific identifier)
        # Generic names like "claude" or "gpt-4" fail; "claude-sonnet-4-20250514" passes
        if mid and (any(c.isdigit() for c in mid.split("-")[-1]) or len(mid) > 15):
            passed += 1
    return {
        "score": round((passed / max(total, 1)) * 100),
        "passed": passed,
        "total": total,
        "reasoning": f"{passed}/{total} agents have version-specific model IDs.",
    }


def prompt_hash_check(agents: list[dict], **kwargs) -> dict:
    """Check that prompt_template_hash is present for LLM-based agents."""
    llm_agents = [a for a in agents if a.get("model_id") and "embedding" not in (a.get("model_id") or "").lower()
                  and "search" not in (a.get("model_id") or "").lower()
                  and "mock" != (a.get("model_id") or "")]
    if not llm_agents:
        return {"score": 100, "passed": 0, "total": 0, "reasoning": "No LLM agents requiring prompt hash."}

    passed = sum(1 for a in llm_agents if a.get("prompt_template_hash"))
    total = len(llm_agents)
    return {
        "score": round((passed / max(total, 1)) * 100),
        "passed": passed,
        "total": total,
        "reasoning": f"{passed}/{total} LLM agents have prompt template hashes.",
    }


def timestamp_check(agents: list[dict], **kwargs) -> dict:
    """Check timestamp presence and monotonicity."""
    total = len(agents)
    has_timestamps = sum(1 for a in agents if a.get("started_at") or a.get("completed_at"))

    # Check ordering
    order_ok = True
    for i in range(1, len(agents)):
        curr = agents[i].get("started_at") or agents[i].get("completed_at")
        prev = agents[i-1].get("completed_at") or agents[i-1].get("started_at")
        if curr and prev and str(curr) < str(prev):
            order_ok = False

    score = round((has_timestamps / max(total, 1)) * 100)
    if not order_ok:
        score = max(0, score - 20)

    return {
        "score": score,
        "passed": has_timestamps,
        "total": total,
        "reasoning": f"{has_timestamps}/{total} agents have timestamps. Order {'valid' if order_ok else 'INVALID'}.",
    }


# ─── RETRIEVAL METRICS ───────────────────────────────────────────────────────────

def retrieval_relevance(agents: list[dict], query_data: dict = None, **kwargs) -> dict:
    """Score retrieval relevance based on whether retrieved docs match expected sources."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    if not chunks:
        return {"score": 0, "reasoning": "No documents retrieved."}

    # Score based on relevance scores if available
    scores = [c.get("relevance_score", c.get("_score", 0.5)) for c in chunks]
    avg_score = sum(scores) / len(scores) if scores else 0
    normalized = min(100, round(avg_score * 100))

    return {
        "score": normalized,
        "reasoning": f"Average relevance score: {avg_score:.2f} across {len(chunks)} chunks.",
    }


def ranking_precision(agents: list[dict], **kwargs) -> dict:
    """Check if the highest-scoring documents are ranked first."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    if len(chunks) < 2:
        return {"score": 75, "reasoning": "Too few chunks to evaluate ranking."}

    # Check if scores are monotonically decreasing (properly ranked)
    scores = [c.get("relevance_score", c.get("_score", 0)) for c in chunks]
    inversions = sum(1 for i in range(len(scores)-1) if scores[i] < scores[i+1])
    max_inversions = len(scores) - 1
    precision = 1.0 - (inversions / max(max_inversions, 1))

    # Check for stale documents ranked above newer ones on same topic
    stale_penalty = 0
    for i, chunk in enumerate(chunks):
        if "SUPERSEDED" in chunk.get("title", "").upper() or "2023" in chunk.get("updated", ""):
            if i < len(chunks) - 1:  # stale doc is not at the bottom
                stale_penalty = 15

    score = max(0, round(precision * 100) - stale_penalty)
    return {
        "score": score,
        "reasoning": f"Ranking precision: {precision:.2f}, inversions: {inversions}, stale penalty: {stale_penalty}.",
    }


def source_authority(agents: list[dict], **kwargs) -> dict:
    """Evaluate authority of retrieved sources based on metadata."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    if not chunks:
        return {"score": 0, "reasoning": "No documents retrieved."}

    # Authority heuristics: official docs > general articles
    high_authority_cats = {"security", "legal", "billing"}
    auth_scores = []
    for c in chunks:
        cat = c.get("category", "")
        if cat in high_authority_cats:
            auth_scores.append(90)
        elif cat in {"product"}:
            auth_scores.append(80)
        elif cat in {"hr"}:
            auth_scores.append(70)
        else:
            auth_scores.append(50)

    avg = sum(auth_scores) / len(auth_scores) if auth_scores else 50
    return {"score": round(avg), "reasoning": f"Average source authority: {avg:.0f}."}


def source_recency(agents: list[dict], **kwargs) -> dict:
    """Evaluate recency of retrieved sources."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    if not chunks:
        return {"score": 0, "reasoning": "No documents retrieved."}

    recency_scores = []
    for c in chunks:
        updated = c.get("updated", "")
        if "2024" in updated or "2025" in updated or "2026" in updated:
            recency_scores.append(100)
        elif "2023" in updated:
            recency_scores.append(40)  # notably stale
        else:
            recency_scores.append(60)

        # Extra penalty if superseded doc
        if "SUPERSEDED" in c.get("title", "").upper():
            recency_scores[-1] = min(recency_scores[-1], 20)

    avg = sum(recency_scores) / len(recency_scores) if recency_scores else 50
    return {"score": round(avg), "reasoning": f"Average recency: {avg:.0f}. {len([s for s in recency_scores if s < 50])} stale sources."}


def retrieval_coverage(agents: list[dict], **kwargs) -> dict:
    """Evaluate whether retrieval found docs from relevant categories."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    analyst = next((a for a in agents if a.get("agent_type") == "analysis"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    categories_found = set(c.get("category", "") for c in chunks)

    # If analyst flagged ambiguity, we expect multiple categories
    is_ambiguous = False
    if analyst:
        analyst_out = analyst.get("output_payload", {})
        is_ambiguous = analyst_out.get("is_ambiguous", False)

    if is_ambiguous and len(categories_found) < 2:
        return {"score": 40, "reasoning": f"Ambiguous query but only retrieved from {categories_found}. Missing alternative interpretation."}

    score = min(100, 60 + len(categories_found) * 15)
    return {"score": score, "reasoning": f"Retrieved from {len(categories_found)} categories: {categories_found}."}


def retrieval_diversity(agents: list[dict], **kwargs) -> dict:
    """Check diversity of retrieved documents."""
    retrieval = next((a for a in agents if a.get("agent_type") == "retrieval"), None)
    if not retrieval:
        return {"score": 50, "reasoning": "No retrieval agent found."}

    chunks = retrieval.get("output_payload", {}).get("chunks", [])
    if len(chunks) < 2:
        return {"score": 60, "reasoning": "Too few chunks to evaluate diversity."}

    doc_ids = [c.get("doc_id", "") for c in chunks]
    unique_docs = len(set(doc_ids))
    categories = set(c.get("category", "") for c in chunks)

    diversity = (unique_docs / len(doc_ids)) * 0.6 + (len(categories) / max(len(doc_ids), 1)) * 0.4
    score = min(100, round(diversity * 100))
    return {"score": score, "reasoning": f"{unique_docs} unique docs, {len(categories)} categories from {len(chunks)} chunks."}


# ─── HANDOFF METRICS ─────────────────────────────────────────────────────────────

def entity_preservation(source_output: dict, handoff_payload: dict, target_input: dict, **kwargs) -> dict:
    """Check what percentage of key entities from source survive into the handoff/target."""
    source_text = _extract_text(source_output)
    handoff_text = _extract_text(handoff_payload)
    target_text = _extract_text(target_input)

    # Extract key entities (numbers, proper nouns, specific terms)
    number_pattern = r'\b\d+[\.\d]*%?\b'
    source_numbers = set(re.findall(number_pattern, source_text))
    target_numbers = set(re.findall(number_pattern, handoff_text + " " + target_text))

    if not source_numbers:
        return {"score": 80, "reasoning": "No numeric entities to track."}

    preserved = source_numbers & target_numbers
    ratio = len(preserved) / len(source_numbers) if source_numbers else 1.0
    score = round(ratio * 100)

    return {
        "score": score,
        "reasoning": f"{len(preserved)}/{len(source_numbers)} numeric entities preserved.",
        "preserved": list(preserved),
        "lost": list(source_numbers - target_numbers),
    }


# ─── REGULATORY RULES ───────────────────────────────────────────────────────────

def check_regulatory_rules(rules: list[dict], query: str, final_answer: str,
                           pii_findings: list[dict], citations: list = None) -> dict:
    """Check compliance with configured regulatory rules."""
    results = []
    query_lower = query.lower()
    answer_lower = final_answer.lower()

    for rule in rules:
        trigger_terms = rule.get("trigger", [])
        # Check if rule is triggered
        triggered = len(trigger_terms) == 0  # empty trigger = always
        for term in trigger_terms:
            if term in query_lower or term in answer_lower:
                triggered = True
                break

        satisfied = True
        if triggered:
            check_type = rule.get("check_type", "has_content")

            if check_type == "pii_absent":
                # Rule passes if no PII in the final answer
                person_pii = [f for f in pii_findings if f.get("type") == "PERSON"
                              and "output" in f.get("location", "").lower()]
                satisfied = len(person_pii) == 0

            elif check_type == "has_citations":
                satisfied = bool(citations and len(citations) > 0)

            else:
                # Default: check that required content keywords appear in answer
                required = rule.get("required_content", [])
                if required:
                    satisfied = any(kw.lower() in answer_lower for kw in required)

        results.append({
            "rule": rule["name"],
            "triggered": triggered,
            "satisfied": satisfied,
            "severity": rule.get("severity", "warning"),
        })

    # Score
    triggered_rules = [r for r in results if r["triggered"]]
    if not triggered_rules:
        score = 100
    else:
        satisfied_count = sum(1 for r in triggered_rules if r["satisfied"])
        # Weight by severity
        weighted_total = 0
        weighted_pass = 0
        severity_w = {"critical": 3, "high": 2, "warning": 1, "info": 0.5}
        for r in triggered_rules:
            w = severity_w.get(r["severity"], 1)
            weighted_total += w
            if r["satisfied"]:
                weighted_pass += w
        score = round((weighted_pass / max(weighted_total, 1)) * 100)

    return {
        "score": score,
        "results": results,
        "reasoning": f"{sum(1 for r in triggered_rules if r['satisfied'])}/{len(triggered_rules)} triggered rules satisfied.",
    }


# ─── REGISTRY ────────────────────────────────────────────────────────────────────

JUDGE_REGISTRY = {
    "pii_scan": pii_scan,
    "pii_channel_scan": pii_channel_scan,
    "input_traceability": input_traceability,
    "model_version_check": model_version_check,
    "prompt_hash_check": prompt_hash_check,
    "timestamp_check": timestamp_check,
    "retrieval_relevance": retrieval_relevance,
    "ranking_precision": ranking_precision,
    "source_authority": source_authority,
    "source_recency": source_recency,
    "retrieval_coverage": retrieval_coverage,
    "retrieval_diversity": retrieval_diversity,
    "entity_preservation": entity_preservation,
    "check_regulatory_rules": check_regulatory_rules,
}
