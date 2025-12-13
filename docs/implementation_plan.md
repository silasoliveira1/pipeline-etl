# Planejamento e Validação da Arquitetura de Dados (ETL)

## 1. Avaliação do Escopo Fornecido
O documento "Escopo da Arquitetura do Projeto de Pipeline de Dados" apresenta uma estrutura **muito robusta e profissional**. Ele cobre os pontos principais exigidos em grandes empresas:
- **Orquestração**: Uso de Airflow é o padrão de mercado.
- **Idempotência e Cargas Incrementais**: Abordagem correta (Watermark e Merge).
- **Conteinerização**: Uso de Docker facilita a reprodução do ambiente.
- **Observabilidade**: Menção a logs, métricas e auditoria.

**Conclusão da Validação**: O escopo está **aprovado** e muito bem desenhado. Ele demonstra maturidade técnica. Não há falhas estruturais, apenas oportunidades de detalhamento.

## 2. Consultoria: O Papel da API no Projeto
Você questionou sobre a API: *"Como será esse desenvolvimento e o que vamos usar de dados, pois o final do fluxo é o SQL Server?"*.

Existem duas formas de enxergar essa API neste projeto. Sugiro a **Abordagem A** para simular um cenário real de empresa.

### Abordagem Sugerida: API como "Simulador de Negócio"
Numa empresa real, o Banco de Dados Transacional (Postgres) não surge vazio. Ele é alimentado por uma aplicação (Backend).
Para o seu portfólio, construiremos um script (ou uma API simples) que **simula vendas acontecendo**.

**Fluxo de Dados:**
1.  **Mundo Externo / Gerador**: Um script Python busca dados (ou gera dados aleatórios).
2.  **API/Ingestor ("Aplicação")**: Grava esses dados no **Postgres** (Tabela `orders`, `customers`).
    *   *Isso simula o site de vendas da empresa funcionando.*
3.  **ETL (Seu foco principal)**: O Airflow lê do Postgres -> Transforma -> Grava no **SQL Server**.
4.  **Analytics**: PowerBI lê do SQL Server.

### O que usar de dados? (Sugestões)
Para não ter que criar produtos reais, podemos usar APIs públicas de dados fictícios ou geradores:
*   **Fake Store API**: Para obter produtos reais (imagem, descrição, preço).
*   **Faker Library (Python)**: Para gerar clientes brasileiros (CPF, Endereço) e datas de transação.
*   **AwesomeAPI (Cotações)**: Para trazer o valor do dólar no dia da venda (enriquecimento de dados).

**Sugestão de Funcionalidade da "API de Ingestão":**
Um script simples que roda a cada X minutos (pode ser agendado no cron ou no próprio Airflow como um DAG separado de "Simulação"):
1.  Busca 5 produtos aleatórios da API Pública ou Lista Estática.
2.  Gera 1 cliente fictício (Faker).
3.  Insere uma compra (Order) no **Postgres**.

Isso garante que seu ETL sempre tenha dados novos para processar (Incremental) sem você precisar inserir na mão.

## 3. Melhorias e Sugestões Técnicas
Aqui estão recomendações para elevar ainda mais o nível do projeto:

### 3.1 Arquitetura de Camadas (Medallion Architecture)
Embora mencionado como "Landing -> Staging -> DW", formalize os nomes das camadas dentro do seu Data Lake (sistema de arquivos ou MinIO) e DW:
*   **Bronze (Raw)**: Dado cru extraído do Postgres/API (Ex: JSON ou Parquet sem tipagem forte).
*   **Silver (Staging/Trusted)**: Dado limpo, tipado, deduplicado. (Aqui aplicamos as regras de *Quality*).
*   **Gold (Analytics/Serving)**: As tabelas Fato e Dimensão no SQL Server prontas para o PowerBI (Modelo Star Schema).

### 3.2 Quality Gates (Great Expectations ou Pandera)
Adicionar um passo explícito de validação entre a Silver e a Gold. Se o dado estiver "sujo" (ex: valor de venda negativo), ele não deve ir para o SQL Server para não quebrar o dashboard.
*   *Ação*: Implementar uma verificação simples com `pandera` no código Python de transformação.

### 3.3 Estrutura do Repositório
O documento sugere uma estrutura boa. Recomendo garantir que os scripts SQL (`create_dw_tables.sql`) sejam executados automaticamente na inicialização do container (via entrypoint) para que "subir o ambiente" seja apenas um `docker-compose up`.

## 4. Plano de Implementação
Vamos dividir o desenvolvimento em fases lógicas:

### Fase 1: Infraestrutura e Fontes (Setup)
*   Criar `docker-compose.yml` com Postgres e SQL Server.
*   Criar script de inicialização dos bancos (DDL das tabelas `orders`, `products` no Postgres e tabelas vazias no SQL Server).
*   **Desenvolver o Script de Ingestão (A "API")**:
    *   Script Python que gera vendas falsas e insere no Postgres.
    *   *Objetivo*: Ter o Postgres populado com dados transacionais.

### Fase 2: Extração e Landing (Bronze)
*   Configurar conexões no Airflow (se já existir, criar as Connections).
*   Criar DAG `extract_postgres`:
    *   Query incremental (Watermark).
    *   Salvar em formato Parquet na pasta `datalake/bronze`.

### Fase 3: Transformação e Carga (Silver & Gold)
*   Criar DAG `transform_load`:
    *   Ler Parquet da Bronze.
    *   Limpar dados (Pandas/Polars).
    *   Aplicar regras de negócio (cálculo de total, conversão de moeda).
    *   Escrever na Silver (Parquet).
    *   Inserir no SQL Server (Gold) usando estratégia de MERGE (Upsert).

### Fase 4: Validação
*   Conectar PowerBI (ou simular consulta SQL) para validar os dados no SQL Server.

---


## Fase 2: Automação e Pipelines (Airflow)

Esta seção detalha como transformaremos os scripts isolados em um pipeline profissional e automatizado.

### 1. Estratégia de Orquestração
Teremos 2 DAGs principais para separar responsabilidades e permitir reprocessamento independente.

#### **DAG 1: `ingest_sales_data` (Frequência: 30 min)**
*   **Objetivo**: Extrair dados novos do Postgres e salvar no Data Lake (Bronze).
*   **Lógica**:
    1.  Ler tabela de controle (`etl_watermark`) para saber a última data de execução.
    2.  Consultar Postgres: `SELECT * FROM table WHERE updated_at > :last_watermark`.
    3.  Salvar arquivo Parquet em: `lake/bronze/{tabela}/YYYYMMDD/{timestamp}.parquet`.
    4.  Atualizar tabela de controle com o novo `max(updated_at)`.
*   **Tabelas Alvo**: `orders`, `order_items`, `products`, `customers`.

#### **DAG 2: `process_sales_dw` (Trigger: Após Ingestão)**
*   **Objetivo**: Ler do Data Lake, transformar e carregar no SQL Server (Gold).
*   **Estrutura (Medallion Architecture)**:
    *   **Silver (Staging)**: 
        *   Ler Parquet Bruto.
        *   Dedup (remover duplicatas se houver reenvio).
        *   Converter tipos (ex: string "100.50" para decimal).
    *   **Gold (Fact/Dim)**: 
        *   Carregar Dimensões (`dim_customers`, `dim_products`) usando SCD Tipo 1 (Atualiza se mudar).
        *   Carregar Fato (`fact_sales`) garantindo integridade referencial (lookup de SKs).
*   **Carga no SQL Server**:
    *   Usaremos scripts SQL com comando `MERGE` (Upsert) ou inserção em tabela temporária + troca para garantir performance.

### 2. Estrutura de Pastas e Scripts
Organizaremos o código dentro da pasta `dags/` e `src/` para manter limpo:
```
dags/
  sales_pipeline.py  # Define orquestração e dependências
src/
  extract.py         # Lógica pura de conexão Postgres -> Parquet
  transform.py       # Pandas/Polars para limpeza
  load.py            # Conexão PyODBC/pymssql para SQL Server
```

---

## Fase 3: Observabilidade e Testes

### 1. Data Quality (Blindagem)
Implementaremos validações na entrada da camada **Gold (SQL Server)**. Se o dado estiver ruim, ele é rejeitado ou alertado.
*   **Validadores**:
    *   `products`: `price` deve ser > 0.
    *   `customers`: `email` deve conter "@".
    *   `orders`: `total_amount` deve ser >= 0.
*   **Implementação**: Uma classe `DataValidator` que recebe o DataFrame logo após a leitura do Bronze e antes do Load.

### 2. Auditoria de Execução
Para saber o que aconteceu sem olhar logs de texto do Airflow, criaremos a tabela `control.etl_audit` no SQL Server.
*   **Schema**:
    *   `execution_id` (UUID ou timestamp)
    *   `process_name` (ex: "load_customers")
    *   `status` (SUCCESS, ERROR)
    *   `rows_processed` (int)
    *   `error_message` (text)
    *   `start_time`, `end_time`
*   **Implementação**: Decorator python ou Context Manager nos DAGs/Loaders.

---
## Próximos Passos (Plano de Ação)
1.  **Criar Tabela de Auditoria**: Script SQL em `sql/sqlserver/audit.sql`.
2.  **Helpers de Auditoria/Validação**: Criar `src/common/audit.py` e `src/common/validators.py`.
3.  **Atualizar Loaders**: Injetar validação e logging.
