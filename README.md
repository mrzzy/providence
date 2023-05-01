# Providence
Data Pipeline &amp; Dashboard for Personal Finance Monitoring.

## Background
I ❤️  [YNAB](https://www.ynab.com/) for personal finance budgeting/accounting, it really helps me keep my finances in check. However, I hold a few pet peeves with YNAB:
- YNAB's bank account import feature only supports Banks from the US and manual account reconciliation is not a fun experience.
- YNAB's limited visualisation features (bar, pie chart & pivot table) does not give a good picture of "state of finances".
- Keying in a transaction into YNAB every time I can take Public Transport can quickly become repetitive.

## Features
Providence aims to make personal finance less tedious with automation & less opaque with visualisation:
- **Data Sources** to scrape data:
    -  **rest-api-src** pulls Budget/Accounting data from YNAB API.
    -  **simplygo-src** scrapes Public Transport trip data from SimplyGo Portal.
- **Data Transforms** to reshape data:
    - **Pandas** to extract transactions from the Excel export I receive from my Bank.
    - **DBT** to reshape raw data into a Dimensional Model & a Data Mart dedicated for populating the Finance Dashboard.
- **Data Pipelines** Airflow DAGs to orchestrate everything.

![[Finance Dashboard Screenshot.png]]

* **Finance Dashboard** visualise the data to give me a picture of where I'm at financially & assist in me in budgeting / accounting.
    - **Unreconciled Transactions** Lists transactions that in my books but not in my bank account & vice versa. Its a great help when reconciling accounts.

## Architecture
```mermaid
flowchart TB
    subgraph AWS
        subgraph src[Data Sources]
            ynab((YNAB)) --> rest-api[REST API Source]
            simplygo-web((Simplygo)) --> simplygo[Simplygo Source]
        end

        rest-api & simplygo -->|json| lake[(AWS S3 Lake)]
        uob((Bank Export)) -->|excel| lake --->|files| ext
        lake -->|excel| pd{{Pandas}} -->|parquet| lake

        subgraph dw[AWS Redshift Warehouse]
            ext[External Tables] -->|clean| dbt-models[DBT Models]
            dbt-models --> dbt{{DBT}} -->|transform| dbt-models
        end
    end
    dw ---> fin-dash
    subgraph GCP
        subgraph GKE
            subgraph airflow[Apache Airflow]
                ynab-pipe[YNAB Pipeline]
                simplygo-pipe[SimplyGo Pipeline]
                uob-pipe[UOB Pipeline]
            end
            subgraph superset[Apache Superset]
                fin-dash((Finance\nDashboard))
            end
        end
    end
```
- **Data Lake** AWS S3
- **Data Warehouse** AWS Redshift Serverless
- **Orchestration** Apache Airflow with Kubernetes Executor.
- **Business Intellegence** Apache Superset

## Data Model
```mermaid
---
title: Providence Data Model
---
erDiagram
    dim_date {
        date id PK
        date date
        int day_of_month
        int day_of_week
        int day_of_year
        int week_of_month
        int week_of_year
        string weekday_name
        string weekday_short
        int month_of_year
        string month_name
        string month_short
        int quarter
        date month_year
        int year
        boolean is_weekend
    }

    fact_public_transport_trip_leg {
        string id PK
        timestamp traveled_on
        int travel_date_id FK
        decimal cost_sgd
        string source
        string destination
        string transport_mode
        string bank_card_id FK
        string billing_ref
        boolean is_billed
        timestamp updated_at
    }

    dim_bank_card {
        string id PK
        string name
        timestamp updated_at
    }

    fact_public_transport_trip_leg }| -- || dim_date: "travelled on"
    fact_public_transport_trip_leg }| -- || dim_bank_card: "billed on"

    fact_accounting_transaction {
        string id PK
        string super_id FK
        decimal amount
        string description
        string clearing_status
        boolean is_approved
        boolean is_deleted
        int budget_id FK
        int account_id FK
        int payee_id FK
        int transfer_account_id FK
        int date_id FK
        timestamp updated_at
    }

    dim_budget {
        string id PK
        string name
        timestamp modified_at
        string currency_code
        string currency_symbol
        timestamp updated_at
    }

    dim_account {
        string id PK
        string name
        boolean is_closed
        boolean is_deleted
        boolean is_liquid
        string budget_type
        string vendor
        string vendor_id
        string vendor_type
        timestamp updated_at
    }

    dim_payee {
        string id PK
        boolean is_deleted
        string transfer_account_id FK
        timestamp updated_at
    }

    dim_budget_category {
        string id PK
        string category_id
        string name
        string budget_id
        string category_group_id
        string category_group
        string goal_type
        decimal goal_amount
        date goal_due
        boolean is_deleted
        timestamp updated_at
        timestamp effective_at
        timestamp expired_at
    }

    fact_accounting_transaction }|--|| fact_accounting_transaction: "parent"
    fact_accounting_transaction }|--|| dim_budget: "uses"
    fact_accounting_transaction }|--|| dim_budget_category: "classified as"
    fact_accounting_transaction }|--|| dim_account: "on"
    fact_accounting_transaction }|--|| dim_account: "transfer to"
    fact_accounting_transaction }|--|| dim_date: "made on"
    fact_accounting_transaction }|--|| dim_payee: "paid to"

    fact_monthly_budget {
        string id PK
        int month_date_id FK
        int budget_id FK
        int category_id FK
        decimal amount
        timestamp updated_at
    }

    fact_monthly_budget }|--|| dim_budget: "allocated to"
    fact_monthly_budget }|--|| dim_budget_category: "classified as"
    fact_monthly_budget }|--|| dim_date: "allocated on"

    fact_vendor_transaction {
        string id PK
        string description
        decimal amount
        int date_id FK
        int account_id FK
        timestamp updated_at
    }

    fact_vendor_transaction }|--|| dim_date: "made on"
    fact_vendor_transaction }|--|| dim_account: "on"

    fact_bank_statement {
        string id PK
        int begin_date_id FK
        int end_date_id FK
        int account_id FK
        decimal balance
        timestamp updated_at
    }
    fact_bank_statement }|--|| dim_date: "statement began"
    fact_bank_statement }|--|| dim_date: "statement ended"
    fact_bank_statement }|--|| dim_account: "on"
```

See [DBT Docs](https://mrzzy.github.io/providence/#!/overview) for more details.

## License
MIT.
