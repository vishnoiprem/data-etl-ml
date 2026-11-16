import datetime

from airflow import models
from airflow.models import Variable
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitSparkSqlJobOperator
from airflow.utils.dates import days_ago

# Configure these as Airflow Variables (Composer > Configuration > Variables),
# or set them with `airflow variables set project_id YOUR_PROJECT_ID`.
project_id = Variable.get('project_id')
region = Variable.get('region')
cluster_name = Variable.get('cluster_name')

default_args = {
    # Tell airflow to start one day ago, so that it runs as soon as you upload it
    "start_date": days_ago(1),
    "project_id": project_id,
    "region": region
}

with models.DAG(
    "spark_sql_demo",
    default_args=default_args,
    schedule_interval=datetime.timedelta(days=1)
) as dag:
    run_query = DataprocSubmitSparkSqlJobOperator(
        project_id=project_id,
        region=region,
        cluster_name=cluster_name,
        query='SELECT current_date',
        task_id='run_spark_sql_query',
    )