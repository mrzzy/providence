# Providence

Personal Finance Data Pipeline & Dashboard.

## Features

![Finance Dashboard Screenshot](assets/finance_dashboard_screenshot.png)

Providence aims to make personal finance less tedious with automation & less opaque with visualisation:

- **Data Sources** to automatically retrieve raw data from data sources:
  - **YNAB Source** pulls Budget/Accounting data from YNAB REST API.
  - **SimplyGo Source** scrapes HTML from [SimplyGo Portal](https://simplygo.transitlink.com.sg/)
- **Data Transforms** to extract tabular data from raw data files:
  - **YNAB transform** extracts accounting transactions from JSON budget data.
  - **SimplyGo transform** extracts public transport trip data from scraped html.
  - **UOB transform** extract bank statement transactions from Excel export.
- **Data Model** DBT Dimensional model integrates data from disparate sources together for analysis.
- **Finance Dashboard** Superset dashboard presets easy to digest metrics on financial health.


## Architecture
```mermaid
---
title: Providence V2
---

flowchart LR
    subgraph p[Prefect, Grafana]
      direction TB
      ynab((YNAB)) &  uob((UOB)) & simplygo((SimplyGO)) -->|sinks| b2
      subgraph b2[B2 Bucket]
          direction LR
          raw[Raw: JSON, Excel] -->|transform| tfms[[Transforms on ACI]] --> staging[Staging: parquet]
      end
      staging -->|load| dbt[[DBT on ACI]] --> dw[(MotherDuck\n DuckDB)]
      dw -->|transform| dbt
      dw -->|visualise| viz(((Superset)))
   end
```

V2 architecture redesign focuses on lowering the Total Cost of Ownership (TCO)
by relying on Serverless Compute and free-tier Managed Services:
- **Compute** Azure Container Instances (ACI)
- **Data Lake** Backblaze B2
- **Data Warehouse** MotherDuck DuckDB
- **Orchestration** Prefect
- **Visualisation** Apache Superset

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
        string account_id FK
        string billing_ref
        boolean is_billed
        timestamp updated_at
    }

    dim_bank_card {
        string id PK
        string name
        timestamp updated_at
    }

    fact_public_transport_trip_leg }| -- || dim_account: "billed to"
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

    fact_vendor_transaction {
        string id PK
        string description
        decimal amount
        int date_id FK
        int account_id FK
        timestamp updated_at
    }

    fact_vendor_transaction }|--|| dim_account: "on"

    fact_bank_statement {
        string id PK
        int begin_date_id FK
        int end_date_id FK
        int account_id FK
        decimal balance
        timestamp updated_at
    }
    fact_bank_statement }|--|| dim_account: "on"
```

See [DBT Docs](https://mrzzy.github.io/providence/#!/overview) for more details.

## License

MIT.
