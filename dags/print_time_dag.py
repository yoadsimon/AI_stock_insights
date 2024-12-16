from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
import pendulum


def print_current_time():
    print("##########")
    print(f"Current time is: {pendulum.now('US/Eastern')}")
    print("##########")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

local_tz = pendulum.timezone('US/Eastern')

with DAG(
        'print_time_dag',
        default_args=default_args,
        description='A simple DAG that prints the current time',
        schedule='47 9 * * *',  # Run every day at 9:30 AM EST
        start_date=pendulum.datetime(2024, 1, 1, tz=local_tz),
        catchup=False,
) as dag:
    print_time_task = PythonOperator(
        task_id='print_time',
        python_callable=print_current_time,
    )
