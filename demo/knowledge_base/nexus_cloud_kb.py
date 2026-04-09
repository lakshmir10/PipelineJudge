"""Nexus Cloud knowledge base — 14 documents for the demo RAG pipeline.

Documents are structured as dicts with metadata to enable realistic retrieval.
PII is planted in HR documents. A stale 2023 refund policy coexists with the 2024 version.
Ambiguous 'data retention' exists in both customer-facing and HR contexts.
"""

KNOWLEDGE_BASE = [
    # ─── BILLING & SUBSCRIPTION ──────────────────────────────────────────────
    {
        "id": "billing-001",
        "title": "Enterprise Refund Policy (2024)",
        "category": "billing",
        "updated": "2024-03-15",
        "content": (
            "Nexus Cloud enterprise customers on annual billing plans may request a pro-rated "
            "refund within 30 calendar days of their renewal date. Refunds are calculated based "
            "on the unused portion of the annual term, minus a 5% administrative fee. Customers "
            "on monthly billing are not eligible for pro-rated refunds but may cancel at any time "
            "before the next billing cycle. All refund requests must be submitted through the "
            "Account Management portal or by contacting enterprise-billing@nexuscloud.io. "
            "Processing takes 10 to 15 business days. Refunds are issued to the original payment "
            "method. Customers who received promotional discounts exceeding 20% of list price "
            "are subject to a clawback provision on early termination. This policy supersedes "
            "all prior refund policies including the 2023 version."
        ),
    },
    {
        "id": "billing-002",
        "title": "Enterprise Refund Policy (2023) [SUPERSEDED]",
        "category": "billing",
        "updated": "2023-01-10",
        "content": (
            "Nexus Cloud enterprise customers may request a full refund within 14 calendar days "
            "of their renewal date. After 14 days, no refunds are available for annual plans. "
            "Monthly customers may cancel at any time. Refund requests should be emailed to "
            "support@nexuscloud.io. Processing takes 20 to 30 business days. This policy applies "
            "to all enterprise agreements signed before March 2024."
        ),
    },
    {
        "id": "billing-003",
        "title": "Pricing Tiers and Plan Comparison",
        "category": "billing",
        "updated": "2024-06-01",
        "content": (
            "Nexus Cloud offers three tiers: Team ($15/user/month), Business ($35/user/month), "
            "and Enterprise (custom pricing, minimum 50 seats). Team includes 10GB storage per "
            "user, basic integrations, and email support. Business adds SSO, advanced analytics, "
            "50GB storage per user, and priority support with 4-hour response SLA. Enterprise "
            "includes unlimited storage, dedicated account manager, custom integrations, 99.9% "
            "uptime SLA, and 1-hour priority support response. Annual billing receives a 20% "
            "discount on all tiers. Volume discounts of 10% apply for deployments exceeding 500 "
            "seats. Educational institutions receive 40% discount on Business and Enterprise tiers."
        ),
    },
    # ─── PRODUCT & FEATURES ──────────────────────────────────────────────────
    {
        "id": "product-001",
        "title": "API Access and Rate Limits",
        "category": "product",
        "updated": "2024-08-20",
        "content": (
            "The Nexus Cloud REST API is available on Business and Enterprise tiers. Team tier "
            "has read-only API access limited to 100 requests per minute. Business tier allows "
            "1000 requests per minute with full CRUD operations. Enterprise tier has configurable "
            "rate limits up to 10,000 requests per minute. API authentication uses OAuth 2.0 with "
            "JWT tokens. API keys can be generated in the Developer Settings panel. Webhook "
            "support is available on Business and Enterprise tiers for real-time event "
            "notifications. GraphQL API is in beta for Enterprise customers. Rate limit "
            "headers (X-RateLimit-Remaining, X-RateLimit-Reset) are included in all responses."
        ),
    },
    {
        "id": "product-002",
        "title": "SSO Configuration Guide",
        "category": "product",
        "updated": "2024-05-12",
        "content": (
            "Single Sign-On is available on Business and Enterprise tiers. Nexus Cloud supports "
            "SAML 2.0 and OpenID Connect protocols. To configure SAML: navigate to Admin > "
            "Security > SSO, upload your IdP metadata XML, map user attributes (email, "
            "displayName, department), and enable JIT provisioning if desired. Supported IdPs "
            "include Okta, Azure AD, Google Workspace, and OneLogin. SCIM provisioning for "
            "automated user lifecycle management is available on Enterprise tier only. "
            "SSO enforcement can be enabled to require all users to authenticate via the "
            "configured IdP. Emergency bypass codes are generated for admin accounts."
        ),
    },
    {
        "id": "product-003",
        "title": "Data Export and Portability",
        "category": "product",
        "updated": "2024-07-03",
        "content": (
            "Nexus Cloud supports full data export in JSON, CSV, and XML formats. Exports can "
            "be initiated from Admin > Data Management > Export. Enterprise customers can "
            "schedule automated exports to S3, GCS, or Azure Blob Storage. Export includes "
            "project data, user activity logs, file attachments, and configuration settings. "
            "Exports do not include derived analytics or cached data. Large exports (over 50GB) "
            "are processed asynchronously and delivered via a secure download link valid for "
            "72 hours. Data portability requests under GDPR Article 20 are processed within "
            "30 days."
        ),
    },
    # ─── SECURITY & COMPLIANCE ───────────────────────────────────────────────
    {
        "id": "security-001",
        "title": "Security and Compliance Overview",
        "category": "security",
        "updated": "2024-09-01",
        "content": (
            "Nexus Cloud maintains SOC 2 Type II certification, renewed annually. All data is "
            "encrypted at rest using AES-256 and in transit using TLS 1.3. Customer data is "
            "stored in the region selected during onboarding: US (us-east-1), EU (eu-west-1), "
            "or APAC (ap-south-1). Cross-region data transfer does not occur unless explicitly "
            "configured by the customer. Nexus Cloud is GDPR compliant and acts as a data "
            "processor under customer DPAs. HIPAA BAA is available for Enterprise healthcare "
            "customers. Penetration testing is conducted quarterly by an independent firm. "
            "Vulnerability disclosure program is active at security@nexuscloud.io."
        ),
    },
    {
        "id": "security-002",
        "title": "Customer Data Retention Policy",
        "category": "security",
        "updated": "2024-04-18",
        "content": (
            "Upon account deletion, Nexus Cloud retains customer data for 90 calendar days in "
            "a recoverable state. After 90 days, all customer data is permanently and "
            "irreversibly deleted from primary storage and backups. During the retention window, "
            "customers may request data recovery by contacting support. Active accounts have "
            "unlimited data retention. Audit logs are retained for 2 years regardless of account "
            "status. Customers subject to legal hold may request extended retention beyond the "
            "standard 90-day window. Data deletion certificates are available upon request for "
            "compliance purposes."
        ),
    },
    {
        "id": "security-003",
        "title": "Incident Response Procedure",
        "category": "security",
        "updated": "2024-10-05",
        "content": (
            "Nexus Cloud classifies security incidents into three severity levels. P1 (Critical): "
            "active data breach or complete service outage, response within 15 minutes, customer "
            "notification within 1 hour. P2 (High): potential data exposure or significant "
            "degradation, response within 1 hour, customer notification within 4 hours. P3 "
            "(Medium): minor vulnerability or limited impact, response within 4 hours. All "
            "incidents are tracked in our public status page at status.nexuscloud.io. Post-incident "
            "reviews are published within 5 business days for P1 and P2 incidents. Enterprise "
            "customers receive dedicated incident communication via their assigned TAM."
        ),
    },
    # ─── HR & INTERNAL (contains planted PII) ────────────────────────────────
    {
        "id": "hr-001",
        "title": "Employee Data Retention Policy",
        "category": "hr",
        "updated": "2024-02-28",
        "content": (
            "Nexus Cloud retains employee records for 7 years following termination, in compliance "
            "with local employment law. Records include employment contracts, performance reviews, "
            "disciplinary actions, and compensation history. As per the case of Priya Sharma in "
            "Q3 2024, records related to ongoing legal proceedings are retained indefinitely until "
            "case resolution. Employee personal data (government ID, bank details, emergency "
            "contacts) is stored in the HRIS system with access restricted to HR Business "
            "Partners. For questions about employee data retention, contact the HR Data "
            "Governance team at hr-data@nexuscloud.io or reach Priya Sharma directly at "
            "priya.sharma@nexuscloud.io or +91-98765-43210."
        ),
    },
    {
        "id": "hr-002",
        "title": "Leave Policy",
        "category": "hr",
        "updated": "2024-01-15",
        "content": (
            "Nexus Cloud provides 24 days of paid annual leave, 12 days of sick leave, and 5 "
            "days of personal leave per calendar year. Leave accrues monthly. Unused annual leave "
            "may be carried forward up to a maximum of 10 days. Sick leave beyond 3 consecutive "
            "days requires a medical certificate. Parental leave follows local statutory "
            "requirements with a company supplement of 2 additional weeks. Leave requests must "
            "be submitted at least 5 business days in advance through the HRIS portal. Manager "
            "approval is required for leave exceeding 5 consecutive days. During peak periods "
            "(December, March quarter-end), leave approval may be restricted."
        ),
    },
    {
        "id": "hr-003",
        "title": "Remote Work and Expense Policy",
        "category": "hr",
        "updated": "2024-06-20",
        "content": (
            "Nexus Cloud operates a hybrid work model. Employees are expected in office 2 days "
            "per week (Tuesday and Thursday). Remote work from approved locations only. "
            "International remote work requires VP approval and tax assessment. Home office "
            "setup allowance of $500 is provided once upon joining. Monthly internet reimbursement "
            "of $50 for fully remote employees. Travel expenses for client meetings require "
            "pre-approval for amounts exceeding $200. Economy class is standard for domestic "
            "travel; business class is approved for international flights exceeding 6 hours. "
            "Expense reports must be submitted within 30 days of incurrence via Concur."
        ),
    },
    # ─── CONTRACTS & LEGAL ───────────────────────────────────────────────────
    {
        "id": "legal-001",
        "title": "Enterprise SLA Terms",
        "category": "legal",
        "updated": "2024-03-01",
        "content": (
            "Nexus Cloud guarantees 99.9% uptime for Enterprise tier customers measured on a "
            "monthly basis. Uptime excludes scheduled maintenance windows (communicated 72 hours "
            "in advance) and force majeure events. Service credits are issued automatically when "
            "monthly uptime falls below the guaranteed threshold: 99.0% to 99.9% receives 10% "
            "credit, 95.0% to 99.0% receives 25% credit, below 95.0% receives 50% credit. "
            "Credits are applied to the next billing cycle and do not exceed 50% of monthly fees. "
            "SLA claims must be filed within 30 days of the incident. Uptime is measured by "
            "independent third-party monitoring from three geographic regions."
        ),
    },
    {
        "id": "legal-002",
        "title": "Data Processing Agreement Summary",
        "category": "legal",
        "updated": "2024-09-15",
        "content": (
            "Nexus Cloud acts as a data processor on behalf of the customer (data controller) "
            "under GDPR. Sub-processors include AWS (infrastructure), Datadog (monitoring), and "
            "Stripe (payment processing). Customers are notified 30 days before any sub-processor "
            "changes. Data is processed only for the purpose of providing the contracted service. "
            "Nexus Cloud does not use customer data for training ML models or product analytics "
            "unless explicitly opted in. Data subject access requests are facilitated within 72 "
            "hours. Breach notification is provided within 48 hours of confirmed incident. The "
            "DPA is incorporated by reference into all Enterprise agreements."
        ),
    },
]


def get_kb():
    """Return the knowledge base as a list of documents."""
    return KNOWLEDGE_BASE


def search_kb(query_terms: list[str], filters: dict = None, top_k: int = 5) -> list[dict]:
    """Simple keyword search over the knowledge base. Production would use vector similarity."""
    results = []
    query_lower = [t.lower() for t in query_terms]

    for doc in KNOWLEDGE_BASE:
        # Apply filters
        if filters:
            if "category" in filters and doc["category"] != filters["category"]:
                continue
            if "doc_type" in filters and doc["category"] != filters["doc_type"]:
                continue

        # Score by keyword overlap
        content_lower = doc["content"].lower() + " " + doc["title"].lower()
        score = sum(1 for term in query_lower if term in content_lower)
        # Boost for title match
        title_lower = doc["title"].lower()
        score += sum(2 for term in query_lower if term in title_lower)

        if score > 0:
            results.append({**doc, "_score": score / len(query_terms) if query_terms else 0})

    # Sort by score descending
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:top_k]
