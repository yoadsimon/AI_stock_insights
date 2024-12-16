from airflow import DAG
from airflow.operators.python import get_current_context, task
import pendulum

from common.execute_daily_stock_analysis import execute_daily_stock_analysis

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'email': ['yoadsimon@gmail.com', 'ai.stockinsights@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
}

local_tz = pendulum.timezone("US/Eastern")

with DAG(
        'daily_stock_analysis',
        default_args=default_args,
        description='Generate stock content and upload to YouTube daily at 9 AM US Eastern Time',
        schedule_interval='0 9 * * *',
        start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
        catchup=False,
        max_active_runs=1,
        concurrency=1,
        tags=['stock', 'youtube'],
) as dag:
    @task(task_id="daily_stock_analysis")
    def daily_stock_analysis():
        context = get_current_context()
        dag_run = context['dag_run']
        stock_symbol = dag_run.conf.get('stock_symbol', "NVDA")
        company_name = dag_run.conf.get('company_name', "NVIDIA Corporation")
        is_mock = dag_run.conf.get('is_mock', True)
        execute_daily_stock_analysis(stock_symbol=stock_symbol, company_name=company_name, is_mock=is_mock)


    run_this = daily_stock_analysis()
