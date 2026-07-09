from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='refresh_retail_warehouse',
    default_args=default_args,
    description='Daily refresh of the RetailWarehouse Star Schema',
    start_date=datetime(2026, 7, 1),
    schedule_interval='0 2 * * *',  # كل يوم الساعة 2 صباحًا
    catchup=False,
    tags=['retail', 'warehouse', 'milestone4'],
) as dag:

    refresh_task = MsSqlOperator(
        task_id='run_sp_refresh_warehouse',
        mssql_conn_id='retail_warehouse_conn',
        sql='EXEC sp_RefreshWarehouse;',
    )

    refresh_task