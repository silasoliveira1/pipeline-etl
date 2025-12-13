import os
import pg8000.dbapi
import time

def get_postgres_conn():
    """
    Returns a pg8000 connection to the Postgres Source.
    Reads params from Env Vars or defaults.
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    db = os.getenv("POSTGRES_DB", "sales_db")
    user = os.getenv("POSTGRES_USER", "sales_user")
    password = os.getenv("POSTGRES_PASSWORD", "sales_password")
    # Handle port as string or int safe
    port = int(os.getenv("POSTGRES_PORT", 5432))

    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = pg8000.dbapi.connect(
                host=host,
                database=db,
                user=user,
                password=password,
                port=port
            )
            # Ensure search path is set to sales
            cur = conn.cursor()
            cur.execute("SET search_path TO sales")
            cur.close()
            return conn
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)

import pytds

def get_sqlserver_conn():
    """
    Returns a connection to SQL Server DW using python-tds.
    """
    host = os.getenv("SQLSERVER_HOST", "localhost")
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "BigDataPassword123!")
    database = os.getenv("SQLSERVER_DB", "sales_dw")
    port = int(os.getenv("SQLSERVER_PORT", 1433))

    # pytds.connect(server, user, password, database)
    conn = pytds.connect(
        server=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=True
    )
    return conn
