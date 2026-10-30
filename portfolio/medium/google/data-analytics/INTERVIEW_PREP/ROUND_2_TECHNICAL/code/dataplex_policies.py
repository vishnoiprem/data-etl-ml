#!/usr/bin/env python3
"""
Dataplex Policies & Governance Automation
Interview-ready implementation demonstrating:
- Lake/Zone/Asset creation
- Policy tag taxonomy management
- Data quality scan automation
- Data lineage extraction
- Glossary management
"""

from google.cloud import dataplex_v1
from google.cloud import datacatalog_v1
from google.cloud import dlp_v2
from google.api_core import operation
import json
from typing import Dict, List, Optional
from datetime import datetime


class DataplexManager:
    """Manage Dataplex resources for data governance."""

    def __init__(self, project_id: str, location: str = 'us-central1'):
        self.project_id = project_id
        self.location = location
        self.dataplex_client = dataplex_v1.DataplexServiceClient()
        self.catalog_client = datacatalog_v1.DataCatalogClient()
        self.dlp_client = dlp_v2.DlpServiceClient()

    # =========================================================================
    # LAKE / ZONE / ASSET MANAGEMENT
    # =========================================================================

    def create_lake(self, lake_id: str, display_name: str, description: str = "") -> dataplex_v1.Lake:
        """Create a Dataplex Lake."""
        parent = f"projects/{self.project_id}/locations/{self.location}"

        lake = dataplex_v1.Lake(
            display_name=display_name,
            description=description,
            labels={"environment": "prod", "managed-by": "terraform"},
            metastore_status=dataplex_v1.Lake.MetastoreStatus(
                endpoint="",
                state=dataplex_v1.Lake.MetastoreStatus.State.ACTIVE
            )
        )

        request = dataplex_v1.CreateLakeRequest(
            parent=parent,
            lake_id=lake_id,
            lake=lake,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_lake(request=request)
        return operation_future.result()

    def create_raw_zone(self, lake_id: str, zone_id: str, display_name: str) -> dataplex_v1.Zone:
        """Create a RAW zone for landing data."""
        parent = f"projects/{self.project_id}/locations/{self.location}/lakes/{lake_id}"

        zone = dataplex_v1.Zone(
            display_name=display_name,
            type_=dataplex_v1.Zone.Type.RAW,
            resource_spec=dataplex_v1.Zone.ResourceSpec(
                location_type=dataplex_v1.Zone.ResourceSpec.LocationType.MULTI_REGION
            ),
            discovery_spec=dataplex_v1.Zone.DiscoverySpec(
                enabled=True,
                csv_options=dataplex_v1.Zone.DiscoverySpec.CsvOptions(
                    disable_type_inference=False,
                    require_header_row=True
                ),
                json_options=dataplex_v1.Zone.DiscoverySpec.JsonOptions(
                    disable_type_inference=False
                ),
                schedule="0 6 * * *"  # Daily 6 AM UTC
            ),
            labels={"zone-type": "raw"}
        )

        request = dataplex_v1.CreateZoneRequest(
            parent=parent,
            zone_id=zone_id,
            zone=zone,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_zone(request=request)
        return operation_future.result()

    def create_curated_zone(self, lake_id: str, zone_id: str, display_name: str) -> dataplex_v1.Zone:
        """Create a CURATED zone for processed/serving data."""
        parent = f"projects/{self.project_id}/locations/{self.location}/lakes/{lake_id}"

        zone = dataplex_v1.Zone(
            display_name=display_name,
            type_=dataplex_v1.Zone.Type.CURATED,
            resource_spec=dataplex_v1.Zone.ResourceSpec(
                location_type=dataplex_v1.Zone.ResourceSpec.LocationType.MULTI_REGION
            ),
            discovery_spec=dataplex_v1.Zone.DiscoverySpec(
                enabled=True,
                schedule="0 6 * * *"
            ),
            labels={"zone-type": "curated"}
        )

        request = dataplex_v1.CreateZoneRequest(
            parent=parent,
            zone_id=zone_id,
            zone=zone,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_zone(request=request)
        return operation_future.result()

    def attach_gcs_asset(self, lake_id: str, zone_id: str, asset_id: str,
                         gcs_path: str, display_name: str) -> dataplex_v1.Asset:
        """Attach GCS bucket as asset to zone."""
        parent = f"projects/{self.project_id}/locations/{self.location}/lakes/{lake_id}/zones/{zone_id}"

        asset = dataplex_v1.Asset(
            display_name=display_name,
            resource_spec=dataplex_v1.Asset.ResourceSpec(
                name=f"//storage.googleapis.com/{gcs_path.replace('gs://', '')}",
                type_=dataplex_v1.Asset.ResourceSpec.Type.STORAGE_BUCKET,
                read_access_mode=dataplex_v1.Asset.ResourceSpec.AccessMode.READ_ONLY
            ),
            discovery_spec=dataplex_v1.Asset.DiscoverySpec(
                enabled=True,
                csv_options=dataplex_v1.Asset.DiscoverySpec.CsvOptions(
                    disable_type_inference=False,
                    require_header_row=True
                )
            ),
            labels={"source": "gcs"}
        )

        request = dataplex_v1.CreateAssetRequest(
            parent=parent,
            asset_id=asset_id,
            asset=asset,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_asset(request=request)
        return operation_future.result()

    def attach_bigquery_asset(self, lake_id: str, zone_id: str, asset_id: str,
                              dataset_id: str, display_name: str) -> dataplex_v1.Asset:
        """Attach BigQuery dataset as asset to zone."""
        parent = f"projects/{self.project_id}/locations/{self.location}/lakes/{lake_id}/zones/{zone_id}"

        asset = dataplex_v1.Asset(
            display_name=display_name,
            resource_spec=dataplex_v1.Asset.ResourceSpec(
                name=f"//bigquery.googleapis.com/projects/{self.project_id}/datasets/{dataset_id}",
                type_=dataplex_v1.Asset.ResourceSpec.Type.BIGQUERY_DATASET,
                read_access_mode=dataplex_v1.Asset.ResourceSpec.AccessMode.READ_WRITE
            ),
            discovery_spec=dataplex_v1.Asset.DiscoverySpec(
                enabled=True
            ),
            labels={"source": "bigquery"}
        )

        request = dataplex_v1.CreateAssetRequest(
            parent=parent,
            asset_id=asset_id,
            asset=asset,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_asset(request=request)
        return operation_future.result()

    # =========================================================================
    # POLICY TAG TAXONOMY MANAGEMENT
    # =========================================================================

    def create_policy_tag_taxonomy(self, taxonomy_id: str, display_name: str,
                                   description: str, policy_tags: List[Dict]) -> datacatalog_v1.Taxonomy:
        """Create policy tag taxonomy with hierarchical tags."""
        parent = f"projects/{self.project_id}/locations/{self.location}"

        # Build policy tags hierarchy
        policy_tag_objects = []
        for tag_def in policy_tags:
            policy_tag = datacatalog_v1.PolicyTag(
                display_name=tag_def['display_name'],
                description=tag_def.get('description', ''),
                parent_policy_tag=tag_def.get('parent_policy_tag', '')
            )
            policy_tag_objects.append(policy_tag)

        taxonomy = datacatalog_v1.Taxonomy(
            display_name=display_name,
            description=description,
            activated_policy_types=[datacatalog_v1.Taxonomy.PolicyType.FINE_GRAINED_ACCESS_CONTROL]
        )

        request = datacatalog_v1.CreateTaxonomyRequest(
            parent=parent,
            taxonomy=taxonomy
        )

        created_taxonomy = self.catalog_client.create_taxonomy(request=request)

        # Create policy tags under taxonomy
        for i, tag_def in enumerate(policy_tags):
            if tag_def.get('parent_policy_tag'):
                parent_tag = tag_def['parent_policy_tag']
            else:
                parent_tag = created_taxonomy.name

            policy_tag = datacatalog_v1.PolicyTag(
                display_name=tag_def['display_name'],
                description=tag_def.get('description', '')
            )

            request = datacatalog_v1.CreatePolicyTagRequest(
                parent=parent_tag,
                policy_tag=policy_tag
            )
            self.catalog_client.create_policy_tag(request=request)

        return created_taxonomy

    # =========================================================================
    # DATA QUALITY SCANS
    # =========================================================================

    def create_data_quality_scan(self, scan_id: str, data_entity: str,
                                 rules: List[Dict], schedule: str = "0 2 * * *") -> dataplex_v1.DataScan:
        """Create automated data quality scan."""
        parent = f"projects/{self.project_id}/locations/{self.location}"

        # Build data quality rules
        dq_rules = []
        for rule in rules:
            dq_rule = dataplex_v1.DataQualityRule()

            if rule['type'] == 'non_null':
                dq_rule.non_null_expectation = dataplex_v1.DataQualityRule.NonNullExpectation()
            elif rule['type'] == 'unique':
                dq_rule.unique_expectation = dataplex_v1.DataQualityRule.UniqueExpectation()
            elif rule['type'] == 'range':
                dq_rule.range_expectation = dataplex_v1.DataQualityRule.RangeExpectation(
                    min_value=rule.get('min'),
                    max_value=rule.get('max')
                )
            elif rule['type'] == 'regex':
                dq_rule.regex_expectation = dataplex_v1.DataQualityRule.RegexExpectation(
                    regex=rule['regex']
                )
            elif rule['type'] == 'set':
                dq_rule.set_expectation = dataplex_v1.DataQualityRule.SetExpectation(
                    values=rule['values']
                )
            elif rule['type'] == 'row_condition':
                dq_rule.row_condition_expectation = dataplex_v1.DataQualityRule.RowConditionExpectation(
                    sql_expression=rule['sql_expression']
                )

            dq_rule.column = rule['column']
            dq_rule.dimension = rule.get('dimension', 'COMPLETENESS')
            dq_rules.append(dq_rule)

        scan = dataplex_v1.DataScan(
            display_name=f"Data Quality Scan: {scan_id}",
            description=f"Automated data quality scan for {data_entity}",
            data=dataplex_v1.DataScan.Data(
                entity=data_entity,
                sampling_percent=100
            ),
            spec=dataplex_v1.DataScan.Spec(
                data_quality_spec=dataplex_v1.DataScan.DataQualitySpec(
                    rules=dq_rules,
                    sampling_percent=100,
                    row_filter=""
                ),
                execution_spec=dataplex_v1.DataScan.ExecutionSpec(
                    trigger=dataplex_v1.Trigger(
                        schedule=dataplex_v1.Trigger.Schedule(
                            cron=schedule,
                            time_zone="UTC"
                        )
                    )
                )
            ),
            labels={"managed-by": "automation", "scan-type": "data-quality"}
        )

        request = dataplex_v1.CreateDataScanRequest(
            parent=parent,
            data_scan_id=scan_id,
            data_scan=scan,
            validate_only=False
        )

        operation_future = self.dataplex_client.create_data_scan(request=request)
        return operation_future.result()

    def get_scan_results(self, scan_id: str) -> Dict:
        """Get latest data quality scan results."""
        scan_name = f"projects/{self.project_id}/locations/{self.location}/dataScans/{scan_id}"

        request = dataplex_v1.GetDataScanRequest(name=scan_name)
        scan = self.dataplex_client.get_data_scan(request=request)

        # Get latest run
        runs = self.dataplex_client.list_data_scan_jobs(
            parent=scan_name,
            filter="state=SUCCEEDED",
            order_by="create_time desc",
            page_size=1
        )

        latest_run = next(iter(runs), None)
        if not latest_run:
            return {"status": "no_runs", "scan": scan_id}

        return {
            "scan_id": scan_id,
            "latest_run": latest_run.name,
            "state": latest_run.state.name,
            "create_time": latest_run.create_time,
            "end_time": latest_run.end_time,
            "data_quality_result": latest_run.data_quality_result
        }

    # =========================================================================
    # DATA LINEAGE
    # =========================================================================

    def get_lineage(self, asset_name: str) -> Dict:
        """Get lineage for an asset."""
        request = dataplex_v1.GetLineageRequest(
            name=f"projects/{self.project_id}/locations/{self.location}/lineageEvents/{asset_name}"
        )

        # Note: Lineage API requires separate setup
        # This is a placeholder for the actual lineage extraction
        return {
            "asset": asset_name,
            "upstream": [],
            "downstream": [],
            "processes": []
        }

    def create_lineage_event(self, source_asset: str, target_asset: str,
                             process_name: str, process_type: str) -> dataplex_v1.LineageEvent:
        """Create custom lineage event."""
        lineage_event = dataplex_v1.LineageEvent(
            source=f"projects/{self.project_id}/locations/{self.location}/assets/{source_asset}",
            target=f"projects/{self.project_id}/locations/{self.location}/assets/{target_asset}",
            process=dataplex_v1.Process(
                name=process_name,
                type_=process_type
            ),
            create_time=datetime.utcnow()
        )

        request = dataplex_v1.CreateLineageEventRequest(
            parent=f"projects/{self.project_id}/locations/{self.location}",
            lineage_event=lineage_event
        )

        return self.dataplex_client.create_lineage_event(request=request)

    # =========================================================================
    # DLP INTEGRATION FOR AUTO-CLASSIFICATION
    # =========================================================================

    def create_dlp_inspect_template(self, template_id: str, display_name: str,
                                    info_types: List[str] = None) -> dlp_v2.InspectTemplate:
        """Create DLP inspect template for auto-classification."""
        parent = f"projects/{self.project_id}/locations/global"

        if info_types is None:
            info_types = [
                'PERSON_NAME', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'US_SSN',
                'CREDIT_CARD_NUMBER', 'IBAN_CODE', 'IP_ADDRESS',
                'DATE_OF_BIRTH', 'GENDER', 'ETHNIC_GROUP'
            ]

        inspect_config = dlp_v2.InspectConfig(
            info_types=[{'name': it} for it in info_types],
            min_likelihood=dlp_v2.Likelihood.POSSIBLE,
            limits=dlp_v2.InspectConfig.FindingLimits(max_findings_per_item=100),
            include_quote=True
        )

        template = dlp_v2.InspectTemplate(
            display_name=display_name,
            description="Auto-classification for Dataplex policy tags",
            inspect_config=inspect_config
        )

        request = dlp_v2.CreateInspectTemplateRequest(
            parent=parent,
            inspect_template=template,
            template_id=template_id
        )

        return self.dlp_client.create_inspect_template(request=request)

    def scan_and_tag_columns(self, project_id: str, dataset_id: str, table_id: str,
                             inspect_template_name: str) -> List[Dict]:
        """Scan BigQuery table with DLP and return suggested policy tags."""
        # This would integrate with Dataplex auto-tagging
        # Placeholder for the actual implementation
        return [
            {"column": "email", "info_type": "EMAIL_ADDRESS", "policy_tag": "PII/EMAIL"},
            {"column": "ssn", "info_type": "US_SSN", "policy_tag": "PII/SSN"},
            {"column": "credit_card", "info_type": "CREDIT_CARD_NUMBER", "policy_tag": "PCI/CREDIT_CARD"}
        ]


# =============================================================================
# POLICY TAG DEFINITIONS (YAML-STYLE for version control)
# =============================================================================

POLICY_TAG_TAXONOMY = {
    "taxonomy_id": "data-classification",
    "display_name": "Data Classification Taxonomy",
    "description": "Enterprise data classification for governance and access control",
    "policy_tags": [
        {"display_name": "PII", "description": "Personally Identifiable Information"},
        {"display_name": "PII/NAME", "description": "Full name", "parent_policy_tag": "PII"},
        {"display_name": "PII/EMAIL", "description": "Email address", "parent_policy_tag": "PII"},
        {"display_name": "PII/PHONE", "description": "Phone number", "parent_policy_tag": "PII"},
        {"display_name": "PII/SSN", "description": "Social Security Number", "parent_policy_tag": "PII"},
        {"display_name": "PII/ADDRESS", "description": "Physical address", "parent_policy_tag": "PII"},
        {"display_name": "PII/DOB", "description": "Date of birth", "parent_policy_tag": "PII"},

        {"display_name": "PCI", "description": "Payment Card Industry data"},
        {"display_name": "PCI/CREDIT_CARD", "description": "Credit card number", "parent_policy_tag": "PCI"},
        {"display_name": "PCI/CARD_EXPIRY", "description": "Card expiration", "parent_policy_tag": "PCI"},
        {"display_name": "PCI/CVV", "description": "CVV code", "parent_policy_tag": "PCI"},

        {"display_name": "PHI", "description": "Protected Health Information"},
        {"display_name": "PHI/PATIENT_ID", "description": "Patient identifier", "parent_policy_tag": "PHI"},
        {"display_name": "PHI/DIAGNOSIS", "description": "Medical diagnosis", "parent_policy_tag": "PHI"},
        {"display_name": "PHI/TREATMENT", "description": "Treatment records", "parent_policy_tag": "PHI"},

        {"display_name": "INTERNAL", "description": "Internal business data"},
        {"display_name": "INTERNAL/EMPLOYEE_ID", "description": "Employee identifier", "parent_policy_tag": "INTERNAL"},
        {"display_name": "INTERNAL/SALARY", "description": "Compensation data", "parent_policy_tag": "INTERNAL"},
        {"display_name": "INTERNAL/REVENUE", "description": "Revenue figures", "parent_policy_tag": "INTERNAL"},

        {"display_name": "PUBLIC", "description": "Publicly shareable data"},
        {"display_name": "PUBLIC/NON_SENSITIVE", "description": "Non-sensitive data", "parent_policy_tag": "PUBLIC"},
    ]
}

DATA_QUALITY_RULES_CUSTOMER = [
    {"column": "customer_id", "type": "non_null", "dimension": "COMPLETENESS"},
    {"column": "customer_id", "type": "unique", "dimension": "UNIQUENESS"},
    {"column": "email", "type": "regex", "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", "dimension": "VALIDITY"},
    {"column": "tier", "type": "set", "values": ["bronze", "silver", "gold", "platinum"], "dimension": "CONSISTENCY"},
    {"column": "signup_date", "type": "row_condition", "sql_expression": "signup_date <= CURRENT_DATE()", "dimension": "ACCURACY"},
    {"column": "lifetime_revenue", "type": "range", "min": "0", "dimension": "VALIDITY"},
]

DATA_QUALITY_RULES_ORDERS = [
    {"column": "order_id", "type": "non_null", "dimension": "COMPLETENESS"},
    {"column": "order_id", "type": "unique", "dimension": "UNIQUENESS"},
    {"column": "customer_id", "type": "non_null", "dimension": "COMPLETENESS"},
    {"column": "amount", "type": "range", "min": "0.01", "dimension": "VALIDITY"},
    {"column": "quantity", "type": "range", "min": "1", "dimension": "VALIDITY"},
    {"column": "status", "type": "set", "values": ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"], "dimension": "CONSISTENCY"},
    {"column": "order_timestamp", "type": "row_condition", "sql_expression": "order_timestamp <= CURRENT_TIMESTAMP()", "dimension": "ACCURACY"},
]


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == '__main__':
    # Example usage
    manager = DataplexManager(project_id="my-project", location="us-central1")

    # 1. Create lake
    # lake = manager.create_lake("enterprise-data-lake", "Enterprise Data Lake")

    # 2. Create zones
    # raw_zone = manager.create_raw_zone("enterprise-data-lake", "raw-zone", "Raw Data Zone")
    # curated_zone = manager.create_curated_zone("enterprise-data-lake", "curated-zone", "Curated Data Zone")

    # 3. Attach assets
    # gcs_asset = manager.attach_gcs_asset("enterprise-data-lake", "raw-zone", "landing-bucket",
    #                                       "landing-bucket", "Landing Zone Bucket")
    # bq_asset = manager.attach_bigquery_asset("enterprise-data-lake", "curated-zone", "analytics-dataset",
    #                                           "analytics", "Analytics Dataset")

    # 4. Create policy tag taxonomy
    # taxonomy = manager.create_policy_tag_taxonomy(
    #     "data-classification", "Data Classification",
    #     "Enterprise data classification", POLICY_TAG_TAXONOMY["policy_tags"]
    # )

    # 5. Create data quality scans
    # customer_scan = manager.create_data_quality_scan(
    #     "customer-daily-quality",
    #     f"projects/my-project/locations/us-central1/lakes/enterprise-data-lake/zones/curated-zone/assets/analytics",
    #     DATA_QUALITY_RULES_CUSTOMER
    # )

    # 6. Create DLP template for auto-classification
    # dlp_template = manager.create_dlp_inspect_template(
    #     "auto-classify-template", "Auto-classification for Dataplex"
    # )

    print("DataplexManager class ready for use")
    print(f"Policy tag taxonomy: {len(POLICY_TAG_TAXONOMY['policy_tags'])} tags defined")
    print(f"Customer DQ rules: {len(DATA_QUALITY_RULES_CUSTOMER)}")
    print(f"Orders DQ rules: {len(DATA_QUALITY_RULES_ORDERS)}")