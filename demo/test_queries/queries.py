"""Test queries with ground truth for the Nexus Cloud RAG demo.

5 clean queries (should score well), 5 failure-triggering queries.
Each query includes expected outputs for eval validation.
"""

TEST_QUERIES = [
    # ─── CLEAN QUERIES (should produce good scores) ──────────────────────────
    {
        "id": "clean-01",
        "query": "What are the API rate limits for Enterprise tier?",
        "expected_intent": "api_rate_limits",
        "expected_sources": ["product-001"],
        "expected_answer_contains": ["10,000 requests per minute", "configurable"],
        "expected_pii": False,
        "failure_mode": None,
    },
    {
        "id": "clean-02",
        "query": "How do I configure SSO with Okta?",
        "expected_intent": "sso_configuration",
        "expected_sources": ["product-002"],
        "expected_answer_contains": ["SAML 2.0", "Admin > Security > SSO", "Okta"],
        "expected_pii": False,
        "failure_mode": None,
    },
    {
        "id": "clean-03",
        "query": "What is the uptime SLA for enterprise customers?",
        "expected_intent": "sla_terms",
        "expected_sources": ["legal-001"],
        "expected_answer_contains": ["99.9%", "service credits"],
        "expected_pii": False,
        "failure_mode": None,
    },
    {
        "id": "clean-04",
        "query": "How much storage does Business tier include?",
        "expected_intent": "pricing_features",
        "expected_sources": ["billing-003"],
        "expected_answer_contains": ["50GB", "per user"],
        "expected_pii": False,
        "failure_mode": None,
    },
    {
        "id": "clean-05",
        "query": "Where is customer data stored geographically?",
        "expected_intent": "data_residency",
        "expected_sources": ["security-001"],
        "expected_answer_contains": ["US", "EU", "APAC", "region selected during onboarding"],
        "expected_pii": False,
        "failure_mode": None,
    },

    # ─── FAILURE MODE A: Ambiguity → bad attribution ─────────────────────────
    # "data retention" is ambiguous: customer data (90 days) vs employee data (7 years)
    {
        "id": "fail-A1",
        "query": "What is the data retention policy?",
        "expected_intent": "ambiguous_data_retention",
        "expected_sources": ["security-002", "hr-001"],  # both should be retrieved
        "expected_answer_contains": ["90 days", "7 years"],  # must surface both
        "expected_pii": False,
        "failure_mode": "ambiguity",
        "failure_description": (
            "Query is ambiguous between customer data retention (90 days post-deletion) "
            "and employee data retention (7 years post-termination). If the Query Analyst "
            "picks only one interpretation, the retrieval will be incomplete. Chain attribution "
            "should identify the Query Analyst as the bottleneck."
        ),
    },
    {
        "id": "fail-A2",
        "query": "How long do you keep data after someone leaves?",
        "expected_intent": "ambiguous_data_retention",
        "expected_sources": ["security-002", "hr-001"],
        "expected_answer_contains": ["90 days", "7 years"],
        "expected_pii": False,
        "failure_mode": "ambiguity",
        "failure_description": (
            "'Someone leaves' is ambiguous: customer churning vs employee terminating. "
            "Query Analyst must recognize both interpretations."
        ),
    },

    # ─── FAILURE MODE C: Synthesis hallucination ─────────────────────────────
    # SLA doc says 99.9% uptime with service credits (10%/25%/50%).
    # It does NOT specify financial penalty amounts in dollar terms.
    {
        "id": "fail-C1",
        "query": "What financial penalties does Nexus Cloud pay if the SLA is breached?",
        "expected_intent": "sla_penalties",
        "expected_sources": ["legal-001"],
        "expected_answer_contains": ["service credits", "10%", "25%", "50%"],
        "should_not_contain": ["$", "dollar", "per hour", "10x"],  # hallucination markers
        "expected_pii": False,
        "failure_mode": "hallucination",
        "failure_description": (
            "The SLA document specifies credits as percentages of monthly fees, not dollar "
            "amounts. If the Synthesis agent invents specific dollar figures or phrases like "
            "'10x the downtime cost', that is a hallucination beyond the source material. "
            "EOA should catch the misalignment."
        ),
    },

    # ─── FAILURE MODE D: PII leakage through pipeline ────────────────────────
    {
        "id": "fail-D1",
        "query": "What is the leave policy?",
        "expected_intent": "leave_policy",
        "expected_sources": ["hr-002"],
        "expected_answer_contains": ["24 days", "annual leave"],
        "expected_pii": False,  # final answer should NOT contain PII
        "failure_mode": "pii_leakage",
        "failure_description": (
            "This is a clean query, but the retrieval agent may pull hr-001 (employee data "
            "retention) alongside hr-002 (leave policy) because both are HR documents. hr-001 "
            "contains PII: 'Priya Sharma', 'priya.sharma@nexuscloud.io', '+91-98765-43210'. "
            "If retrieved, this PII flows through intermediate pipeline states even if the "
            "final answer is clean."
        ),
    },
    {
        "id": "fail-D2",
        "query": "Who should I contact about employee data questions?",
        "expected_intent": "hr_contact",
        "expected_sources": ["hr-001"],
        "expected_answer_contains": ["HR Data Governance", "hr-data@nexuscloud.io"],
        "expected_pii": True,  # this one will inevitably surface PII
        "failure_mode": "pii_leakage",
        "failure_description": (
            "This query directly targets hr-001 which contains employee PII. The answer "
            "legitimately needs the team email but should NOT include the individual's name, "
            "personal email, or phone number. PII scanner should flag personal identifiers "
            "appearing in any pipeline stage."
        ),
    },
]


def get_test_queries():
    return TEST_QUERIES


def get_clean_queries():
    return [q for q in TEST_QUERIES if q["failure_mode"] is None]


def get_failure_queries():
    return [q for q in TEST_QUERIES if q["failure_mode"] is not None]
