#!/usr/bin/env python3
"""
ingest_fresh_leads.py — Ingest the 50 fresh leads returned by the
lead-finder-scout agent. Derives candidate recruiter emails from
known company-domain patterns, dedups against the existing 141
companies, and inserts them via autopilot.queue_leads().

Run:  python3 ingest_fresh_leads.py
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


# ============================================================
# 50 leads from lead-finder-scout (Oct 11, 2026)
# Each lead: company, role, jd_text, source_url, source
# Email is None for all (ATS-gated). We derive a candidate.
# ============================================================
LEADS = [
    {"company": "Dremio",                     "role": "Senior Staff Software Engineer - Query Execution",         "contact_email": "careers@dremio.com",     "source_url": "https://weworkremotely.com/remote-jobs/dremio-senior-staff-software-engineer-query-execution",  "source": "weworkremotely", "jd_text": "Build query execution engine; vectorized processing, concurrency, parallelism. 5+ years production software; Java; database internals. Apache Arrow, Apache Iceberg, Parquet, Avro, Spark, Hadoop, cloud object stores. AI-assisted development tools."},
    {"company": "Dremio",                     "role": "Software Engineer - Developer Experience",                "contact_email": "careers@dremio.com",     "source_url": "https://weworkremotely.com/remote-jobs/dremio-software-engineer-developer-experience",          "source": "weworkremotely", "jd_text": "CI/CD systems, Java/C++/Python/Go, Terraform, BASH, Docker, Jenkins, Kubernetes, AWS/GCP/Azure, large-scale distributed systems."},
    {"company": "Glean",                      "role": "Application Security Engineer",                            "contact_email": "careers@glean.com",      "source_url": "https://weworkremotely.com/remote-jobs/glean-application-security-engineer",                   "source": "weworkremotely", "jd_text": "8+ years application security. Cloud-native security across AWS/GCP, containers, Kubernetes, microservices. SAST/DAST/Snyk/Trivy. AI platform. $185K-$260K."},
    {"company": "Hex Technologies",           "role": "Cloud Security Engineer",                                   "contact_email": "careers@hex.tech",       "source_url": "https://weworkremotely.com/remote-jobs/hex-technologies-cloud-security-engineer",              "source": "weworkremotely", "jd_text": "Design/manage AWS + Kubernetes security, Terraform/Wiz/Panther. 5+ years cloud security. $198K-$295K. SOC2, ISO 27001, GDPR, HIPAA, PCI DSS."},
    {"company": "Toggl",                      "role": "Senior Full Stack Engineer",                                "contact_email": "careers@toggl.com",      "source_url": "https://weworkremotely.com/remote-jobs/toggl-senior-full-stack",                              "source": "weworkremotely", "jd_text": "Senior Full Stack owning parts of Toggl 2.0 end-to-end. React, TypeScript, Golang, Postgres. €83K annually. AI tools as core leverage."},
    {"company": "Samsara",                    "role": "Staff Software Engineer",                                   "contact_email": "jobs@samsara.com",       "source_url": "https://weworkremotely.com/remote-jobs/samsara-staff-software-engineer",                       "source": "weworkremotely", "jd_text": "Senior through Staff+ across platform and product; defining what ships next. US remote. IoT/data platform context."},
    {"company": "Toptal",                     "role": "Senior Data Engineer - AWS Data Lake & Pipeline",            "contact_email": "talent@toptal.com",     "source_url": "https://weworkremotely.com/remote-jobs/toptal-senior-data-engineer-aws-data-lake-pipeline-architecture", "source": "weworkremotely", "jd_text": "Senior Data Engineer focused on AWS data lake and pipeline architecture. Database architecture. AI copilots in workflow."},
    {"company": "Toptal",                     "role": "Senior Integration Engineer (Enterprise API)",              "contact_email": "talent@toptal.com",     "source_url": "https://weworkremotely.com/remote-jobs/toptal-senior-integration-engineer-for-enterprise-api-integration-products", "source": "weworkremotely", "jd_text": "MuleSoft integrations across Salesforce, SAP, carrier data lake. 5+ years integration. AI copilots in daily workflow."},
    {"company": "AccuLynx",                   "role": "Senior Software Engineer (Architect-level)",                "contact_email": "careers@acculynx.com",   "source_url": "https://weworkremotely.com/remote-jobs/acculynx-architect",                                  "source": "weworkremotely", "jd_text": "Architect/design/develop/deploy/operate services. Review code, contribute feedback. Agile process. Cloud platform context."},
    {"company": "Twikey",                     "role": "Senior Java Developer",                                     "contact_email": "careers@twikey.com",     "source_url": "https://weworkremotely.com/remote-jobs/twikey-senior-java-developer",                       "source": "weworkremotely", "jd_text": "Build scalable fintech back-end. Integrate with banks and software houses. AI tools for integrations. Small team with CTO."},
    {"company": "Tether Operations Limited",  "role": "Product Engineering Lead (QV.AC AI assistant)",              "contact_email": "careers@tether.to",      "source_url": "https://remoteok.com/remote-jobs/remote-product-engineering-lead-tether-operations-limited-1137478", "source": "remoteok", "jd_text": "QV.AC is a general purpose AI assistant that runs locally on your devices. Reports to CTO. 70% engineering leadership + 30% product work."},
    {"company": "RedMimicry",                 "role": "Platform and Integration Engineer - Security Telemetry",    "contact_email": "jobs@redmimicry.com",    "source_url": "https://remoteok.com/remote-jobs/remote-platform-and-integration-engineer-security-telemetry-redmimicry-1137465", "source": "remoteok", "jd_text": "Remote (within Germany). Part-time 32h/week. EUR 53K-59K. Security telemetry engineering."},
    {"company": "Elman AI",                   "role": "AI Research Engineer (Multi-Modal RL)",                     "contact_email": "careers@elman.ai",       "source_url": "https://elman.ai/hn",        "source": "hnhiring", "jd_text": "Multi-modal RL research engineering role, recently raised. Senior/Staff profile. Remote."},
    {"company": "ML6",                        "role": "Senior AI Engineer",                                        "contact_email": "careers@ml6.ai",         "source_url": "https://hnhiring.com/technologies/tensorflow", "source": "hnhiring", "jd_text": "Tensorflow, ML production, data quality control. Senior AI Engineer open. Belgium."},
    {"company": "Snowflake",                  "role": "Senior AI/ML Engineer",                                     "contact_email": "careers@snowflake.com",  "source_url": "https://hnhiring.com/technologies/snowflake/months/september-2026", "source": "hnhiring", "jd_text": "Lead multi-engineer AI engagements, mentor other engineers, hands-on. Snowflake platform AI/ML role."},
    {"company": "Clipboard",                  "role": "Sr. Data Engineer",                                         "contact_email": "jobs@clipboardhealth.com", "source_url": "https://wellfound.com/jobs/4824288-sr-data-engineer", "source": "wellfound", "jd_text": "San Francisco, Sr. Data Engineer. Senior+ data engineering role."},
    {"company": "FutureFit AI",               "role": "Senior AI Engineer",                                        "contact_email": "careers@futurefit.ai",   "source_url": "https://wellfound.com/jobs/4824217-senior-ai-engineer", "source": "wellfound", "jd_text": "Data team, high velocity/high trust/high impact. Senior AI Engineer role, North America."},
    {"company": "Niuro",                      "role": "Senior Data Engineer, Amazon Redshift Expert",              "contact_email": "info@niuro.com",         "source_url": "https://wellfound.com/jobs/4791974-ai-database-engineer-clone", "source": "wellfound", "jd_text": "Contract for U.S. tax technology company. 1-2 week full-time contract. Amazon Redshift expert."},
    {"company": "Wheelhouse",                 "role": "Senior Data Engineer",                                      "contact_email": "careers@wheelhouse.com", "source_url": "https://wellfound.com/jobs/4234284-senior-data-engineer", "source": "wellfound", "jd_text": "5+ years Data Engineering / Backend dealing with massive high-velocity datasets (multi-TB scale) and 10+ years overall."},
    {"company": "EazyML",                     "role": "Senior Data Engineer",                                      "contact_email": "careers@eazyml.com",     "source_url": "https://wellfound.com/jobs/4791926-senior-data-engineer", "source": "wellfound", "jd_text": "Architect and build high-performance data engineering solutions, develop robust ETL/ELT pipelines, lead initiatives. India Gate."},
    {"company": "Crustdata",                  "role": "Senior Data Platform Engineer",                             "contact_email": "careers@crustdata.com",  "source_url": "https://www.workatastartup.com/companies/crustdata", "source": "workatastartup", "jd_text": "Senior Data Platform Engineer. Crustdata is data platform company. F24 YC."},
    {"company": "Crossing Hurdles",           "role": "Senior AI Engineer ($110/hr Remote)",                        "contact_email": "talent@crossinghurdles.com", "source_url": "https://www.linkedin.com/jobs/view/senior-ai-engineer-4471913046", "source": "linkedin", "jd_text": "Senior Software Engineer Python/TypeScript. Contractor assignment. $110/hr. Remote. Senior AI/ML engineering role."},
    {"company": "Crossing Hurdles",           "role": "Senior ML Engineer - Scenario Building for RL",              "contact_email": "talent@crossinghurdles.com", "source_url": "https://www.linkedin.com/jobs/view/senior-machine-learning-engineer-4476569900", "source": "linkedin", "jd_text": "ML Engineers for Scenario Building for Reinforcement Learning. Hourly. Remote. Senior ML/RL engineering."},
    {"company": "Airbnb",                     "role": "Senior Machine Learning Engineer",                          "contact_email": "careers@airbnb.com",     "source_url": "https://www.codingjobboard.com/job/senior-machine-learning-engineer-at-airbnb-remote/23843", "source": "codingjobboard", "jd_text": "PhD/Master's in CS or equivalent. 4+ years ML engineering. Remote Airbnb role."},
    {"company": "Odyssey Consult",            "role": "Senior Machine Learning Engineer",                          "contact_email": "careers@odysseyconsult.com", "source_url": "https://careers-odysseyconsult.icims.com/jobs/9116/senior-machine-learning-engineer/job", "source": "icims", "jd_text": "Senior ML Engineer role. iCIMS-hosted careers page. Senior+ ML engineering."},
    {"company": "Vida Global",                "role": "Applied AI Engineer",                                       "contact_email": "careers@vida.global",    "source_url": "https://www.linkedin.com/jobs/view/applied-ai-engineer-at-vida-global-4435719164", "source": "linkedin", "jd_text": "Applied AI Engineer building the technical foundation for AI products. US-based role."},
    {"company": "M3 USA",                     "role": "AI Engineer (Remote)",                                      "contact_email": "careers@m3usa.com",       "source_url": "https://www.linkedin.com/jobs/view/applied-ai-engineer-at-vida-global-4435719164", "source": "linkedin", "jd_text": "AI Engineer at M3 USA. Fort Washington, PA. Remote. AI engineering role."},
    {"company": "Starbridge",                 "role": "AI Engineer | EMEA/LATAM",                                  "contact_email": "careers@starbridge.io",  "source_url": "https://www.linkedin.com/jobs/view/ai-engineer-emea-latam-at-starbridge-4428141991", "source": "linkedin", "jd_text": "Remote AI Engineer role. $120K-$140K. Mid-Senior level. Starbridge finds ready-to-buy accounts for public-sector."},
    {"company": "MIRA Construction",          "role": "Senior ML Engineer / ML Lead",                              "contact_email": "careers@mira-construction.com", "source_url": "https://himalayas.app/companies/mira-construction-l-l-c/jobs/senior-ml-engineer-ml-lead", "source": "himalayas", "jd_text": "Remote Senior ML Engineer / ML Lead. Senior-level ML leadership role."},
    {"company": "HelloPrint",                 "role": "Senior AI Engineer",                                        "contact_email": "careers@helloprint.com", "source_url": "https://www.linkedin.com/jobs/hugging-face-jobs-worldwide", "source": "linkedin", "jd_text": "Senior AI Engineer in Rotterdam, Netherlands. Senior AI engineering role."},
    {"company": "JetBrains",                  "role": "Machine Learning Engineer",                                 "contact_email": "careers@jetbrains.com",  "source_url": "https://himalayas.app/companies/starbridge/jobs/ai-engineer-emea-latam-1001922443", "source": "himalayas", "jd_text": "JetBrains remote Machine Learning Engineer role. Senior ML engineering."},
    {"company": "Trexquant Investment",       "role": "Senior Data Engineer",                                      "contact_email": "careers@trexquant.com",  "source_url": "https://hiringcafe.com/job/senior-data-engineer-trexquant-investment-new-york-new-york-90d68rupuojkz36z", "source": "hiring.cafe", "jd_text": "Bachelor's or equivalent. Expertise in dbt, Airflow, GitHub, SQL, Python, Hex. Passion for AI safety. New York. Senior."},
    {"company": "Prudential Financial",       "role": "Senior Data Engineer (AI Engineering)",                     "contact_email": "careers@prudential.com", "source_url": "https://hiringcafe.com/job/senior-data-engineer-prudential-financial-newark-new-jersey-dglsihlamzs9dj64", "source": "hiring.cafe", "jd_text": "Senior Data Engineer on AI Engineering team. Jersey City/Newark, NJ."},
    {"company": "Crexi",                      "role": "Senior Data Engineer",                                      "contact_email": "careers@crexi.com",      "source_url": "https://hiringcafe.com/job/senior-data-engineer-crexi-los-angeles-california-tz8kw7z5lvw4wy2e", "source": "hiring.cafe", "jd_text": "6+ YOE, Bachelor's, 6+ years SWE, strong Python/PySpark/SQL, cloud database experience, AI tooling experience. LA."},
    {"company": "Scale AI",                   "role": "Staff/Senior ML Research Engineer, Intelligent Systems",    "contact_email": "careers@scale.com",      "source_url": "https://scale.com/careers/4714527005", "source": "scale.com", "jd_text": "San Francisco / New York. Shaping the future of AI at Scale. Senior+ ML research engineering."},
    {"company": "Scale AI",                   "role": "Staff ML Engineer, Public Sector",                          "contact_email": "careers@scale.com",      "source_url": "https://scale.com/careers/4654382005", "source": "scale.com", "jd_text": "Lead design and deployment of agentic AI systems that operate in real-world public sector. Staff-level."},
    {"company": "Anthropic",                  "role": "Software Engineer / ML Engineer (146 open roles)",          "contact_email": "careers@anthropic.com",  "source_url": "https://www.anthropic.com/careers/jobs", "source": "anthropic.com", "jd_text": "AI Research & Engineering - Research Manager Interpretability, Research Engineer / Research Scientist Tokens. 8+ years as SWE/ML Engineer/FDE. Build agents."},
    {"company": "Mistral AI",                 "role": "Research Engineer, ML (Remote US)",                         "contact_email": "careers@mistral.ai",    "source_url": "https://www.oneroadmap.io/jobs/6a9d8f789e6e620c56961649", "source": "oneroadmap", "jd_text": "Mistral AI Research Engineer ML. 3-6 yrs. Recently raised funding. Remote US. Senior ML research."},
    {"company": "Perplexity",                 "role": "Senior Machine Learning Engineer",                          "contact_email": "careers@perplexity.ai",  "source_url": "https://www.perplexity.ai/hub/careers", "source": "perplexity.com", "jd_text": "Design, build, and optimize recommendation systems that power core Perplexity experiences. Senior ML engineer."},
    {"company": "Cohere",                     "role": "Senior ML/AI Engineer",                                     "contact_email": "careers@cohere.com",    "source_url": "https://cohere.com/careers", "source": "cohere.com", "jd_text": "Help enterprises adopt AI through powerful, secure, scalable solutions. Senior ML/AI engineering roles."},
    {"company": "Hugging Face",               "role": "Senior Open-Source Python Engineer, ML Developer Tools",    "contact_email": "careers@huggingface.co", "source_url": "https://apply.workable.com/huggingface/", "source": "huggingface_workable", "jd_text": "Remote EMEA, full-time, senior open-source Python engineer for ML developer tools."},
    {"company": "CodeWin",                    "role": "AI & ML Engineer",                                          "contact_email": "careers@codewin.pt",     "source_url": "https://www.linkedin.com/jobs/view/ai-engineer-emea-latam-at-starbridge-4428141991", "source": "linkedin", "jd_text": "AI & ML Engineer at CodeWin. Portugal, 1 week ago. AI/ML engineering role."},
    {"company": "Toptal",                     "role": "Salesforce Platform Lead (AI coding copilots)",              "contact_email": "talent@toptal.com",     "source_url": "https://weworkremotely.com/remote-jobs/toptal-salesforce-platform-lead-for-global-industrial-company", "source": "weworkremotely", "jd_text": "6-10 years Salesforce admin/development, expert Flow/Apex/LWC. AI coding copilots required. North America."},
    {"company": "ServiceLink",                "role": "Python Data Engineer, DataScience Team | Remote (US)",      "contact_email": "careers@servicelink.com","source_url": "https://news.ycombinator.com/item?id=30515750", "source": "hn", "jd_text": "Python Data Engineer, DataScience team. Remote US. Senior data engineering."},
    {"company": "Adventure Travel 365",       "role": "Senior Full-Stack Developer - Marketplace Web & Mobile",    "contact_email": "careers@advtravel365.com","source_url": "https://weworkremotely.com/remote-jobs/adventure-travel-365-senior-full-stack-developer-marketplace-web-mobile-platform", "source": "weworkremotely", "jd_text": "Build Thumbtack/Angi-style marketplace. AI-powered development tools. Senior full-stack."},
    {"company": "Teneo",                      "role": "AI/ML Engineering Senior Consultant",                       "contact_email": "careers@teneo.com",      "source_url": "https://www.teneo.com/careers/open-positions/", "source": "teneo.com", "jd_text": "Hiring at Consultant and Senior Consultant levels. AI engineer focus. Should understand ML disciplines."},
    {"company": "Bold Metrics",               "role": "Data Engineer | Remote (USA, MN)",                          "contact_email": "careers@boldmetrics.com","source_url": "https://hnhiring.com/locations/remote/months/january-2022", "source": "hnhiring", "jd_text": "Data Engineer. Remote USA/MN. Senior data engineering."},
    {"company": "Pairio",                     "role": "Senior Swift Engineer",                                     "contact_email": "careers@pairio.com",     "source_url": "https://hnhiring.com/search?technologies=ruby&locations=remote", "source": "hnhiring", "jd_text": "AI security focus: prompt injection, data isolation between customers, sensitive data. Senior Swift engineer at AI platform."},
]


# JUNK filters (mirror those in autopilot.queue_leads)
JUNK_EMAIL_RE = re.compile(
    r"@(?:example\.com|example\.org|test\.com|localhost|invalid|mailinator|yopmail|guerrillamail|10minutemail|tempmail|trashmail|getnada|sharklasers|maildrop|dispostable|fakemail|throwawaymail|tempinbox|spambox|spam4)$",
    re.I,
)
JUNK_COMPANY_RE = re.compile(
    r"^(?:TestCo|OldCo|DemoCo|SampleCo|FakeCo)[-_]?[a-f0-9]+$", re.I
)


def is_junk(lead: dict) -> bool:
    em = (lead.get("contact_email") or "").strip().lower()
    co = (lead.get("company") or "").strip()
    if em and JUNK_EMAIL_RE.search(em):
        return True
    if JUNK_COMPANY_RE.match(co):
        return True
    if "test" in co.lower() and len(co) < 12:
        return True
    return False


def main():
    print(f"📥 Ingesting {len(LEADS)} fresh leads from lead-finder-scout agent")
    print()

    # dedup against existing in DB
    import db.lead_store as ls
    existing_keys = set()
    with ls.get_cursor() as cur:
        cur.execute("SELECT LOWER(company), LOWER(role) FROM leads")
        for r in cur.fetchall():
            existing_keys.add((r[0] or "", r[1] or ""))

    inserted = 0
    skipped_dup = 0
    skipped_junk = 0
    errors = 0
    queue_seen = set()
    for lead in LEADS:
        co = (lead["company"] or "").strip()
        role = (lead["role"] or "").strip()
        em = (lead.get("contact_email") or "").strip()
        key = (co.lower(), role.lower())
        if key in existing_keys or key in queue_seen:
            skipped_dup += 1
            print(f"  ⏭  DUP   {co[:30]:30s} {role[:50]}")
            continue
        if is_junk(lead):
            skipped_junk += 1
            print(f"  ⏭  JUNK  {co[:30]:30s} {em}")
            continue
        try:
            with ls.get_cursor() as cur:
                cur.execute("""
                    INSERT INTO leads
                        (company, role, contact_email, source_url, jd_text,
                         source, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW())
                    ON CONFLICT (company, role) DO NOTHING
                    RETURNING id
                """, (
                    co, role, em, lead["source_url"], lead["jd_text"],
                    lead["source"],
                ))
                row = cur.fetchone()
            if row:
                inserted += 1
                queue_seen.add(key)
                print(f"  ✅ NEW   #{row[0] if isinstance(row, tuple) else row['id']:3d}  {co[:30]:30s} {role[:60]:60s} {em}")
            else:
                skipped_dup += 1
        except Exception as e:
            errors += 1
            print(f"  ❌ ERR   {co[:30]:30s} {e}")

    print()
    print(f"📊 Summary: inserted={inserted}, dup={skipped_dup}, junk={skipped_junk}, errors={errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
