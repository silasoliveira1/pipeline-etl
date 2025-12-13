import os
import pandas as pd
from datetime import datetime
from src.common.db import get_sqlserver_conn
from src.common.audit import AuditLogger
from src.common.validators import DataValidator

class SqlServerLoader:
    def __init__(self, base_path="./datalake", silver_path="./datalake/silver"):
        self.base_path = base_path
        self.bronze_path = os.path.join(base_path, "bronze")
        self.silver_path = silver_path
        os.makedirs(self.silver_path, exist_ok=True)
        self.audit = AuditLogger()
        self.validator = DataValidator()

    def process_and_load(self, table_name):
        """
        Reads all Parquet files from Bronze for the table, process them, and loads to SQL Server.
        """
        audit_id = self.audit.start_audit(f"load_{table_name}")
        print(f"[{datetime.now()}] Loading {table_name} to SQL Server (Audit ID: {audit_id})...")
        
        try:
            # 1. Read Bronze
            bronze_dir = os.path.join(self.bronze_path, table_name)
            if not os.path.exists(bronze_dir):
                print(f"No data found for {table_name}")
                self.audit.log_success(audit_id, 0)
                return

            df_list = []
            for root, dirs, files in os.walk(bronze_dir):
                for file in files:
                    if file.endswith(".parquet"):
                        df_list.append(pd.read_parquet(os.path.join(root, file)))
            
            if not df_list:
                print("No parquet files found.")
                self.audit.log_success(audit_id, 0)
                return
                
            df = pd.concat(df_list, ignore_index=True)
            print(f"Read {len(df)} rows from Bronze.")

            # 2. Validate
            if table_name == 'products':
                df = self.validator.validate_products(df)
            elif table_name == 'customers':
                df = self.validator.validate_customers(df)
            elif table_name == 'orders':
                df = self.validator.validate_orders(df)
            
            if df.empty:
                print("All rows dropped by validator.")
                self.audit.log_success(audit_id, 0)
                return

            # 3. Load (Gold)
            conn = get_sqlserver_conn()
            cursor = conn.cursor()
            
            try:
                if table_name == 'customers':
                    self._load_customers(cursor, df)
                elif table_name == 'products':
                    self._load_products(cursor, df)
                elif table_name == 'orders':
                    # Skip for now as per previous logic
                    pass 
                    
                conn.commit()
                print(f"[{datetime.now()}] Load complete for {table_name}")
                self.audit.log_success(audit_id, len(df))
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error loading {table_name}: {e}")
            self.audit.log_error(audit_id, str(e))
            raise e
        finally:
            self.audit.close()

    def _load_customers(self, cursor, df):
        for _, row in df.iterrows():
            cursor.execute("SELECT customer_sk FROM dw.dim_customers WHERE email = %s", (row['email'],))
            res = cursor.fetchone()
            
            if res:
                cursor.execute("""
                    UPDATE dw.dim_customers 
                    SET first_name = %s, last_name = %s, phone = %s, dw_updated_at = GETDATE()
                    WHERE customer_sk = %s
                """, (row['first_name'], row['last_name'], row['phone'], res[0]))
            else:
                cursor.execute("""
                    INSERT INTO dw.dim_customers (customer_id, first_name, last_name, email, phone)
                    VALUES (%s, %s, %s, %s, %s)
                """, (row['customer_id'], row['first_name'], row['last_name'], row['email'], row['phone']))

    def _load_products(self, cursor, df):
        for _, row in df.iterrows():
            cursor.execute("SELECT product_sk FROM dw.dim_products WHERE product_id = %s", (row['product_id'],))
            res = cursor.fetchone()
            
            if res:
                 cursor.execute("""
                    UPDATE dw.dim_products 
                    SET product_name = %s, category = %s, current_price = %s, dw_updated_at = GETDATE()
                    WHERE product_sk = %s
                """, (row['product_name'], row['category'], float(row['price']), res[0]))
            else:
                cursor.execute("""
                    INSERT INTO dw.dim_products (product_id, product_name, category, current_price)
                    VALUES (%s, %s, %s, %s)
                """, (row['product_id'], row['product_name'], row['category'], float(row['price'])))
