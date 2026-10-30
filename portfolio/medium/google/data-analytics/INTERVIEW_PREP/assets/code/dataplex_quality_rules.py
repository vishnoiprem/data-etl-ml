# Dataplex Quality Rules — Programmatic Governance as Code
## Production-Grade Python for Dataplex Data Quality & Governance Automation

---

## 🎯 Use Case
**Governance as Code:** Define, deploy, and manage Dataplex data quality scans, policy tags, and lineage programmatically. Enables CI/CD for governance, version-controlled quality rules, and automated compliance reporting.

---

```python
"""
dataplex_quality_rules.py

Production-grade Dataplex governance automation.
Demonstrates: Quality scan creation, policy tag taxonomy, lineage extraction,
compliance reporting, and CI/CD integration.

Prerequisites:
    pip install google-cloud-dataplex google-cloud-dlp google-cloud-bigquery

Authentication:
    gcloud auth application-default login
    # Or service account with roles/dataplex.admin, roles/dlp.admin, roles/bigquery.metadataViewer
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from google.cloud import dataplex_v1, dlp_v2, bigquery
from google.api_core import exceptions as gcp_exceptions
from google.protobuf import field_mask_pb2


# ─── Configuration & Constants ────────────────────────────────────────────

class QualityDimension(str, Enum):
    """Standard data quality dimensions."""
    COMPLETENESS = "COMPLETENESS"
    ACCURACY = "ACCURACY"
    CONSISTENCY = "CONSISTENCY"
    VALIDITY = "VALIDITY"
    UNIQUENESS = "UNIQUENESS"
    TIMELINESS = "TIMELINESS"


class RuleType(str, Enum):
    """Dataplex rule types."""
    ROW_CONDITION = "ROW_CONDITION"
    SET_CONDITION = "SET_CONDITION"
    SQL = "SQL"


# Default quality thresholds (adjust per domain)
DEFAULT_THRESHOLDS = {
    QualityDimension.COMPLETENESS: 0.99,      # 99% non-null
    QualityDimension.ACCURACY: 0.95,          # 95% valid format
    QualityDimension.CONSISTENCY: 0.98,       # 98% cross-field consistent
    QualityDimension.VALIDITY: 0.97,          # 97% valid values
    QualityDimension.UNIQUENESS: 0.999,       # 99.9% unique keys
    QualityDimension.TIMELINESS: 3600,        # 1 hour max latency
}


# ─── Quality Rule Definitions ──────────────────────────────────────────────

class QualityRule:
    """Reusable quality rule definition."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        dimension: QualityDimension,
        rule_type: RuleType,
        expression: str,
        description: str = "",
        threshold: float = 0.95,
        columns: Optional[List[str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.rule_id = rule_id
        self.name = name
        self.dimension = dimension
        self.rule_type = rule_type
        self.expression = expression
        self.description = description
        self.threshold = threshold
        self.columns = columns or []
        self.tags = tags or {}
    
    def to_dataplex_rule(self) -> dataplex_v1.DataQualityRule:
        """Convert to Dataplex DataQualityRule proto."""
        rule = dataplex_v1.DataQualityRule()
        rule.rule_id = self.rule_id
        rule.name = self.name
        rule.description = self.description
        
        if self.rule_type == RuleType.ROW_CONDITION:
            rule.row_condition = dataplex_v1.DataQualityRule.RowCondition(
                expression=self.expression,
            )
        elif self.rule_type == RuleType.SET_CONDITION:
            # For aggregate rules (e.g., COUNT(*) > threshold)
            rule.set_condition = dataplex_v1.DataQualityRule.SetCondition(
                expression=self.expression,
            )
        elif self.rule_type == RuleType.SQL:
            # Custom SQL for complex logic
            rule.sql = self.expression
        
        # Add dimension as label for filtering
        rule.labels = {
            "quality_dimension": self.dimension.value,
            "threshold": str(self.threshold),
        }
        rule.labels.update(self.tags)
        
        return rule


# ─── Pre-built Rule Library (Domain-Agnostic) ──────────────────────────────

def get_standard_quality_rules(table_schema: Dict[str, str]) -> List[QualityRule]:
    """
    Generate standard quality rules from table schema.
    
    Args:
        table_schema: Dict of column_name -> BigQuery data type
        
    Returns:
        List of QualityRule objects
    """
    rules = []
    
    # 1. Completeness: Primary key not null
    pk_columns = [c for c, t in table_schema.items() if c.endswith("_id") or c in ("id", "event_id", "customer_id")]
    for pk in pk_columns:
        rules.append(QualityRule(
            rule_id=f"completeness_{pk}_not_null",
            name=f"{pk} completeness",
            dimension=QualityDimension.COMPLETENESS,
            rule_type=RuleType.ROW_CONDITION,
            expression=f"{pk} IS NOT NULL",
            description=f"Primary key {pk} must not be null",
            threshold=DEFAULT_THRESHOLDS[QualityDimension.COMPLETENESS],
            columns=[pk],
            tags={"category": "completeness", "severity": "critical"},
        ))
    
    # 2. Completeness: Required columns not null
    required_columns = [c for c in table_schema.keys() if not c.startswith("_")]
    for col in required_columns:
        if col not in pk_columns:
            rules.append(QualityRule(
                rule_id=f"completeness_{col}_not_null",
                name=f"{col} completeness",
                dimension=QualityDimension.COMPLETENESS,
                rule_type=RuleType.ROW_CONDITION,
                expression=f"{col} IS NOT NULL",
                description=f"Required column {col} should not be null",
                threshold=DEFAULT_THRESHOLDS[QualityDimension.COMPLETENESS] * 0.9,  # Slightly lower for non-PK
                columns=[col],
                tags={"category": "completeness", "severity": "warning"},
            ))
    
    # 3. Validity: Email format
    email_columns = [c for c in table_schema.keys() if "email" in c.lower()]
    for col in email_columns:
        rules.append(QualityRule(
            rule_id=f"validity_{col}_email_format",
            name=f"{col} email format",
            dimension=QualityDimension.VALIDITY,
            rule_type=RuleType.ROW_CONDITION,
            expression=f"{col} IS NULL OR REGEXP_CONTAINS({col}, r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$')",
            description=f"{col} must be valid email format",
            threshold=DEFAULT_THRESHOLDS[QualityDimension.VALIDITY],
            columns=[col],
            tags={"category": "validity", "severity": "warning"},
        ))
    
    # 4. Validity: Positive amounts
    amount_columns = [c for c in table_schema.keys() if "amount" in c.lower() or "price" in c.lower() or "revenue" in c.lower()]
    for col in amount_columns:
        rules.append(QualityRule(
            rule_id=f"validity_{col}_positive",
            name=f"{col} positive value",
            dimension=QualityDimension.VALIDITY,
            rule_type=RuleType.ROW_CONDITION,
            expression=f"{col} IS NULL OR {col} >= 0",
            description=f"{col} must be non-negative",
            threshold=DEFAULT_THRESHOLDS[QualityDimension.VALIDITY],
            columns=[col],
            tags={"category": "validity", "severity": "critical"},
        ))
    
    # 5. Uniqueness: Primary key uniqueness
    for pk in pk_columns:
        rules.append(QualityRule(
            rule_id=f"uniqueness_{pk}_unique",
            name=f"{pk} uniqueness",
            dimension=QualityDimension.UNIQUENESS,
            rule_type=RuleType.SET_CONDITION,
            expression=f"COUNT(DISTINCT {pk}) / COUNT(*) >= {DEFAULT_THRESHOLDS[QualityDimension.UNIQUENESS]}",
            description=f"Primary key {pk} must be unique",
            threshold=DEFAULT_THRESHOLDS[QualityDimension.UNIQUENESS],
            columns=[pk],
            tags={"category": "uniqueness", "severity": "critical"},
        ))
    
    # 6. Timeliness: Data freshness (if timestamp column exists)
    ts_columns = [c for c in table_schema.keys() if "timestamp" in c.lower() or "date" in c.lower() or "_ts" in c.lower() or "_dt" in c.lower()]
    for col in ts_columns[:1]:  # Use first timestamp column
        rules.append(QualityRule(
            rule_id=f"timeliness_{col}_freshness",
            name=f"{col} data freshness",
            dimension=QualityDimension.TIMELINESS,
            rule_type=RuleType.SQL,
            expression=f"""
                SELECT 
                    CASE 
                        WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX({col}), SECOND) <= {DEFAULT_THRESHOLDS[QualityDimension.TIMELINESS]}
                        THEN 1.0 ELSE 0.0 
                    END as freshness_score
                FROM `{{table_fqn}}`
            """,
            description=f"Data should be fresher than {DEFAULT_THRESHOLDS[QualityDimension.TIMELINESS]} seconds",
            threshold=1.0,
            columns=[col],
            tags={"category": "timeliness", "severity": "warning"},
        ))
    
    return rules


# Domain-specific rule sets
FINANCIAL_RULES = [
    QualityRule(
        rule_id="fin_accuracy_reconciliation",
        name="Financial reconciliation",
        dimension=QualityDimension.ACCURACY,
        rule_type=RuleType.SQL,
        expression="""
            SELECT 
                CASE 
                    WHEN ABS(SUM(credit) - SUM(debit)) / NULLIF(SUM(credit), 0) <= 0.001
                    THEN 1.0 ELSE 0.0 
                END as reconciliation_score
            FROM `{{table_fqn}}`
        """,
        description="Credits and debits must reconcile within 0.1%",
        threshold=1.0,
        columns=["credit", "debit"],
        tags={"domain": "finance", "severity": "critical", "regulation": "SOX"},
    ),
    QualityRule(
        rule_id="fin_validity_currency_code",
        name="Valid ISO currency code",
        dimension=QualityDimension.VALIDITY,
        rule_type=RuleType.ROW_CONDITION,
        expression="currency IN ('USD', 'EUR', 'GBP', 'JPY', 'SGD', 'AUD', 'CAD', 'CHF', 'CNY', 'HKD')",
        description="Currency must be valid ISO 4217 code",
        threshold=1.0,
        columns=["currency"],
        tags={"domain": "finance", "severity": "critical"},
    ),
]

HEALTHCARE_RULES = [
    QualityRule(
        rule_id="hc_accuracy_phi_detection",
        name="PHI detection accuracy",
        dimension=QualityDimension.ACCURACY,
        rule_type=RuleType.SQL,
        expression="""
            -- Uses DLP scan results stored in metadata table
            SELECT 
                CASE 
                    WHEN phi_detected_count = 0 THEN 1.0 
                    ELSE 0.0 
                END as phi_score
            FROM `{{dlp_results_table}}`
            WHERE source_table = '{{table_fqn}}'
        """,
        description="No PHI should be detected in non-PHI tables",
        threshold=1.0,
        columns=[],
        tags={"domain": "healthcare", "regulation": "HIPAA", "severity": "critical"},
    ),
]


# ─── Dataplex Client Wrapper ───────────────────────────────────────────────

class DataplexGovernanceClient:
    """High-level client for Dataplex governance operations."""
    
    def __init__(self, project_id: str, location: str = "asia-southeast1"):
        self.project_id = project_id
        self.location = location
        self._dataplex_client = dataplex_v1.DataScanServiceClient()
        self._catalog_client = dataplex_v1.CatalogServiceClient()
        self._dlp_client = dlp_v2.DlpServiceClient()
        self._bq_client = bigquery.Client(project=project_id)
    
    @property
    def parent(self) -> str:
        return f"projects/{self.project_id}/locations/{self.location}"
    
    # ─── Data Quality Scans ──────────────────────────────────────────────
    
    def create_data_quality_scan(
        self,
        scan_id: str,
        data_source: str,  # BigQuery table: projects/proj/datasets/ds/tables/tbl
        rules: List[QualityRule],
        schedule: str = "0 6 * * *",  # Daily 6 AM UTC
        description: str = "",
        labels: Optional[Dict[str, str]] = None,
    ) -> dataplex_v1.DataScan:
        """Create a Dataplex data quality scan."""
        
        # Build scan configuration
        scan = dataplex_v1.DataScan()
        scan.name = f"{self.parent}/dataScans/{scan_id}"
        scan.description = description
        scan.labels = labels or {}
        scan.labels.update({"managed-by": "governance-as-code"})
        
        # Data source
        scan.data = dataplex_v1.DataScan.Data()
        scan.data.resource = data_source
        
        # Quality specification
        spec = dataplex_v1.DataQualitySpec()
        for rule in rules:
            spec.rules.append(rule.to_dataplex_rule())
        scan.data_quality_spec = spec
        
        # Schedule
        if schedule:
            scan.schedule = dataplex_v1.DataScan.Schedule()
            scan.schedule.cron = schedule
            scan.schedule.timezone = "UTC"
        
        # Execution spec
        scan.execution_spec = dataplex_v1.DataScan.ExecutionSpec()
        scan.execution_spec.trigger = dataplex_v1.DataScan.ExecutionSpec.Trigger.ON_DEMAND
        
        # Create request
        request = dataplex_v1.CreateDataScanRequest(
            parent=self.parent,
            data_scan_id=scan_id,
            data_scan=scan,
        )
        
        try:
            operation = self._dataplex_client.create_data_scan(request=request)
            result = operation.result(timeout=300)
            print(f"Created data quality scan: {result.name}")
            return result
        except gcp_exceptions.AlreadyExists:
            print(f"Scan {scan_id} already exists, updating...")
            return self.update_data_quality_scan(scan_id, rules, schedule, description, labels)
    
    def update_data_quality_scan(
        self,
        scan_id: str,
        rules: List[QualityRule],
        schedule: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> dataplex_v1.DataScan:
        """Update existing data quality scan."""
        
        scan_name = f"{self.parent}/dataScans/{scan_id}"
        
        # Get current scan
        current = self._dataplex_client.get_data_scan(name=scan_name)
        
        # Update rules
        spec = dataplex_v1.DataQualitySpec()
        for rule in rules:
            spec.rules.append(rule.to_dataplex_rule())
        current.data_quality_spec = spec
        
        # Update schedule if provided
        if schedule:
            current.schedule = dataplex_v1.DataScan.Schedule()
            current.schedule.cron = schedule
            current.schedule.timezone = "UTC"
        
        # Update description
        if description:
            current.description = description
        
        # Update labels
        if labels:
            current.labels = {**current.labels, **labels, "managed-by": "governance-as-code"}
        
        # Build update mask
        update_mask = field_mask_pb2.FieldMask(
            paths=["data_quality_spec", "schedule", "description", "labels"]
        )
        
        request = dataplex_v1.UpdateDataScanRequest(
            data_scan=current,
            update_mask=update_mask,
        )
        
        operation = self._dataplex_client.update_data_scan(request=request)
        result = operation.result(timeout=300)
        print(f"Updated data quality scan: {result.name}")
        return result
    
    def run_data_quality_scan(self, scan_id: str) -> dataplex_v1.RunDataScanResponse:
        """Trigger on-demand data quality scan."""
        request = dataplex_v1.RunDataScanRequest(
            name=f"{self.parent}/dataScans/{scan_id}",
        )
        operation = self._dataplex_client.run_data_scan(request=request)
        return operation.result(timeout=600)
    
    def get_scan_results(self, scan_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Get latest scan results with parsed metrics."""
        
        scan_name = f"{self.parent}/dataScans/{scan_id}"
        
        if run_id:
            run_name = f"{scan_name}/runs/{run_id}"
        else:
            # Get latest run
            runs = list(self._dataplex_client.list_data_scan_runs(parent=scan_name))
            if not runs:
                return {"error": "No runs found"}
            run_name = runs[0].name  # Latest first
        
        run = self._dataplex_client.get_data_scan_run(name=run_name)
        
        # Parse results
        return self._parse_scan_results(run)
    
    def _parse_scan_results(self, run: dataplex_v1.DataScanRun) -> Dict[str, Any]:
        """Parse scan run results into structured format."""
        
        result = {
            "scan_id": run.name.split("/")[-3],
            "run_id": run.name.split("/")[-1],
            "state": run.state.name,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "rules_passed": 0,
            "rules_failed": 0,
            "rules_total": 0,
            "rule_results": [],
            "summary": {},
        }
        
        if run.result and run.result.data_quality_result:
            dq_result = run.result.data_quality_result
            
            for rule_result in dq_result.rule_results:
                passed = rule_result.passed
                result["rules_total"] += 1
                if passed:
                    result["rules_passed"] += 1
                else:
                    result["rules_failed"] += 1
                
                result["rule_results"].append({
                    "rule_id": rule_result.rule_id,
                    "rule_name": rule_result.rule_name,
                    "passed": passed,
                    "rows_scanned": rule_result.rows_scanned,
                    "rows_passed": rule_result.rows_passed,
                    "rows_failed": rule_result.rows_failed,
                    "pass_percentage": rule_result.pass_percentage,
                    "threshold": rule_result.threshold,
                })
            
            # Summary
            result["summary"] = {
                "total_rows_scanned": dq_result.rows_scanned,
                "overall_pass_percentage": dq_result.pass_percentage,
                "dimensions": self._aggregate_by_dimension(result["rule_results"]),
            }
        
        return result
    
    def _aggregate_by_dimension(self, rule_results: List[Dict]) -> Dict[str, Dict]:
        """Aggregate results by quality dimension."""
        dimensions = {}
        for rr in rule_results:
            # Dimension is in labels (would need to fetch rule metadata)
            # Simplified: infer from rule_id prefix
            dim = rr["rule_id"].split("_")[0].upper()
            if dim not in dimensions:
                dimensions[dim] = {"passed": 0, "failed": 0, "total": 0}
            dimensions[dim]["total"] += 1
            if rr["passed"]:
                dimensions[dim]["passed"] += 1
            else:
                dimensions[dim]["failed"] += 1
        return dimensions
    
    # ─── Policy Tags & Taxonomy ──────────────────────────────────────────
    
    def create_policy_taxonomy(
        self,
        taxonomy_id: str,
        display_name: str,
        policy_tags: List[Dict[str, Any]],
        description: str = "",
    ) -> dataplex_v1.PolicyTagTaxonomy:
        """Create policy tag taxonomy for column-level access control."""
        
        taxonomy = dataplex_v1.PolicyTagTaxonomy()
        taxonomy.name = f"{self.parent}/policyTagTaxonomies/{taxonomy_id}"
        taxonomy.display_name = display_name
        taxonomy.description = description
        
        # Policy tags are created separately via Data Catalog API
        # This creates the taxonomy container
        
        request = dataplex_v1.CreatePolicyTagTaxonomyRequest(
            parent=self.parent,
            policy_tag_taxonomy_id=taxonomy_id,
            policy_tag_taxonomy=taxonomy,
        )
        
        try:
            operation = self._catalog_client.create_policy_tag_taxonomy(request=request)
            return operation.result(timeout=300)
        except gcp_exceptions.AlreadyExists:
            print(f"Taxonomy {taxonomy_id} already exists")
            return self._catalog_client.get_policy_tag_taxonomy(name=taxonomy.name)
    
    def apply_policy_tags_to_table(
        self,
        table_fqn: str,  # project.dataset.table
        column_policy_tags: Dict[str, str],  # column -> policy_tag_name
    ) -> None:
        """Apply policy tags to BigQuery table columns."""
        
        table = self._bq_client.get_table(table_fqn)
        schema = list(table.schema)
        
        updated = False
        for field in schema:
            if field.name in column_policy_tags:
                field.policy_tags = bigquery.SchemaFieldPolicyTags(
                    names=[column_policy_tags[field.name]]
                )
                updated = True
        
        if updated:
            table.schema = schema
            self._bq_client.update_table(table, ["schema"])
            print(f"Applied policy tags to {table_fqn}")
        else:
            print(f"No matching columns found in {table_fqn}")
    
    # ─── Lineage ─────────────────────────────────────────────────────────
    
    def get_table_lineage(
        self,
        table_fqn: str,
        direction: str = "BOTH",  # UPSTREAM, DOWNSTREAM, BOTH
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """Extract lineage for a BigQuery table."""
        
        # Dataplex lineage API
        from google.cloud.dataplex_v1 import LineageClient
        
        lineage_client = LineageClient()
        process_name = f"projects/{self.project_id}/locations/{self.location}/processes/bigquery"
        
        # Search lineage events
        from google.cloud.dataplex_v1.types import SearchLineageRequest
        
        request = SearchLineageRequest(
            process=process_name,
            target=f"bigquery:{table_fqn}",
            direction=direction,
        )
        
        # Note: Full lineage extraction requires multiple API calls
        # This is a simplified version
        return {
            "table": table_fqn,
            "direction": direction,
            "max_depth": max_depth,
            "note": "Full implementation requires recursive SearchLineage calls",
        }
    
    # ─── Compliance Reporting ────────────────────────────────────────────
    
    def generate_compliance_report(
        self,
        scan_ids: List[str],
        regulations: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate compliance report from scan results."""
        
        regulations = regulations or ["SOX", "GDPR", "HIPAA", "MAS-TRM", "PCI-DSS"]
        
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_id": self.project_id,
            "location": self.location,
            "scans_analyzed": len(scan_ids),
            "regulations": regulations,
            "summary": {
                "total_rules": 0,
                "passed": 0,
                "failed": 0,
                "critical_failures": 0,
                "by_regulation": {},
                "by_dimension": {},
            },
            "details": [],
        }
        
        for scan_id in scan_ids:
            results = self.get_scan_results(scan_id)
            if "error" in results:
                continue
            
            report["details"].append(results)
            report["summary"]["total_rules"] += results["rules_total"]
            report["summary"]["passed"] += results["rules_passed"]
            report["summary"]["failed"] += results["rules_failed"]
            
            # Aggregate by regulation (from rule tags)
            for rr in results["rule_results"]:
                # Would need to fetch rule metadata for tags
                # Simplified: infer from rule_id
                pass
        
        # Calculate pass rate
        if report["summary"]["total_rules"] > 0:
            report["summary"]["pass_rate"] = (
                report["summary"]["passed"] / report["summary"]["total_rules"]
            )
        else:
            report["summary"]["pass_rate"] = 0.0
        
        return report
    
    # ─── CI/CD Integration ───────────────────────────────────────────────
    
    def export_scan_config(self, scan_id: str) -> Dict[str, Any]:
        """Export scan configuration as JSON for version control."""
        
        scan_name = f"{self.parent}/dataScans/{scan_id}"
        scan = self._dataplex_client.get_data_scan(name=scan_name)
        
        config = {
            "scan_id": scan_id,
            "description": scan.description,
            "labels": dict(scan.labels),
            "data_source": scan.data.resource if scan.data else None,
            "schedule": scan.schedule.cron if scan.schedule else None,
            "rules": [],
        }
        
        if scan.data_quality_spec:
            for rule in scan.data_quality_spec.rules:
                config["rules"].append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "type": "ROW_CONDITION" if rule.row_condition else "SET_CONDITION" if rule.set_condition else "SQL",
                    "expression": rule.row_condition.expression if rule.row_condition else 
                                  rule.set_condition.expression if rule.set_condition else
                                  rule.sql if rule.sql else "",
                    "labels": dict(rule.labels),
                })
        
        return config
    
    def deploy_from_config(self, config: Dict[str, Any]) -> dataplex_v1.DataScan:
        """Deploy scan from version-controlled config."""
        
        rules = []
        for r in config.get("rules", []):
            rule_type = RuleType(r["type"])
            if rule_type == RuleType.ROW_CONDITION:
                expr = r["expression"]
            elif rule_type == RuleType.SET_CONDITION:
                expr = r["expression"]
            else:
                expr = r["expression"]
            
            rules.append(QualityRule(
                rule_id=r["rule_id"],
                name=r["name"],
                dimension=QualityDimension(r["labels"].get("quality_dimension", "VALIDITY")),
                rule_type=rule_type,
                expression=expr,
                description=r.get("description", ""),
                threshold=float(r["labels"].get("threshold", "0.95")),
                tags=r.get("labels", {}),
            ))
        
        return self.create_data_quality_scan(
            scan_id=config["scan_id"],
            data_source=config["data_source"],
            rules=rules,
            schedule=config.get("schedule"),
            description=config.get("description", ""),
            labels=config.get("labels"),
        )


# ─── DLP Integration for PII Detection ────────────────────────────────────

class DLPScanner:
    """Wrapper for Cloud DLP inspection jobs."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = dlp_v2.DlpServiceClient()
    
    def create_inspect_template(
        self,
        template_id: str,
        info_types: List[str] = None,
        min_likelihood: str = "POSSIBLE",
    ) -> dlp_v2.InspectTemplate:
        """Create reusable DLP inspect template."""
        
        info_types = info_types or [
            "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD_NUMBER",
            "US_SOCIAL_SECURITY_NUMBER", "PERSON_NAME", "LOCATION",
            "IBAN_CODE", "SWIFT_CODE", "PASSPORT", "DRIVERS_LICENSE",
        ]
        
        inspect_config = dlp_v2.InspectConfig(
            info_types=[{"name": it} for it in info_types],
            min_likelihood=getattr(dlp_v2.Likelihood, min_likelihood),
            include_quote=True,
            limits=dlp_v2.InspectConfig.FindingLimits(max_findings_per_item=100),
        )
        
        template = dlp_v2.InspectTemplate(
            inspect_config=inspect_config,
            display_name=f"DLP Template: {template_id}",
        )
        
        parent = f"projects/{self.project_id}"
        request = dlp_v2.CreateInspectTemplateRequest(
            parent=parent,
            inspect_template=template,
            template_id=template_id,
        )
        
        try:
            return self.client.create_inspect_template(request=request)
        except gcp_exceptions.AlreadyExists:
            return self.client.get_inspect_template(name=f"{parent}/inspectTemplates/{template_id}")
    
    def inspect_bigquery_table(
        self,
        table_fqn: str,
        template_name: str,
        sample_rows: int = 10000,
    ) -> Dict[str, Any]:
        """Run DLP inspection on BigQuery table."""
        
        # Configure BigQuery source
        bigquery_options = dlp_v2.BigQueryOptions(
            table_reference=dlp_v2.BigQueryTable(
                project_id=table_fqn.split(".")[0],
                dataset_id=table_fqn.split(".")[1],
                table_id=table_fqn.split(".")[2],
            ),
            sample_method=dlp_v2.BigQueryOptions.SampleMethod.TOP,
            rows_limit=sample_rows,
        )
        
        storage_config = dlp_v2.StorageConfig(
            big_query_options=bigquery_options,
        )
        
        # Create inspect job
        inspect_job = dlp_v2.InspectJob(
            inspect_template_name=template_name,
            storage_config=storage_config,
            actions=[
                dlp_v2.Action(
                    save_findings=dlp_v2.Action.SaveFindings(
                        output_config=dlp_v2.OutputStorageConfig(
                            table=dlp_v2.BigQueryTable(
                                project_id=self.project_id,
                                dataset_id="dlp_findings",
                                table_id=f"findings_{int(time.time())}",
                            )
                        )
                    )
                )
            ],
        )
        
        parent = f"projects/{self.project_id}"
        request = dlp_v2.CreateDlpJobRequest(
            parent=parent,
            inspect_job=inspect_job,
        )
        
        job = self.client.create_dlp_job(request=request)
        print(f"Started DLP job: {job.name}")
        
        # Wait for completion (in production, use async polling)
        job = self.client.get_dlp_job(name=job.name)
        while job.state not in (dlp_v2.DlpJob.JobState.DONE, dlp_v2.DlpJob.JobState.FAILED):
            time.sleep(30)
            job = self.client.get_dlp_job(name=job.name)
        
        if job.state == dlp_v2.DlpJob.JobState.FAILED:
            return {"error": job.error.message if job.error else "Unknown error"}
        
        # Parse findings
        return self._parse_findings(job)
    
    def _parse_findings(self, job: dlp_v2.DlpJob) -> Dict[str, Any]:
        """Parse DLP findings into structured format."""
        
        findings_by_type = {}
        total_findings = 0
        
        for finding in job.inspect_details.result.findings:
            info_type = finding.info_type.name
            if info_type not in findings_by_type:
                findings_by_type[info_type] = 0
            findings_by_type[info_type] += 1
            total_findings += 1
        
        return {
            "job_name": job.name,
            "state": job.state.name,
            "total_findings": total_findings,
            "findings_by_type": findings_by_type,
            "create_time": job.create_time.isoformat() if job.create_time else None,
            "end_time": job.end_time.isoformat() if job.end_time else None,
        }


# ─── Main: CI/CD Pipeline Example ────────────────────────────────────────

def main():
    """Example: Deploy governance from config files."""
    
    import argparse
    import yaml
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Deploy Dataplex governance from config")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--location", default="asia-southeast1", help="GCP location")
    parser.add_argument("--config-dir", required=True, help="Directory with YAML configs")
    parser.add_argument("--action", choices=["deploy", "export", "report"], default="deploy")
    args = parser.parse_args()
    
    client = DataplexGovernanceClient(args.project, args.location)
    config_dir = Path(args.config_dir)
    
    if args.action == "deploy":
        for config_file in config_dir.glob("*.yaml"):
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            if config.get("type") == "data_quality_scan":
                print(f"Deploying scan: {config['scan_id']}")
                client.deploy_from_config(config)
    
    elif args.action == "export":
        # Export all scans to config files
        scans = list(client._dataplex_client.list_data_scans(parent=client.parent))
        for scan in scans:
            scan_id = scan.name.split("/")[-1]
            config = client.export_scan_config(scan_id)
            output_file = config_dir / f"{scan_id}.yaml"
            with open(output_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            print(f"Exported: {output_file}")
    
    elif args.action == "report":
        scans = list(client._dataplex_client.list_data_scans(parent=client.parent))
        scan_ids = [s.name.split("/")[-1] for s in scans]
        report = client.generate_compliance_report(scan_ids)
        
        output_file = config_dir / f"compliance_report_{int(time.time())}.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Compliance report: {output_file}")
        print(f"Pass rate: {report['summary'].get('pass_rate', 0):.2%}")


if __name__ == "__main__":
    main()
```

---

## 📋 Example YAML Config (Version Controlled)

```yaml
# governance-configs/scan_events_curated.yaml

type: "data_quality_scan"
scan_id: "events-curated-quality"
description: "Quality scan for curated events table"
labels:
  domain: "analytics"
  environment: "prod"
  team: "data-engineering"
  managed-by: "governance-as-code"

data_source: "projects/my-project/datasets/curated/tables/events_partitioned"
schedule: "0 6 * * *"  # Daily 6 AM UTC

rules:
  - rule_id: "completeness_event_id_not_null"
    name: "Event ID completeness"
    dimension: "COMPLETENESS"
    type: "ROW_CONDITION"
    expression: "event_id IS NOT NULL"
    description: "Event ID must not be null"
    labels:
      quality_dimension: "COMPLETENESS"
      threshold: "0.999"
      severity: "critical"
      category: "completeness"

  - rule_id: "validity_amount_positive"
    name: "Amount positive"
    dimension: "VALIDITY"
    type: "ROW_CONDITION"
    expression: "amount IS NULL OR amount >= 0"
    description: "Transaction amount must be non-negative"
    labels:
      quality_dimension: "VALIDITY"
      threshold: "1.0"
      severity: "critical"
      category: "validity"

  - rule_id: "uniqueness_event_id_unique"
    name: "Event ID uniqueness"
    dimension: "UNIQUENESS"
    type: "SET_CONDITION"
    expression: "COUNT(DISTINCT event_id) / COUNT(*) >= 0.999"
    description: "Event ID must be unique"
    labels:
      quality_dimension: "UNIQUENESS"
      threshold: "0.999"
      severity: "critical"
      category: "uniqueness"

  - rule_id: "timeliness_event_dt_freshness"
    name: "Data freshness"
    dimension: "TIMELINESS"
    type: "SQL"
    expression: |
      SELECT 
        CASE 
          WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(event_dt), SECOND) <= 3600
          THEN 1.0 ELSE 0.0 
        END as freshness_score
      FROM `{{table_fqn}}`
    description: "Data should be fresher than 1 hour"
    labels:
      quality_dimension: "TIMELINESS"
      threshold: "1.0"
      severity: "warning"
      category: "timeliness"
```

---

## 🎯 Interview Talking Points

### "How do you implement governance as code with Dataplex?"

1. **Version-Controlled Rules** — Quality rules defined in YAML/JSON, deployed via CI/CD pipeline
2. **Automated Deployment** — `DataplexGovernanceClient.deploy_from_config()` creates/updates scans
3. **Policy Tags as Code** — Taxonomy and column mappings in config, applied programmatically
4. **Compliance Reporting** — Automated report generation from scan results, mapped to regulations
5. **DLP Integration** — PII detection as part of governance pipeline, findings stored for audit

### "How do you handle schema evolution in quality rules?"

1. **Rule Generation from Schema** — `get_standard_quality_rules(table_schema)` auto-generates rules
2. **CI/CD Gate** — On schema change (BigQuery DDL), pipeline regenerates rules and validates
3. **Backward Compatibility** — New columns get default rules; removed columns flagged for rule cleanup
4. **Rule Versioning** — Each rule has `rule_id` with semantic versioning (`v1_completeness_event_id`)

### "How do you scale quality scans across 1000+ tables?"

1. **Template Scans** — Parameterized scan configs (table pattern, rule set) deployed per domain
2. **Domain Rule Sets** — Financial, Healthcare, Marketing rule libraries reused
3. **Incremental Scans** — Partition-level scanning for large tables (Dataplex supports partition filters)
4. **Parallel Execution** — Multiple scan jobs triggered concurrently via Cloud Scheduler/Workflows
5. **Cost Control** — Sampling for exploratory scans (`TABLESAMPLE SYSTEM (10 PERCENT)`), full scans for critical

### "What's your approach to column-level security?"

1. **Policy Tag Taxonomy** — Hierarchical tags: `PII > Email`, `PII > SSN`, `PCI > CreditCard`, `MAS-TRM > CustomerData`
2. **IAM Conditions** — `resource.matchTag('projects/proj/locations/loc/taxonomies/tax/policyTags/tag')`
3. **Automated Application** — DLP scan → detect PII columns → apply policy tags → update BigQuery schema
4. **Access Requests** — Data stewards approve via workflow; IAM bindings updated via script

---

## 📋 Production Checklist

- [ ] **CI/CD Pipeline** — GitHub Actions / Cloud Build: validate YAML → deploy to dev → integration test → prod
- [ ] **IAM** — Service account: `dataplex.admin`, `dlp.jobs.create`, `bigquery.tables.update`, `datacatalog.taxonomies.update`
- [ ] **VPC-SC** — Dataplex, DLP, BigQuery, Data Catalog in perimeter
- [ ] **Monitoring** — Alert on: scan failure rate > 5%, pass rate < 90%, critical rule failure
- [ ] **Cost Control** — Scan sampling for large tables, schedule off-peak, partition filters
- [ ] **Runbooks** — Scan failure investigation, rule threshold tuning, policy tag emergency removal
- [ ] **Documentation** — Rule catalog (Confluence), taxonomy hierarchy, compliance mapping matrix