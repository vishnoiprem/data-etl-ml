# AWS Professional Services — FDE / Sr. Consultant

## Company Snapshot
- **HQ**: Seattle, WA
- **Team Size**: ~800+ ProServe FDEs
- **Comp**: Base $150K–$200K; TC $220K–$400K
- **What they deploy**: Bedrock / SageMaker / Q for enterprise
- **Travel**: 50–75% (Mon–Thu)

## Interview Process
1. Recruiter
2. Coding screen
3. AWS-flavored system design
4. Loop
   - Coding 2
   - AWS Well-Architected design
   - Customer scenario
   - Bar-raiser (often an SA manager)

---

## ✅ SUCCESS STORIES

### AWS architecture
**Q:** *"Design a Bedrock-powered document Q&A for an insurance company with PII constraints."*
**A (winner):**
- **Edge**: CloudFront + WAF.
- **Auth**: Cognito + IAM Identity Center; SSO with customer's IdP.
- **Compute**: Lambda for orchestration, Step Functions for multi-step flows.
- **Bedrock**: Claude via cross-region inference profile (eu-central-1 for EU, us-east-1 for US); guardrails enabled.
- **Vector**: OpenSearch Serverless with VPC endpoint.
- **PII**: Comprehend PII detection on inputs + outputs; KMS encryption with customer-managed key.
- **Observability**: CloudWatch + X-Ray.
- **Well-Architected**: hits all 6 pillars with documented trade-offs.
**Why it worked:** AWS-native, addressed PII explicitly, named KMS / WAF / Cognito / OpenSearch.

---

### Customer scenario
**Q:** *"Customer wants to migrate 200 ML models to Bedrock in 6 months. They're terrified of regressions."*
**A (winner):** *"I'd propose a 'shadow + parallel run' framework: every legacy model runs in parallel with the Bedrock version for 4 weeks; we measure agreement + business KPIs; we cut over per use case once parity is met. Use SageMaker Model Registry for the registry of record. I'd staff a 2-person team + customer counterpart for 6 months."*
**Why it worked:** Concrete plan (shadow mode, parallel run, agreement metrics), staff plan, timeline.

---

## ❌ REJECTION STORIES

### AWS architecture
**Q:** *"Design a serverless API."*
**A (loser):** Generic answer without naming AWS services.
**Why it failed:** AWS interview wants AWS-native answers.
**What they should have said:** API Gateway, Lambda, DynamoDB, S3, CloudWatch, X-Ray, SAM / CDK for IaC.

---

### Customer scenario
**Q:** *"Customer says Bedrock doesn't work in their region."*
**A (loser):** *"Use OpenAI."*
**Why it failed:** Counter-positioning inside an AWS interview. Wrong answer.
**What they should have said:** *"Which region? Bedrock is in most major regions, but not all. We can use cross-region inference profiles to route. If truly unavailable, the closest region via latency-based routing."*

---

## 📚 Reading List
1. AWS Well-Architected Framework + GenAI lens
3. AWS Bedrock docs
4. *"Serverless Architectures on AWS"* (free ebook)
5. AWS re:Invent talks (YouTube)
6. levels.fyi AWS ProServe
7. r/aws threads