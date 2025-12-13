from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add src to sys.path
# Support both .. (sibling) and . (child)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from src.load.sqlserver_loader import SqlServerLoader

def run_load(table_name, **kwargs):
    loader = SqlServerLoader(base_path=os.path.join(os.path.dirname(__file__), '..', 'datalake'))
    loader.process_and_load(table_name)

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'retries': 0,
}

with DAG(
    'process_sales_dw',
    default_args=default_args,
    description='Loads Parquet from Bronze to SQL Server DW',
    schedule_interval='0 * * * *', # Every hour
    catchup=False,
    tags=['etl', 'gold']
) as dag:

    t_load_products = PythonOperator(
        task_id='load_products',
        python_callable=run_load,
        op_kwargs={'table_name': 'products'}
    )

    t_load_customers = PythonOperator(
        task_id='load_customers',
        python_callable=run_load,
        op_kwargs={'table_name': 'customers'}
    )
    
    # Independent loads for dimensions
    [t_load_products, t_load_customers]
