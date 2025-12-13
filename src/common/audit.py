from datetime import datetime
from src.common.db import get_sqlserver_conn
import uuid

class AuditLogger:
    def __init__(self):
        self.conn = get_sqlserver_conn()
        self.cursor = self.conn.cursor()

    def start_audit(self, process_name, execution_id=None):
        if not execution_id:
            execution_id = str(uuid.uuid4())
            
        try:
            # Split execution to ensure we get the ID
            query = """
                INSERT INTO control.etl_audit (execution_id, process_name, status, start_time)
                VALUES (%s, %s, 'START', GETDATE());
            """
            self.cursor.execute(query, (execution_id, process_name))
            
            self.cursor.execute("SELECT @@IDENTITY")
            row = self.cursor.fetchone()
            self.conn.commit()
            return int(row[0]) if row and row[0] is not None else None
        except Exception as e:
            print(f"Audit Start Failed: {e}")
            return None

    def log_success(self, audit_id, rows_processed=0):
        if not audit_id: return
        try:
            query = """
                UPDATE control.etl_audit 
                SET status = 'SUCCESS', rows_processed = %s, end_time = GETDATE()
                WHERE audit_id = %s
            """
            self.cursor.execute(query, (rows_processed, audit_id))
            self.conn.commit()
        except Exception as e:
            print(f"Audit Success Log Failed: {e}")

    def log_error(self, audit_id, error_message):
        if not audit_id: return
        try:
            # Truncate error if too long
            error_message = str(error_message)[:4000]
            query = """
                UPDATE control.etl_audit 
                SET status = 'ERROR', error_message = %s, end_time = GETDATE()
                WHERE audit_id = %s
            """
            self.cursor.execute(query, (error_message, audit_id))
            self.conn.commit()
        except Exception as e:
            print(f"Audit Error Log Failed: {e}")

    def close(self):
        try:
            self.conn.close()
        except:
            pass
