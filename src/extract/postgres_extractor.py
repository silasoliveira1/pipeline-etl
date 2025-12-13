import os
import pandas as pd
from datetime import datetime
from src.common.db import get_postgres_conn

class PostgresExtractor:
    def __init__(self, base_path="./datalake"):
        self.base_path = base_path
        self.bronze_path = os.path.join(base_path, "bronze")
        os.makedirs(self.bronze_path, exist_ok=True)

    def extract_table(self, table_name: str, watermark_col: str = 'updated_at', last_watermark: str = '1970-01-01 00:00:00'):
        """
        Extracts new rows from Postgres based on watermark.
        """
        print(f"[{datetime.now()}] Extracting {table_name} since {last_watermark}...")
        
        query = f"""
            SELECT * 
            FROM sales.{table_name} 
            WHERE {watermark_col} > '{last_watermark}'
        """
        
        conn = get_postgres_conn()
        try:
            # Use native cursor to avoid SQLAlchemy issues on some envs
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Fetch data and column names
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            cursor.close()
            
            df = pd.DataFrame(data, columns=columns)
            
            row_count = len(df)
            print(f"[{datetime.now()}] Found {row_count} new rows.")
            
            if row_count > 0:
                self._save_to_bronze(df, table_name)
                # Return the new max watermark
                # Ensure we handle timestamp objects correctly
                new_watermark = df[watermark_col].max()
                return str(new_watermark)
            
            return last_watermark

        finally:
            conn.close()

    def _save_to_bronze(self, df: pd.DataFrame, table_name: str):
        """
        Saves DataFrame as Parquet in the Bronze layer partition by ingestion date.
        Path: bronze/{table}/YYYY/MM/DD/{timestamp}.parquet
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        save_dir = os.path.join(self.bronze_path, table_name, year, month, day)
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = now.strftime("%H%M%S")
        file_path = os.path.join(save_dir, f"{timestamp}.parquet")
        
        # Enforce PyArrow engine for compatibility
        df.to_parquet(file_path, engine='pyarrow', index=False)
        print(f"[{datetime.now()}] Saved {len(df)} rows to {file_path}")
