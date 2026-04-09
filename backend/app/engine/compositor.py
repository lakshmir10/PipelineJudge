"""Score Compositor — weighted composite calculation and compliance floor rule.

Takes individual dimension scores, computes layer scores and overall system score.
Applies the compliance floor rule: if compliance < threshold, cap overall score.
"""


def compute_layer_score(dimension_scores: dict[str, float], dimension_weights: dict[str, float]) -> float:
    """Compute weighted average of dimension scores within a layer."""
    total_weight = sum(dimension_weights.get(code, 1.0) for code in dimension_scores)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(
        dimension_scores[code] * dimension_weights.get(code, 1.0)
        for code in dimension_scores
    )
    return round(weighted_sum / total_weight, 1)


def compute_system_score(
    layer_scores: dict[str, float],
    layer_weights: dict[str, float],
    compliance_floor_threshold: float = 70.0,
    compliance_floor_cap: float = 50.0,
) -> dict:
    """Compute overall system score with compliance floor rule.

    Args:
        layer_scores: {"product": 73, "pipeline": 64, "compliance": 82}
        layer_weights: {"product": 0.35, "pipeline": 0.40, "compliance": 0.25}
        compliance_floor_threshold: If compliance is below this, cap overall score
        compliance_floor_cap: Max overall score when compliance floor is active

    Returns:
        {"overall": float, "compliance_capped": bool}
    """
    total_weight = sum(layer_weights.values())
    if total_weight == 0:
        return {"overall": 0, "compliance_capped": False}

    weighted_sum = sum(
        layer_scores.get(layer, 0) * weight
        for layer, weight in layer_weights.items()
    )
    overall = round(weighted_sum / total_weight, 1)

    # Compliance floor rule
    compliance_score = layer_scores.get("compliance", 100)
    compliance_capped = False

    if compliance_score < compliance_floor_threshold:
        overall = min(overall, compliance_floor_cap)
        compliance_capped = True

    return {
        "overall": overall,
        "compliance_capped": compliance_capped,
    }


def normalize_llm_score(raw_score: float, min_val: float = 1, max_val: float = 5) -> float:
    """Normalize a 1-5 LLM judge score to 0-100."""
    if raw_score <= min_val:
        return 0.0
    if raw_score >= max_val:
        return 100.0
    return round(((raw_score - min_val) / (max_val - min_val)) * 100, 1)


def compute_subdimension_composite(sub_scores: dict[str, float], sub_weights: dict[str, float]) -> float:
    """Compute weighted composite of subdimension scores."""
    total_weight = sum(sub_weights.get(name, 1.0) for name in sub_scores)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(
        sub_scores[name] * sub_weights.get(name, 1.0)
        for name in sub_scores
    )
    return round(weighted_sum / total_weight, 1)
