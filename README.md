# Projeto ETL de Vendas (End-to-End)

Este repositório contém uma implementação completa de um pipeline de dados (ETL) utilizando **Docker**, **Airflow**, **Postgres** e **SQL Server**.

## 🏗 Arquitetura

O fluxo de dados segue uma variação da arquitetura Medallion aka **Simplified Medallion** (Bronze -> Gold):
1.  **Origem (Postgres)**: Banco de dados transacional simulando um e-commerce.
2.  **Ingestão (Bronze)**: DAG `ingest_sales_data` extrai dados novos incrementalmente para arquivos Parquet no Data Lake local (Raw Data).
3.  **Processamento (Gold)**: DAG `process_sales_dw` lê a Bronze, aplica **qualidade e limpeza em memória (Transient Silver)** e carrega diretamente no SQL Server (Data Warehouse).
4.  **Destino (SQL Server)**: Armazena as tabelas Dimensão e Fato prontas para consumo.

> **Nota de Arquitetura**: Optamos por não persistir a camada *Silver* em disco (Parquet) para reduzir latência e custos de armazenamento, dado que as transformações são leves e o Data Warehouse atua como a camada de verdade única para consumo. A lógica de limpeza ("Silver") é aplicada `in-flight` durante a carga.

## 🚀 Como Rodar o Projeto

### Pré-requisitos
*   Docker e Docker Compose
*   Python 3.10+

### Passo 1: Subir Infraestrutura
```bash
docker-compose -f docker/docker-compose-databases.yaml up -d
```
Isso iniciará os containers do Postgres (`postgres_sales`) e SQL Server (`sqlserver_etl`).

### Passo 2: Gerar Dados Simulados
Para popular a origem com vendas fictícias:
```bash
source venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1
python src/datagen/generate_data.py
```

### Passo 3: Executar o ETL (Simulação Manual)
Se não tiver o Airflow rodando, use os scripts manuais para testar a lógica dos DAGs:

**Extrator (Bronze)**:
```bash
# Código equivalente ao DAG ingest_sales_data
python -c "import sys; sys.path.append('.'); from dags.ingest_sales_data import run_extraction; run_extraction('products'); run_extraction('orders')"
```

**Loader (Gold)**:
```bash
# Código equivalente ao DAG process_sales_dw
export SQLSERVER_HOST=localhost
python -c "import sys; sys.path.append('.'); from dags.process_sales_dw import run_load; run_load('products')"
```

## 📂 Estrutura do Projeto

*   `dags/`: Definições dos workflows do Airflow.
*   `src/`: Código fonte modularizado.
    *   `extract/`: Lógica de extração do Postgres.
    *   `load/`: Lógica de carga no SQL Server (inclui Validação e Auditoria).
    *   `common/`: Helpers de Banco, Log e Validação.
    *   `datagen/`: Script gerador de dados falsos.
    *   `tests/`: Testes unitários (`pytest`).
*   `docker/`: Arquivos docker-compose.
*   `docs/`: Documentação detalhada e artefatos do projeto.
*   `sql/`: Scripts de inicialização dos bancos.

## ✅ Observabilidade
*   **Auditoria**: Verifique a tabela `control.etl_audit` no SQL Server para logs de execução.
*   **Qualidade**: Regras de negócio são aplicadas em `src/common/validators.py`.

---
*Desenvolvido como projeto de referência de Engenharia de Dados.*