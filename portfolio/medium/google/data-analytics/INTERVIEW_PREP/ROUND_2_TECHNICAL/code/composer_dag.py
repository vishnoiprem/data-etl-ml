#!/usr/bin/env python3
"""
Composer DAG - Data Pipeline Orchestration with Best Practices
Interview-ready implementation demonstrating:
- Idempotent task design
- Retry policies with exponential backoff
- SLA monitoring
- Data quality gates
- Parameterized runs
- Alerting integration
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.dataflow import DataflowStartFlexTemplateOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
import json


# Default arguments for all tasks
DEFAULT_ARGS = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(hours=1),
    'sla': timedelta(hours=4),  # Overall DAG SLA
    'execution_timeout': timedelta(hours=3),
}

# DAG Configuration
DAG_ID = 'daily_customer_360_pipeline'
PROJECT_ID = '{{ var.value.gcp_project }}'
REGION = '{{ var.value.gcp_region }}'
GCS_BUCKET = '{{ var.value.data_bucket }}'
BQ_DATASET = '{{ var.value.bq_dataset }}'
DATAFLOW_TEMPLATE_GCS_PATH = f'gs://{GCS_BUCKET}/templates'
COMPOSER_BUCKET = '{{ var.value.composer_bucket }}'


def validate_data_quality(**context):
    """Data quality validation using Great Expectations or custom SQL."""
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT_ID)
    ds = context['ds']  # Execution date in YYYY-MM-DD

    # Quality checks
    checks = [
        {
            'name': 'row_count_check',
            'query': f'''
                SELECT COUNT(*) as cnt
                FROM `{PROJECT_ID}.{BQ_DATASET}.customer_360`
                WHERE DATE(last_activity_ts) = "{ds}"
            ''',
            'min_value': 1,
            'description': 'At least 1 row for the date'
        },
        {
            'name': 'null_customer_id_check',
            'query': f'''
                SELECT COUNT(*) as cnt
                FROM `{PROJECT_ID}.{BQ_DATASET}.customer_360`
                WHERE DATE(last_activity_ts) = "{ds}"
                  AND customer_id IS NULL
            ''',
            'max_value': 0,
            'description': 'No null customer_ids'
        },
        {
            'name': 'revenue_non_negative_check',
            'query': f'''
                SELECT COUNT(*) as cnt
                FROM `{PROJECT_ID}.{BQ_DATASET}.customer_360`
                WHERE DATE(last_activity_ts) = "{ds}"
                  AND lifetime_revenue < 0
            ''',
            'max_value': 0,
            'description': 'No negative revenue'
        },
        {
            'name': 'freshness_check',
            'query': f'''
                SELECT MAX(DATE(last_activity_ts)) as max_date
                FROM `{PROJECT_ID}.{BQ_DATASET}.customer_360`
            ''',
            'custom_check': lambda row: (datetime.strptime(ds, '%Y-%m-%d').date() - row.max_date).days <= 1,
            'description': 'Data no older than 1 day'
        }
    ]

    results = []
    for check in checks:
        try:
            job = client.query(check['query'])
            row = list(job.result())[0]

            if 'custom_check' in check:
                passed = check['custom_check'](row)
            elif 'min_value' in check:
                passed = getattr(row, list(row.keys())[0]) >= check['min_value']
            elif 'max_value' in check:
                passed = getattr(row, list(row.keys())[0]) <= check['max_value']
            else:
                passed = False

            results.append({
                'check': check['name'],
                'passed': passed,
                'value': getattr(row, list(row.keys())[0]),
                'description': check['description']
            })

            if not passed:
                raise ValueError(f"Quality check failed: {check['name']} - {check['description']}")

        except Exception as e:
            results.append({
                'check': check['name'],
                'passed': False,
                'error': str(e)
            })
            raise

    # Push results to XCom for downstream tasks
    context['ti'].xcom_push(key='quality_results', value=results)
    return results


def send_success_notification(**context):
    """Send success notification with metrics."""
    ds = context['ds']
    quality_results = context['ti'].xcom_pull(key='quality_results', task_ids='validate_data_quality')

    message = f"""
    ✅ *Pipeline Success: {DAG_ID}*
    *Date:* {ds}
    *Quality Checks:* {len([r for r in quality_results if r['passed']])}/{len(quality_results)} passed
    *Duration:* {{ context['ti'].duration }} seconds
    """

    # In production: send to Slack, PagerDuty, email
    print(message)
    return message


def send_failure_alert(context):
    """Failure callback for alerting."""
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['execution_date']
    exception = context.get('exception')

    message = f"""
    🚨 *Pipeline Failure: {dag_id}*
    *Task:* {task_id}
    *Execution:* {execution_date}
    *Error:* {exception}
    *Log URL:* {context['task_instance'].log_url}
    """

    # In production: send to Slack, PagerDuty, email
    print(message)
    return message


# DAG Definition
with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description='Daily Customer 360 Pipeline: Extract → Transform → Load → Validate',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Prevent concurrent runs
    concurrency=10,  # Max concurrent tasks
    tags=['customer-360', 'daily', 'production', 'data-engineering'],
    on_failure_callback=send_failure_alert,
    params={
        'backfill_date': None,  # Optional manual backfill date
        'skip_extract': False,  # Skip extract for testing
    }
) as dag:

    # =========================================================================
    # TASK GROUP: EXTRACT
    # =========================================================================
    with TaskGroup(group_id='extract', tooltip='Extract data from sources') as extract_group:

        # Wait for source data to land in GCS
        wait_for_orders = GCSObjectExistenceSensor(
            task_id='wait_for_orders',
            bucket=GCS_BUCKET,
            object=f'landing/orders/{{{{ ds }}}}/orders.parquet',
            timeout=3600,  # 1 hour max wait
            poke_interval=300,  # Check every 5 minutes
            mode='reschedule',  # Free up worker slot while waiting
        )

        wait_for_customers = GCSObjectExistenceSensor(
            task_id='wait_for_customers',
            bucket=GCS_BUCKET,
            object=f'landing/customers/{{{{ ds }}}}/customers.parquet',
            timeout=3600,
            poke_interval=300,
            mode='reschedule',
        )

        wait_for_events = GCSObjectExistenceSensor(
            task_id='wait_for_events',
            bucket=GCS_BUCKET,
            object=f'landing/events/{{{{ ds }}}}/events.parquet',
            timeout=3600,
            poke_interval=300,
            mode='reschedule',
        )

        # Dataflow Flex Template: Extract & Validate Orders
        extract_orders = DataflowStartFlexTemplateOperator(
            task_id='extract_orders',
            project_id=PROJECT_ID,
            location=REGION,
            body={
                'launchParameter': {
                    'jobName': f'extract-orders-{{{{ ds_nodash }}}}',
                    'containerSpecGcsPath': f'{DATAFLOW_TEMPLATE_GCS_PATH}/extract-orders.json',
                    'parameters': {
                        'input_path': f'gs://{GCS_BUCKET}/landing/orders/{{{{ ds }}}}/*.parquet',
                        'output_table': f'{PROJECT_ID}:{BQ_DATASET}.stg_orders',
                        'date_partition': '{{ ds }}',
                    },
                    'environment': {
                        'maxWorkers': 20,
                        'machineType': 'n1-standard-4',
                        'serviceAccountEmail': 'dataflow-sa@{{ var.value.gcp_project }}.iam.gserviceaccount.com',
                        'subnetwork': 'regions/{{ var.value.gcp_region }}/subnetworks/dataflow-subnet',
                    }
                }
            },
            # Idempotency: same job name for same date = safe to retry
        )

        # Dataflow Flex Template: Extract & Validate Customers
        extract_customers = DataflowStartFlexTemplateOperator(
            task_id='extract_customers',
            project_id=PROJECT_ID,
            location=REGION,
            body={
                'launchParameter': {
                    'jobName': f'extract-customers-{{{{ ds_nodash }}}}',
                    'containerSpecGcsPath': f'{DATAFLOW_TEMPLATE_GCS_PATH}/extract-customers.json',
                    'parameters': {
                        'input_path': f'gs://{GCS_BUCKET}/landing/customers/{{{{ ds }}}}/*.parquet',
                        'output_table': f'{PROJECT_ID}:{BQ_DATASET}.stg_customers',
                        'date_partition': '{{ ds }}',
                    },
                    'environment': {
                        'maxWorkers': 10,
                        'machineType': 'n1-standard-4',
                    }
                }
            }
        )

        # Dataflow Flex Template: Extract & Validate Events
        extract_events = DataflowStartFlexTemplateOperator(
            task_id='extract_events',
            project_id=PROJECT_ID,
            location=REGION,
            body={
                'launchParameter': {
                    'jobName': f'extract-events-{{{{ ds_nodash }}}}',
                    'containerSpecGcsPath': f'{DATAFLOW_TEMPLATE_GCS_PATH}/extract-events.json',
                    'parameters': {
                        'input_path': f'gs://{GCS_BUCKET}/landing/events/{{{{ ds }}}}/*.parquet',
                        'output_table': f'{PROJECT_ID}:{BQ_DATASET}.stg_events',
                        'date_partition': '{{ ds }}',
                    },
                    'environment': {
                        'maxWorkers': 50,
                        'machineType': 'n1-standard-4',
                        'enableStreamingEngine': False,
                    }
                }
            }
        )

        # Extract dependencies
        [wait_for_orders, wait_for_customers, wait_for_events] >> [extract_orders, extract_customers, extract_events]

    # =========================================================================
    # TASK GROUP: TRANSFORM
    # =========================================================================
    with TaskGroup(group_id='transform', tooltip='Transform and enrich data') as transform_group:

        # dbt models for transformation (run via Dataflow or Cloud Run Job)
        # Here using BigQuery SQL for simplicity - replace with dbt in production

        transform_stg_to_dim = BigQueryInsertJobOperator(
            task_id='transform_stg_to_dim',
            project_id=PROJECT_ID,
            location=REGION,
            configuration={
                'query': {
                    'query': f'''
                        -- Build dim_customer from stg_customers
                        MERGE `{PROJECT_ID}.{BQ_DATASET}.dim_customer` T
                        USING (
                            SELECT
                                customer_id,
                                email,
                                tier,
                                region,
                                segment,
                                signup_date,
                                CURRENT_TIMESTAMP() as updated_ts
                            FROM `{PROJECT_ID}.{BQ_DATASET}.stg_customers`
                            WHERE DATE(_processed_ts) = "{{{{ ds }}}}"
                            QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY _processed_ts DESC) = 1
                        ) S
                        ON T.customer_id = S.customer_id
                        WHEN MATCHED THEN UPDATE SET
                            email = S.email,
                            tier = S.tier,
                            region = S.region,
                            segment = S.segment,
                            updated_ts = S.updated_ts
                        WHEN NOT MATCHED THEN INSERT (
                            customer_id, email, tier, region, segment, signup_date, created_ts, updated_ts
                        ) VALUES (
                            S.customer_id, S.email, S.tier, S.region, S.segment, S.signup_date,
                            CURRENT_TIMESTAMP(), S.updated_ts
                        )
                    ''',
                    'useLegacySql': False,
                },
                'labels': {'pipeline': DAG_ID, 'layer': 'transform'}
            },
            sla=timedelta(hours=1),
        )

        transform_fact_orders = BigQueryInsertJobOperator(
            task_id='transform_fact_orders',
            project_id=PROJECT_ID,
            location=REGION,
            configuration={
                'query': {
                    'query': f'''
                        -- Build fact_orders from stg_orders
                        INSERT INTO `{PROJECT_ID}.{BQ_DATASET}.fact_orders`
                        SELECT
                            order_id,
                            customer_id,
                            product_id,
                            amount,
                            quantity,
                            order_timestamp,
                            status,
                            channel,
                            currency,
                            CURRENT_TIMESTAMP() as _processed_ts
                        FROM `{PROJECT_ID}.{BQ_DATASET}.stg_orders`
                        WHERE DATE(_processed_ts) = "{{{{ ds }}}}"
                          AND order_id NOT IN (
                              SELECT order_id FROM `{PROJECT_ID}.{BQ_DATASET}.fact_orders`
                              WHERE DATE(_processed_ts) = "{{{{ ds }}}}"
                          )  -- Idempotency: avoid duplicates on retry
                    ''',
                    'useLegacySql': False,
                },
                'labels': {'pipeline': DAG_ID, 'layer': 'transform'}
            },
            sla=timedelta(hours=1),
        )

        transform_customer_360 = BigQueryInsertJobOperator(
            task_id='transform_customer_360',
            project_id=PROJECT_ID,
            location=REGION,
            configuration={
                'query': {
                    'query': f'''
                        -- Build customer_360 aggregate table
                        MERGE `{PROJECT_ID}.{BQ_DATASET}.customer_360` T
                        USING (
                            SELECT
                                o.customer_id,
                                c.tier,
                                c.region,
                                c.segment,
                                COUNT(DISTINCT o.order_id) as total_orders,
                                SUM(o.amount) as lifetime_revenue,
                                COUNT(DISTINCT DATE(o.order_timestamp)) as active_days,
                                MIN(o.order_timestamp) as first_order_ts,
                                MAX(o.order_timestamp) as last_order_ts,
                                MAX(o._processed_ts) as last_activity_ts,
                                CURRENT_TIMESTAMP() as updated_ts
                            FROM `{PROJECT_ID}.{BQ_DATASET}.fact_orders` o
                            JOIN `{PROJECT_ID}.{BQ_DATASET}.dim_customer` c
                                ON o.customer_id = c.customer_id
                            WHERE DATE(o._processed_ts) = "{{{{ ds }}}}"
                            GROUP BY 1,2,3,4
                        ) S
                        ON T.customer_id = S.customer_id
                        WHEN MATCHED THEN UPDATE SET
                            total_orders = S.total_orders,
                            lifetime_revenue = S.lifetime_revenue,
                            active_days = S.active_days,
                            last_order_ts = S.last_order_ts,
                            last_activity_ts = S.last_activity_ts,
                            updated_ts = S.updated_ts
                        WHEN NOT MATCHED THEN INSERT (
                            customer_id, tier, region, segment,
                            total_orders, lifetime_revenue, active_days,
                            first_order_ts, last_order_ts, last_activity_ts,
                            created_ts, updated_ts
                        ) VALUES (
                            S.customer_id, S.tier, S.region, S.segment,
                            S.total_orders, S.lifetime_revenue, S.active_days,
                            S.first_order_ts, S.last_order_ts, S.last_activity_ts,
                            CURRENT_TIMESTAMP(), S.updated_ts
                        )
                    ''',
                    'useLegacySql': False,
                },
                'labels': {'pipeline': DAG_ID, 'layer': 'transform'}
            },
            sla=timedelta(hours=1),
        )

        # Transform dependencies
        [transform_stg_to_dim, transform_fact_orders] >> transform_customer_360

    # =========================================================================
    # TASK GROUP: DATA QUALITY
    # =========================================================================
    with TaskGroup(group_id='data_quality', tooltip='Data quality validation') as dq_group:

        validate_data_quality_task = PythonOperator(
            task_id='validate_data_quality',
            python_callable=validate_data_quality,
            provide_context=True,
            sla=timedelta(minutes=30),
        )

        # Great Expectations checkpoint (alternative to custom validation)
        # ge_checkpoint = PythonOperator(
        #     task_id='ge_checkpoint',
        #     python_callable=run_ge_checkpoint,
        #     op_kwargs={'checkpoint_name': 'customer_360_daily'},
        # )

    # =========================================================================
    # TASK GROUP: LOAD / SERVE
    # =========================================================================
    with TaskGroup(group_id='load', tooltip='Load to serving layer') as load_group:

        # Refresh materialized views
        refresh_mvs = BigQueryInsertJobOperator(
            task_id='refresh_materialized_views',
            project_id=PROJECT_ID,
            location=REGION,
            configuration={
                'query': {
                    'query': f'''
                        -- Materialized views auto-refresh, but force refresh for consistency
                        CALL BQ.REFRESH_MATERIALIZED_VIEW('{PROJECT_ID}.{BQ_DATASET}.mv_daily_customer_metrics');
                        CALL BQ.REFRESH_MATERIALIZED_VIEW('{PROJECT_ID}.{BQ_DATASET}.mv_customer_cohorts');
                    ''',
                    'useLegacySql': False,
                }
            },
            sla=timedelta(minutes=15),
        )

        # Export to Looker / Data Studio (if needed)
        # export_to_looker = EmptyOperator(task_id='export_to_looker')

    # =========================================================================
    # SUCCESS NOTIFICATION
    # =========================================================================
    success_notification = PythonOperator(
        task_id='success_notification',
        python_callable=send_success_notification,
        provide_context=True,
        trigger_rule='all_success',
    )

    # =========================================================================
    # DAG FLOW
    # =========================================================================
    (
        extract_group
        >> transform_group
        >> dq_group
        >> load_group
        >> success_notification
    )

    # Task-level dependencies for clarity
    extract_group >> transform_group
    transform_group >> dq_group
    dq_group >> load_group
    load_group >> success_notification


# =============================================================================
# UTILITY FUNCTIONS (for use in other DAGs)
# =============================================================================

def create_dataflow_task(task_id: str, template_name: str, parameters: dict,
                         max_workers: int = 20, machine_type: str = 'n1-standard-4'):
    """Factory function for Dataflow tasks."""
    return DataflowStartFlexTemplateOperator(
        task_id=task_id,
        project_id=PROJECT_ID,
        location=REGION,
        body={
            'launchParameter': {
                'jobName': f'{template_name}-{{{{ ds_nodash }}}}-{{{{ task_instance.try_number }}}}',
                'containerSpecGcsPath': f'{DATAFLOW_TEMPLATE_GCS_PATH}/{template_name}.json',
                'parameters': parameters,
                'environment': {
                    'maxWorkers': max_workers,
                    'machineType': machine_type,
                    'serviceAccountEmail': f'dataflow-sa@{PROJECT_ID}.iam.gserviceaccount.com',
                }
            }
        }
    )


def create_bq_merge_task(task_id: str, target_table: str, source_query: str,
                         merge_keys: list, partition_field: str = None):
    """Factory function for BigQuery MERGE tasks."""
    merge_conditions = ' AND '.join([f'T.{k} = S.{k}' for k in merge_keys])

    # Build UPDATE SET clause (all columns except merge keys)
    update_cols = [f'{k} = S.{k}' for k in merge_keys]  # Simplified

    query = f'''
        MERGE `{PROJECT_ID}.{BQ_DATASET}.{target_table}` T
        USING ({source_query}) S
        ON {merge_conditions}
        WHEN MATCHED THEN UPDATE SET
            {", ".join(update_cols)},
            updated_ts = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT (...)
            VALUES (...)
    '''

    return BigQueryInsertJobOperator(
        task_id=task_id,
        project_id=PROJECT_ID,
        location=REGION,
        configuration={
            'query': {
                'query': query,
                'useLegacySql': False,
            }
        }
    )


# =============================================================================
# TESTING HELPERS
# =============================================================================

if __name__ == '__main__':
    # Test DAG parsing
    print(f"DAG '{DAG_ID}' parsed successfully")
    print(f"Tasks: {len(dag.tasks)}")
    for task in dag.tasks:
        print(f"  - {task.task_id} ({type(task).__name__})")