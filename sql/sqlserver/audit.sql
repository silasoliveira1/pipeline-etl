/*
    Audit Table for ETL Process
    Tracks execution status and metrics.
*/

USE sales_dw;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'etl_audit' AND schema_id = SCHEMA_ID('control'))
BEGIN
    CREATE TABLE control.etl_audit (
        audit_id INT IDENTITY(1,1) PRIMARY KEY,
        execution_id VARCHAR(50), -- UUID provided by Airflow/Python
        process_name VARCHAR(100),
        status VARCHAR(20), -- 'START', 'SUCCESS', 'ERROR'
        rows_processed INT DEFAULT 0,
        error_message NVARCHAR(MAX),
        start_time DATETIME2 DEFAULT GETDATE(),
        end_time DATETIME2
    );
END
GO
