from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import json

# Add src to sys.path to allow imports
# Support both:
# 1. Dev structure: src is sibling of dags (..)
# 2. Deploy structure: src is inside dags (.)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from src.extract.postgres_extractor import PostgresExtractor

# Watermark Manager (Local JSON implementation for simplicity)
class WatermarkManager:
    def __init__(self, file_path='etl_watermark.json'):
        self.file_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        
    def get_watermark(self, table_name):
        if not os.path.exists(self.file_path):
            return '1970-01-01 00:00:00'
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return data.get(table_name, '1970-01-01 00:00:00')
        except Exception:
            return '1970-01-01 00:00:00'

    def update_watermark(self, table_name, value):
        data = {}
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                try:
                    data = json.load(f)
                except: 
                    pass
        
        data[table_name] = value
        
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

def run_extraction(table_name, **kwargs):
    extractor = PostgresExtractor(base_path=os.path.join(os.path.dirname(__file__), '..', 'datalake'))
    wm_manager = WatermarkManager()
    
    last_wm = wm_manager.get_watermark(table_name)
    print(f"Starting extraction for {table_name} with watermark: {last_wm}")
    
    new_wm = extractor.extract_table(table_name, last_watermark=last_wm)
    
    if new_wm > last_wm:
        print(f"Updating watermark for {table_name} to {new_wm}")
        wm_manager.update_watermark(table_name, new_wm)
    else:
        print(f"No new data for {table_name}")

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ingest_sales_data',
    default_args=default_args,
    description='Ingests sales data from Postgres to Bronze Parquet',
    schedule_interval='*/30 * * * *', # Every 30 mins
    catchup=False,
    tags=['etl', 'bronze']
) as dag:

    t_products = PythonOperator(
        task_id='ingest_products',
        python_callable=run_extraction,
        op_kwargs={'table_name': 'products'}
    )

    t_customers = PythonOperator(
        task_id='ingest_customers',
        python_callable=run_extraction,
        op_kwargs={'table_name': 'customers'}
    )

    t_orders = PythonOperator(
        task_id='ingest_orders',
        python_callable=run_extraction,
        op_kwargs={'table_name': 'orders'}
    )
    
    # Dependencies (Parallel execution is fine here, or sequential if resources are low)
    [t_products, t_customers, t_orders]
