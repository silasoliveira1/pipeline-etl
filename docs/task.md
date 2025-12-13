# Projeto ETL Sales - Checklist

- [x] **Fase 1: Infraestrutura e Fontes**
    - [x] Configurar Docker Compose (Postgres e SQL Server).
    - [x] Criar scripts de inicialização (DDL).
    - [x] Criar script gerador de dados (API Simulada).
    - [x] Validar funcionamento dos bancos e carga inicial.

- [ ] **Fase 2: Automação e ETL (Airflow)** <!-- CURRENT -->
    - [x] **Planejamento**
    - [x] **Extração (Ingestion)** <!-- DONE -->
        - [x] Helper de Conexão `src/common/db.py`
        - [x] Extrator `src/extract/postgres_extractor.py` (Incremental)
        - [x] DAG `dags/ingest_sales_data.py`
    - [x] **Transformação e Carga (Processing)** <!-- DONE -->
        - [x] Connection Helper para SQL Server (python-tds).
        - [x] Loader `src/load/sqlserver_loader.py` (Parquet -> SQL Server).
        - [x] DAG `dags/process_sales_dw.py`.

- [x] **Fase 3: Observabilidade e Testes** <!-- DONE -->
    - [x] **Data Quality** <!-- DONE -->
        - [x] Criar validadores em `src/common/validators.py`.
        - [x] Integrar validação no Loader (Bloquear dados inválidos).
    - [x] **Auditoria** <!-- DONE -->
        - [x] Criar tabela `control.etl_audit` no SQL Server.
        - [x] Criar helper `Logger` para gravar logs de execução no banco.
        - [x] Atualizar DAGs para usar o Logger.
