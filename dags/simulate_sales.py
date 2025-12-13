from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from src.datagen.generate_data import main as generate_data

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'retries': 0,
}

with DAG(
    'simulate_sales_activity',
    default_args=default_args,
    description='Generates random sales data in Postgres to simulate live traffic',
    schedule='*/5 * * * *', # Every 5 minutes
    catchup=False,
    tags=['simulation', 'datagen']
) as dag:

    t_generate = PythonOperator(
        task_id='generate_random_transactions',
        python_callable=generate_data
    )
