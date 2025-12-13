# Walkthrough: Validação e Setup da Infraestrutura

## O que foi feito
1.  **Infraestrutura Docker**: Subimos os containers `postgres_sales` (Transacional) e `sqlserver_etl` (Analytics) usando `docker-compose`.
2.  **Inicialização dos Bancos**:
    *   **Postgres**: Tabelas `sales.orders`, `sales.customers`, etc. criadas.
    *   **SQL Server**: Database `sales_dw` e tabelas `dw.fact_sales`, `dw.dim_customers`.
3.  **Geração de Dados (A "API Simulada")**:
    *   Criamos e rodamos o script `src/datagen/generate_data.py`.
    *   Ele conectou no Fake Store API (ou gerou localmente) e inseriu pedidos aleatórios no Postgres.

## Validação

### 1. Containers Rodando
Executamos `docker ps` e confirmamos que ambos estão UP.

### 2. Dados no Postgres (Resultados do Script)
O script de geração de dados executou com sucesso:
```text
Starting Data Generator...
Fetching products from Fake Store API...
Inserted 20 products from API.
Generating 5 new sales transactions...
Created Order #1 for Customer #1
...
Done.
```
Isso prova que o banco Transacional (Origem) já tem movimentação para ser extraída pelo ETL.

## Como Acessar/Verificar
Se quiser verificar o banco Postgres manualmente:
```bash
docker exec -it postgres_sales psql -U sales_user -d sales_db
# Dentro do psql:
SET search_path TO sales;
SELECT * FROM orders;
```

Para o SQL Server:
```bash
docker exec -it sqlserver_etl /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P 'BigDataPassword123!' -d sales_dw
# Dentro do sqlcmd:
SELECT name FROM sys.tables;

### 3. Validação do ETL (Fase 2)
Implementamos os DAGs e Scripts de ETL. Para validar localmente sem o Airflow (simulação):

**Extração (Ingestion)**:
```bash
# Rodar extração manual
python manual_dag_run.py
```
Isso cria arquivos parquet na pasta `datalake/bronze`.

**Carga (Load)**:
```bash
# Rodar carga manual para SQL Server
python manual_load_run.py
```

**Verificar no SQL Server**:
```bash
docker exec -it sqlserver_etl /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P 'BigDataPassword123!' -d sales_dw -Q "SELECT COUNT(*) AS total_customers FROM dw.dim_customers; SELECT COUNT(*) AS total_products FROM dw.dim_products;"
```

### 4. Validação da Observabilidade (Fase 3)
Verificar se o processo de carga gravou logs na tabela de auditoria.

**Comando SQL via Docker**:
```bash
docker exec -it sqlserver_etl /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P 'BigDataPassword123!' -d sales_dw -Q "SELECT top 5 execution_id, process_name, status, rows_processed, start_time, end_time FROM control.etl_audit ORDER BY audit_id DESC"
```
Esperado: Linhas com `status = 'SUCCESS'`.

