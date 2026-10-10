# L8.5: The security perimeter — API gateway, mTLS, secrets, and the audit log

> **FDE framing in one line:** the security perimeter is the trust boundary. The agent runs inside; the customer and the public internet are outside. The 5 layers — API gateway, mTLS, secrets, audit log, identity — turn a working agent into a product the customer's CISO will approve. The FDE who can name all 5 layers is the FDE who can land the regulated-industry engagement.

## The 3 things you'll learn

1. The 5 security layers: API gateway (rate limit, auth, audit), mTLS (encrypt in transit), secrets management (Vault, AWS Secrets Manager), audit log (who did what when), and identity (OAuth, JWT, mTLS, OIDC). Each layer protects a different attack surface.
2. The 3 compliance regimes: SOC 2 (US service organizations), HIPAA (US healthcare), PCI DSS (payment card industry). Each requires specific controls; the FDE maps the customer's requirements to the 5 layers.
3. The "zero trust" pattern: every request is authenticated, authorized, and audited. The agent trusts no one — not the customer's network, not the customer's employees, not the FDE. The pattern is the only one that survives a CISO review.

## Concept

The security perimeter is the trust boundary between the agent (inside) and the world (outside). The FDE's job is to design the perimeter so that (1) only authorized callers can reach the agent, (2) the data is encrypted in transit and at rest, (3) the secrets are managed, rotated, and never logged, (4) every action is auditable, (5) the customer's compliance regime (SOC 2, HIPAA, PCI) is satisfied. **The wrong choice is to ship without a perimeter (the agent is a public API with no auth). The right choice is the 5 layers + zero trust + the compliance map.**

The 5 security layers:

1. **API gateway.** The front door. The gateway enforces: rate limit (per-caller, per-tenant, per-IP), authentication (API key, OAuth, JWT), authorization (which endpoints the caller can invoke), and audit logging (every request is logged with the caller's identity). The right tool: Kong, AWS API Gateway, Azure API Management, Google Cloud Endpoints.
2. **mTLS (mutual TLS).** Encrypt in transit. Both the caller and the agent authenticate each other with certificates. The right choice for service-to-service communication; the right choice for compliance; the right choice for zero trust. The wrong choice for browser-based clients (browsers don't have certificates).
3. **Secrets management.** The vault. Secrets (API keys, DB passwords, OAuth tokens) are stored encrypted, rotated automatically, and never logged. The right tool: HashiCorp Vault, AWS Secrets Manager, Google Secret Manager, Azure Key Vault. The wrong choice: hardcoded secrets in environment variables, committed to git, or pasted in Slack.
4. **Audit log.** The record. Every action is logged: who called, when, what they requested, what the agent did, what the result was. The audit log is immutable; the audit log is queryable; the audit log is the artifact that answers "what happened" during a security review. The right tool: a dedicated log stream (CloudWatch, Loki) with retention ≥ 1 year.
5. **Identity.** The authentication mechanism. The agent knows who the caller is: API key (simple), OAuth 2.0 (delegated, customer-controlled), JWT (self-contained), mTLS (certificate-based), OIDC (federated identity). The right choice depends on the customer's identity provider and the compliance regime.

The 3 compliance regimes:

1. **SOC 2 (US service organizations).** The customer must demonstrate: access control, change management, monitoring, incident response. The 5 security layers cover SOC 2. The audit log is the key artifact.
2. **HIPAA (US healthcare).** The customer must demonstrate: PHI protection, encryption in transit and at rest, access control, audit logging. The 5 layers cover HIPAA + the additional requirement of "minimum necessary" access (the agent only sees the PHI it needs).
3. **PCI DSS (payment card industry).** The customer must demonstrate: cardholder data protection, network segmentation, encryption, access control, audit logging. The 5 layers cover PCI + the additional requirement of network segmentation (the agent runs in a separate VPC).

The "zero trust" pattern is the recognition that the agent trusts no one — not the customer's network, not the customer's employees, not the FDE. Every request is authenticated (who is the caller?), authorized (what can they do?), and audited (what did they do?). The pattern is the only one that survives a CISO review. **The wrong choice is "we trust our network" (the network is the perimeter; once you're inside, you can do anything). The right choice is zero trust: every request is verified.**

## The pattern

The 5 security layers (the FDE's reference):

```python
SECURITY_LAYERS = {
    "L1_api_gateway": {
        "purpose": "Rate limit, authenticate, authorize, audit",
        "tools": ["Kong (open-source)", "AWS API Gateway (managed)", "Azure API Management (managed)"],
        "configuration": "rate_limit: 100/min per API key; auth: OAuth 2.0; audit: enabled",
        "best_for": "Every agent; the front door",
    },
    "L2_mtls": {
        "purpose": "Encrypt in transit; authenticate both parties",
        "tools": ["Linkerd (service mesh)", "Istio (service mesh)", "Cert-manager (certificate management)"],
        "configuration": "All inter-service communication uses TLS; certs rotated every 90 days",
        "best_for": "Service-to-service; compliance; zero trust",
    },
    "L3_secrets": {
        "purpose": "Store, rotate, and audit secrets",
        "tools": ["HashiCorp Vault (open-source)", "AWS Secrets Manager (managed)", "Google Secret Manager (managed)"],
        "configuration": "Secrets stored encrypted; rotated every 30 days; access logged",
        "best_for": "API keys, DB passwords, OAuth tokens",
    },
    "L4_audit_log": {
        "purpose": "Record every action; immutable; queryable",
        "tools": ["CloudWatch Logs (managed)", "Loki (open-source)", "Splunk (managed, enterprise)"],
        "configuration": "Every request logged with: timestamp, request_id, caller, action, result; retention 1 year",
        "best_for": "Compliance, incident response, debugging",
    },
    "L5_identity": {
        "purpose": "Who is the caller?",
        "tools": ["OAuth 2.0 (Auth0, Cognito, Okta)", "JWT (self-contained)", "API key (simple)", "mTLS (service-to-service)"],
        "configuration": "OAuth with customer-specific scopes; JWT for self-contained; mTLS for service-to-service",
        "best_for": "Customer identity, federated auth, machine-to-machine",
    },
}
```

The 3 compliance regimes mapped to the 5 layers:

```python
COMPLIANCE_MAP = {
    "soc2": {
        "requirements": ["access control", "change management", "monitoring", "incident response"],
        "covered_by_layers": ["L1_api_gateway (access control + audit)", "L3_secrets (change management)", "L4_audit_log (monitoring)", "L5_identity (incident response: who did what)"],
        "additional_artifacts": ["SOC 2 Type II report (annual audit)", "Change management policy", "Incident response plan", "Access review (quarterly)"],
    },
    "hipaa": {
        "requirements": ["PHI protection", "encryption in transit and at rest", "access control", "audit logging"],
        "covered_by_layers": ["L1_api_gateway (access control)", "L2_mtls (encryption in transit)", "L3_secrets (encryption at rest)", "L4_audit_log (audit logging)"],
        "additional_artifacts": ["BAA (Business Associate Agreement)", "Risk assessment", "Workforce training", "PHI handling policy"],
    },
    "pci_dss": {
        "requirements": ["cardholder data protection", "network segmentation", "encryption", "access control", "audit logging"],
        "covered_by_layers": ["L1_api_gateway (access control)", "L2_mtls (encryption in transit)", "L3_secrets (encryption at rest)", "L4_audit_log (audit logging)"],
        "additional_artifacts": ["Network segmentation (agent in separate VPC)", "PCI DSS AoC (Attestation of Compliance)", "Penetration test (annual)", "Vulnerability scan (quarterly)"],
    },
}
```

The API gateway configuration (the FDE's reference):

```yaml
# Kong API gateway config
services:
  - name: agent
    url: http://agent-service:8000
    routes:
      - name: agent-route
        paths:
          - /v1/agent
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
          policy: local
          limit_by: consumer
      - name: jwt
        config:
          secret_is_base64: false
          claims_to_verify:
            - exp
            - tenant
      - name: oauth2
        config:
          scopes:
            - agent:run
            - agent:admin
      - name: prometheus
        config:
          per_consumer: true
      - name: aws-lambda
        config:
          aws_key: ${secrets.aws_access_key}
          aws_secret: ${secrets.aws_secret_key}
```

The secrets management pattern (Vault):

```python
import hvac

# Initialize Vault client
client = hvac.Client(url="https://vault.atlasmart.internal:8200", token=os.environ["VAULT_TOKEN"])

def get_secret(secret_path: str) -> str:
    """Get a secret from Vault; never log the secret."""
    response = client.secrets.kv.v2.read_secret_version(path=secret_path)
    return response["data"]["data"]["value"]

# Get secrets at startup
OPENAI_API_KEY = get_secret("secret/data/openai/prod")
DATABASE_URL = get_secret("secret/data/postgres/prod")
REDIS_URL = get_secret("secret/data/redis/prod")

# Use the secrets in the agent
agent = SingleAgent(
    model=OpenAIModel(api_key=OPENAI_API_KEY),
    database_url=DATABASE_URL,
    redis_url=REDIS_URL,
)

# Audit log: every secret access is logged
# Vault's audit log: "user prem read secret/data/openai/prod at 2026-10-10T10:23:45Z"
```

The audit log (the CISO's view):

```json
{
  "timestamp": "2026-10-10T10:23:45.123Z",
  "request_id": "req-abc123",
  "tenant": "acme",
  "caller": "user-alice@acme.com",
  "caller_ip": "203.0.113.42",
  "action": "POST /v1/agent",
  "request_body": {"email": "alice@acme.com"},
  "response_status": 200,
  "response_body_truncated": "...",
  "agent_actions": [
    {"step": 1, "tool": "clearbit_lookup", "args": {"email": "alice@acme.com"}},
    {"step": 2, "tool": "lane_check", "args": {"origin": "SG", "destination": "VN"}}
  ],
  "agent_cost_usd": 0.0012,
  "agent_latency_ms": 2340,
  "auth_method": "oauth2",
  "auth_scopes": ["agent:run"],
  "user_agent": "curl/8.0.0",
  "trace_id": "trace-abc123"
}
```

The "zero trust" implementation:

```python
def agent_request_handler(request):
    """Every request is authenticated, authorized, and audited."""
    # 1. Authenticate: who is the caller?
    caller = authenticate(request)  # OAuth, JWT, mTLS, API key
    if not caller:
        audit_log("unauthorized", request=request)
        return {"status": 401, "error": "unauthorized"}

    # 2. Authorize: what can they do?
    if not authorized(caller, action=request.action, resource=request.resource):
        audit_log("forbidden", caller=caller, request=request)
        return {"status": 403, "error": "forbidden"}

    # 3. Rate limit: are they within their quota?
    if rate_limited(caller, quota="100/min"):
        audit_log("rate_limited", caller=caller, request=request)
        return {"status": 429, "error": "rate_limited"}

    # 4. Audit: log the request
    audit_log("request_started", caller=caller, request=request)

    # 5. Process: run the agent
    result = run_agent(goal=request.goal, tenant=caller.tenant)

    # 6. Audit: log the result
    audit_log("request_completed", caller=caller, request=request, result=result)

    return {"status": 200, "result": result}
```

The pattern that wins interviews is the "5 layers × 3 compliance regimes + zero trust" pattern. The candidate who says "I design the security perimeter as 5 layers (API gateway, mTLS, secrets, audit log, identity) mapped to 3 compliance regimes (SOC 2, HIPAA, PCI). Zero trust: every request is authenticated, authorized, and audited. The wrong choice is 'we trust our network' (perimeter-based security). The right choice is zero trust + the 5 layers + the compliance map" is the candidate who demonstrates the security-mindset.

## Code or example

The 5 most common security errors and fixes:

```python
SECURITY_ERRORS = {
    "secret_in_git": {
        "symptom": "API key or DB password committed to git",
        "cause": "Developer pastes the secret in code; commits without checking",
        "fix": "Pre-commit hook (gitleaks, trufflehog) blocks commits with secrets; rotate the leaked secret immediately; use Vault instead of env vars",
    },
    "missing_rate_limit": {
        "symptom": "API is hammered; cost spikes; agent is overloaded",
        "cause": "No rate limit on the API gateway",
        "fix": "Add rate limit (100/min per API key, 1000/min per tenant); add alert when rate limit is hit > 1000 times/day",
    },
    "audit_log_disabled": {
        "symptom": "Can't answer 'who did what when' during a security review",
        "cause": "Audit log not configured; or audit log retention too short",
        "fix": "Enable audit log on API gateway + the agent; retention 1 year; test the audit log by simulating a request",
    },
    "overprivileged_caller": {
        "symptom": "An OAuth client has more scopes than needed",
        "cause": "Developer grants '*' scope for simplicity",
        "fix": "Grant the minimum necessary scope; review OAuth client scopes quarterly; use scope-based authorization",
    },
    "missing_mtls": {
        "symptom": "Service-to-service traffic is unencrypted",
        "cause": "TLS not configured; or TLS is configured but not enforced",
        "fix": "Enforce TLS on all service-to-service communication; use Linkerd or Istio for automatic mTLS; rotate certs every 90 days",
    },
}
```

The 4 secret rotation patterns (the FDE's reference):

```python
SECRET_ROTATION = {
    "static_with_rotation": {
        "description": "Secret is static; rotated manually every 90 days",
        "tools": "AWS Secrets Manager with rotation enabled",
        "process": "Generate new secret in the source service; update in Vault/Secrets Manager; restart the agent to pick up the new secret",
        "downtime": "0 (rolling restart)",
    },
    "dynamic": {
        "description": "Secret is short-lived (e.g., 1 hour); generated on demand",
        "tools": "Vault dynamic secrets; AWS IAM roles for service accounts",
        "process": "Agent requests a new credential at startup; the credential expires in 1 hour; the agent requests a new one when needed",
        "downtime": "0",
    },
    "federated": {
        "description": "No static secret; the agent assumes an IAM role",
        "tools": "AWS IAM roles for service accounts (IRSA), GCP workload identity",
        "process": "The agent assumes a role; the role grants temporary credentials; no static secret is needed",
        "downtime": "0",
    },
    "manual": {
        "description": "Secret is static; rotated manually on a schedule",
        "tools": "1Password, AWS Secrets Manager",
        "process": "Developer generates new secret; updates in 1Password; updates in the production config; restarts the agent",
        "downtime": "< 1 minute (rolling restart)",
    },
}
```

The AtlasMart security perimeter (the case study):

```python
ATLASMART_SECURITY = {
    "compliance_regime": "SOC 2 Type II (in progress); no HIPAA / PCI",
    "layers": {
        "L1_api_gateway": {
            "tool": "AWS API Gateway",
            "rate_limit": "100/min per API key; 1000/min per tenant",
            "auth": "OAuth 2.0 with customer-specific scopes",
            "audit": "All requests logged to CloudWatch + S3 (1 year retention)",
        },
        "L2_mtls": {
            "tool": "Linkerd service mesh",
            "config": "All inter-service communication uses mTLS; certs rotated every 90 days",
            "scope": "agent ↔ postgres, agent ↔ redis, agent ↔ openai",
        },
        "L3_secrets": {
            "tool": "AWS Secrets Manager",
            "secrets": ["openai-api-key", "database-url", "redis-url", "oauth-client-secret"],
            "rotation": "Every 30 days (automated)",
            "access": "IAM role-based; only the agent can read; audit logged",
        },
        "L4_audit_log": {
            "tool": "CloudWatch Logs + S3",
            "events": ["all API requests", "all agent actions (steps, tools, args)", "all secret access", "all config changes"],
            "retention": "30 days hot (CloudWatch) + 1 year cold (S3)",
        },
        "L5_identity": {
            "tool": "OAuth 2.0 (Auth0)",
            "scopes": ["agent:run", "agent:admin", "agent:read"],
            "tenants": "Multi-tenant; each tenant has its own OAuth client + scopes",
        },
    },
    "compliance_artifacts": [
        "SOC 2 Type II report (annual)",
        "Change management policy (GitHub PR reviews)",
        "Incident response plan (runbook + on-call rotation)",
        "Access review (quarterly)",
        "Penetration test (annual)",
    ],
    "monthly_cost": "$50 (API Gateway + Secrets Manager + CloudWatch)",
    "audit_findings": "0 (passed 2026 SOC 2 audit)",
}
```

## Production addendum

The security question is the answer to "how do you secure an agent in production." The 60-second script:

> "5 layers. API gateway (rate limit, auth, audit). mTLS (encrypt in transit). Secrets (Vault, rotation). Audit log (who did what when, 1 year retention). Identity (OAuth, JWT, mTLS). 3 compliance regimes: SOC 2, HIPAA, PCI. Zero trust: every request is authenticated, authorized, audited. The wrong choice is 'we trust our network' (perimeter-based security). The right choice is zero trust + the 5 layers + the compliance map + secret rotation every 30 days + the 5 most common errors."

This is the difference between a candidate who says "we have auth" and a candidate who says "5 layers, 3 compliance regimes, zero trust, 4 secret rotation patterns, the 5 most common errors, the audit log is the CISO's view." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/security/` — the security reference.
- **Reference implementation**: `course/hardcode/level-9-failure-handling/18-hallucination-detector.py` — the canonical security setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — secrets as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — MCP server security parallels the agent security.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — security as a system design topic.

## The 3 questions this lecture preps you for

1. **"How do you secure an agent in production?"** Answer: 5 layers (API gateway, mTLS, secrets, audit log, identity) + 3 compliance regimes (SOC 2, HIPAA, PCI) + zero trust. The wrong choice is "we trust our network." The right choice is the 5 layers + zero trust + the compliance map + secret rotation every 30 days.
2. **"What is zero trust?"** Answer: every request is authenticated (who is the caller?), authorized (what can they do?), and audited (what did they do?). The agent trusts no one — not the network, not the employees, not the FDE. The pattern is the only one that survives a CISO review. Perimeter-based security ("we trust our network") is the wrong choice.
3. **"What is the audit log?"** Answer: every action is logged: who called, when, what they requested, what the agent did, what the result was. The audit log is immutable, queryable, retained for 1 year (or per compliance regime). The audit log is the artifact that answers "what happened" during a security review. The wrong choice is no audit log (can't answer "who did what when").

## Read next

`L8-6-cost-management-at-scale.md` — the 5th pillar: cost management. Per-tenant cost tracking, budget alerts, cost attribution, FinOps. The CFO conversation.