"""Airflow DAG for Snowflake Intelligence Scheduled Alerts."""

from datetime import datetime, timedelta

from airflow import DAG
from infra.common import airflow_slack_alerts
from metro.operators.snowflake import SnowflakeK8sPodOperator

DEFAULT_ARGS = {
    "owner": "zblackwood",
    "image": "automated_emails:latest",
    "image_pull_policy": "Always",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 15),
    "email": [
        "zachary.blackwood@snowflake.com",
        "tyler.richards@snowflake.com",
    ],
    "email_on_failure": True,
    "email_on_retry": False,
    "execution_timeout": timedelta(hours=2),
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
    "on_failure_callback": airflow_slack_alerts.task_fail_slack_alert,
    "executor_config": {
        "shout": timedelta(minutes=120),
        "shout_interval": timedelta(minutes=60),
    },
    # `env_vars` provides environment variables to pods run by the SnowflakeK8sPodOperator.
    # This is used to expose the DAG/Task ids to the `query_comment` macro, which adds the
    # DAG/Task id as part of the query comment. This allows the query to be mapped to the
    # DAG/Task that triggered it. The ENV variable names must match the macro exactly.
    # DO NOT change them.
    "env_vars": {
        "DBT_ENV_CUSTOM_ENV_AIRFLOW_DAG_ID": "{{ task_instance.dag_id }}",
        "DBT_ENV_CUSTOM_ENV_AIRFLOW_TASK_ID": "{{ task_instance.task_id }}",
    },
}

with DAG(
    "snowflake_intelligence_alerts",
    schedule="0 15 * * *",  # Daily at 8am PST (16:00 UTC)
    tags=["product", "alerts", "snowflake_intelligence"],
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    catchup=False,
    description="Process and send Snowflake Intelligence scheduled alerts daily",
) as dag:
    process_alerts = SnowflakeK8sPodOperator(
        task_id="process_snowflake_intelligence_alerts",
        bash_command="python snowflake_intelligence_alerts.py",
        execution_timeout=timedelta(hours=2),
    )

    process_alerts
