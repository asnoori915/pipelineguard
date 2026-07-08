# PipelineGuard

PipelineGuard is a portfolio project I built to practice data quality validation with synthetic relational data in PostgreSQL.

It generates a small e-commerce dataset, loads it into the database, optionally breaks the data on purpose, runs validation checks, saves run history to PostgreSQL, and writes both Markdown and JSON reports.

Many validation rules live in `config/validation_rules.yml`, which makes the checks easier to adjust and explain.

## Project Overview

PipelineGuard simulates a small e-commerce data pipeline with five related tables. It generates clean synthetic CSV files, loads them into PostgreSQL, runs config-driven validation checks, and records the results.

The project also includes a data break simulator so I can inject common data quality issues and confirm the validation layer catches them.

Recent additions include:

- PostgreSQL audit tables for run history
- JSON report output alongside Markdown
- automatic saving of validation results on every pipeline run
- a dbt analytics layer with staging models, marts, and tests

## Why I Built This

The idea came from working with database-oriented synthetic data workflows and wanting to understand data quality validation more directly.

Generating and loading data is only part of the job. I also wanted practice checking whether the data is complete, consistent, and structurally correct before anything downstream depends on it.

PipelineGuard helped me work on:

- relational schema design
- synthetic data generation with valid foreign keys
- SQL-based validation checks
- config-driven rules
- reporting and run history for data quality results
- basic analytics modeling with dbt

This is a learning project, not production tooling. It gave me a concrete way to think about validation as part of the pipeline itself.

## Tech Stack

- Python
- PostgreSQL 16
- Docker Compose
- SQL
- pandas
- Faker
- SQLAlchemy
- PyYAML
- python-dotenv
- tabulate
- dbt Core

## Architecture Flow

```text
generate_data → load_data → break_data (optional) → validate_data → audit → generate_report → dbt (optional)
```

```text
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  generate_data  │────▶│   load_data     │────▶│   break_data     │
│  (CSV files)    │     │  (PostgreSQL)   │     │    (optional)    │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ generate_report │◀────│     audit       │◀────│ validate_data    │
│ (MD + JSON)     │     │ (PostgreSQL)    │     │  (SQL + YAML)    │
└─────────────────┘     └─────────────────┘     └──────────────────┘
```

Validation rules are loaded from `config/validation_rules.yml` at runtime.

| Module | What it does |
| --- | --- |
| `pipeline/config.py` | Loads database settings from `.env` |
| `pipeline/db.py` | SQLAlchemy connection helpers |
| `pipeline/generate_data.py` | Builds clean CSV files with Faker and pandas |
| `pipeline/load_data.py` | Resets tables and loads CSVs into PostgreSQL |
| `pipeline/break_data.py` | Injects data quality issues for testing |
| `pipeline/validate_data.py` | Runs config-driven validation checks |
| `pipeline/audit.py` | Saves validation runs to PostgreSQL audit tables |
| `pipeline/generate_report.py` | Writes Markdown and JSON quality reports |
| `pipeline/run_dbt.py` | Runs dbt models and tests |
| `pipeline/main.py` | Runs the full workflow |

## Database Tables

### Core e-commerce tables

| Table | Description |
| --- | --- |
| `customers` | Customer names, email, and signup timestamp |
| `products` | Product name, category, and price |
| `orders` | Orders linked to customers |
| `order_items` | Line items linked to orders and products |
| `payments` | Payments linked to orders |

The main tables use foreign keys to keep relationships valid.

For broken relationship testing, the project uses a separate `staging_orders` table without constraints. That lets the pipeline demonstrate invalid references without modifying protected production tables.

Each pipeline run starts clean. The loader resets the main tables and removes simulator artifacts such as `staging_orders` and the `legacy_customer_code` column.

### PostgreSQL audit tables

PipelineGuard also stores validation run history in PostgreSQL. This makes it possible to review past runs without relying only on report files.

Audit tables are created in:

- `sql/01_create_tables.sql` for new database setups
- `sql/03_create_quality_audit_tables.sql` for applying the audit schema separately

#### `quality_runs`

One row per pipeline run.

| Column | Description |
| --- | --- |
| `run_id` | Unique run identifier (UUID) |
| `run_timestamp` | When the run was saved |
| `break_type` | Break scenario used, if any |
| `overall_status` | `PASS`, `WARNING`, or `FAIL` |
| `total_checks` | Total number of validation checks |
| `passed_checks` | Number of passing checks |
| `warning_checks` | Number of warning checks |
| `failed_checks` | Number of failing checks |

#### `quality_check_results`

One row per validation check result.

| Column | Description |
| --- | --- |
| `id` | Auto-incrementing primary key |
| `run_id` | Foreign key to `quality_runs` |
| `check_name` | Name of the validation check |
| `table_name` | Table checked |
| `status` | `PASS`, `WARNING`, or `FAIL` |
| `details` | Short explanation of the result |
| `recommendation` | Suggested next step |

Every run of `python -m pipeline.main` saves results through `pipeline/audit.py` and prints the saved `run_id`.

## Data Break Simulator

The break simulator injects realistic issues so validation can be tested beyond the happy path.

Supported break types:

| Break type | What it does |
| --- | --- |
| `missing_emails` | Clears email values for a sample of customers |
| `negative_payments` | Sets payment amounts to negative values |
| `future_order_dates` | Moves some orders into the future |
| `broken_foreign_keys` | Loads invalid customer references into `staging_orders` |
| `schema_drift` | Adds an unexpected column to the `customers` table |

## Config-Driven Validation Rules

Validation rules are defined in `config/validation_rules.yml`.

That file is the source of truth for:

- expected table names
- minimum row counts
- primary keys
- required columns
- null thresholds
- non-negative numeric checks
- foreign key checks where reasonable

This keeps the validation logic readable and makes it easier to extend the project without rewriting Python for every rule change.

## Schema Drift Detection

PipelineGuard compares the actual PostgreSQL columns for each configured table against the `required_columns` listed in `config/validation_rules.yml`.

For each table, the schema drift check returns:

- **PASS** if the schema matches exactly
- **WARNING** if there are unexpected extra columns
- **FAIL** if required columns are missing

You can trigger it intentionally with:

```bash
python -m pipeline.main --break schema_drift
```

## Validation Checks

Each check returns `PASS`, `WARNING`, or `FAIL`, along with details and a recommendation.

Current checks include:

| Check | What it looks for |
| --- | --- |
| Row counts | Minimum expected rows per configured table |
| Schema drift | Missing or extra columns vs. `required_columns` |
| Null emails | Customer email null rate above configured threshold |
| Negative payment amounts | Negative values in configured numeric columns |
| Future order dates | Orders dated after today |
| Invalid order customer references | Broken customer references in `staging_orders` |
| Invalid payment order references | Payments pointing to missing orders |

## Markdown Report Output

The Markdown report is written to `reports/quality_report.md`.

It includes:

- title and run timestamp
- overall status (`PASS`, `WARNING`, or `FAIL`)
- summary counts for total checks, passed, warnings, and failed
- a full table of check results
- a **Key Findings** section for warnings and failures only
- a short **How to Interpret This Report** section

Example overall statuses:

- **PASS** if there are no warnings or failures
- **WARNING** if there are warnings but no failures
- **FAIL** if one or more checks failed

This report is easy to read manually or share as documentation for a pipeline run.

## JSON Report Output

The JSON report is written to `reports/quality_report.json`.

It includes:

- `run_timestamp`
- `overall_status`
- `summary` counts
- `validation_results` list with the full result for each check

Example structure:

```json
{
  "run_timestamp": "2026-07-08 13:15:00",
  "overall_status": "PASS",
  "summary": {
    "total_checks": 11,
    "passed": 11,
    "warnings": 0,
    "failed": 0
  },
  "validation_results": []
}
```

The JSON file is useful for programmatic review, dashboards, or CI workflows where a machine-readable result is easier to process than Markdown.

## What the dbt Layer Does

After data is loaded into PostgreSQL, PipelineGuard can optionally build an analytics layer with dbt.

The dbt project lives in `dbt_pipelineguard/` and reads from the raw `public` schema tables. It builds:

- staging views for cleaned source data
- mart tables for reporting and analysis
- dbt tests for keys, relationships, and accepted values

Models are written to the `analytics` schema by default. Staging models are materialized as views, and mart models are materialized as tables.

This layer is optional. The Python validation engine can run on its own. dbt adds a familiar analytics transformation step on top of the same PostgreSQL database.

## Staging Models

Staging models live in `dbt_pipelineguard/models/staging/` and select from dbt sources in the `public` schema.

| Model | Source table | Purpose |
| --- | --- | --- |
| `stg_customers` | `customers` | Customer records with `has_email` |
| `stg_products` | `products` | Product catalog |
| `stg_orders` | `orders` | Orders with `is_future_order` |
| `stg_order_items` | `order_items` | Line items with `line_total` |
| `stg_payments` | `payments` | Payments with `is_paid` and `is_negative_payment` |

Transformations are intentionally light. The goal is to clean and document the raw data, not rebuild the whole pipeline in SQL.

## Mart Models

Mart models live in `dbt_pipelineguard/models/marts/` and are built from staging models.

| Model | Grain | Purpose |
| --- | --- | --- |
| `fact_orders` | one row per order | Order details, order totals, and payment info |
| `customer_order_summary` | one row per customer | Order counts, spend totals, first and latest order dates |
| `payment_quality_summary` | one summary row | Payment counts, negative payments, and failed/pending totals |

These marts make it easier to explore customer behavior and payment quality after the pipeline runs.

## dbt Tests

dbt tests are defined in:

- `dbt_pipelineguard/models/sources/sources.yml`
- `dbt_pipelineguard/models/staging/schema.yml`
- `dbt_pipelineguard/models/marts/schema.yml`

They cover:

- `not_null` and `unique` on primary keys
- `not_null` on important foreign keys
- `relationships` between staging models
- `accepted_values` for order and payment statuses generated by the Python pipeline

Mart tests include basic checks such as unique order IDs and not-null summary metrics.

## How dbt Complements the Python Validation Engine

The Python validation engine and dbt solve related but different problems.

**Python validation** (`pipeline/validate_data.py`):

- runs configurable data quality checks from `config/validation_rules.yml`
- supports the break simulator and audit logging
- produces Markdown and JSON reports
- is focused on pipeline-level quality checks

**dbt layer**:

- models the data for analytics use cases
- tests assumptions during transformation
- documents tables and columns in the dbt project
- builds reusable marts on top of the same PostgreSQL data

In practice, Python validation answers: "Is this dataset safe to use right now?"

dbt helps answer: "Can I reliably transform and analyze this data downstream?"

They work well together because both layers operate on the same database, but they check the data from different angles.

## How to Run dbt Manually

Make sure PostgreSQL is running and the raw tables are loaded first.

From the project root:

```bash
python -m pipeline.run_dbt --run
python -m pipeline.run_dbt --test
python -m pipeline.run_dbt --all
```

You can also run dbt directly:

```bash
cd dbt_pipelineguard
dbt run
dbt test
```

## How to Run the Full Pipeline with dbt

To run the Python pipeline and then execute dbt models and tests:

```bash
python -m pipeline.main --run-dbt
```

You can combine this with a break scenario:

```bash
python -m pipeline.main --break negative_payments --run-dbt
```

When `--run-dbt` is provided, PipelineGuard runs the normal workflow first, then runs `dbt run` and `dbt test` after report generation.

## How to Query Recent Pipeline Runs

After running the pipeline, you can inspect run history directly in PostgreSQL.

Recent runs:

```sql
SELECT
    run_id,
    run_timestamp,
    break_type,
    overall_status,
    total_checks,
    passed_checks,
    warning_checks,
    failed_checks
FROM quality_runs
ORDER BY run_timestamp DESC
LIMIT 10;
```

Check results for a specific run:

```sql
SELECT
    check_name,
    table_name,
    status,
    details,
    recommendation
FROM quality_check_results
WHERE run_id = '<run_id>'
ORDER BY id;
```

Failed checks across recent runs:

```sql
SELECT
    r.run_timestamp,
    r.break_type,
    c.check_name,
    c.table_name,
    c.details
FROM quality_check_results c
JOIN quality_runs r ON c.run_id = r.run_id
WHERE c.status = 'FAIL'
ORDER BY r.run_timestamp DESC;
```

When you run `python -m pipeline.main`, the saved run ID is printed in the terminal:

```text
Saved quality run: 3f1c8b2a-...
```

## How to Run the Project

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts PostgreSQL and runs the SQL files in `sql/` to create the tables.

### 2. Set up environment variables

```bash
cp .env.example .env
```

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
python -m pipeline.main
```

## Example Commands

Clean run:

```bash
python -m pipeline.main
```

Run the full pipeline with dbt:

```bash
python -m pipeline.main --run-dbt
```

Run with a specific data break:

```bash
python -m pipeline.main --break missing_emails
python -m pipeline.main --break negative_payments
python -m pipeline.main --break future_order_dates
python -m pipeline.main --break broken_foreign_keys
python -m pipeline.main --break schema_drift
python -m pipeline.main --break negative_payments --run-dbt
```

Run individual steps:

```bash
python -m pipeline.generate_data
python -m pipeline.load_data
python -m pipeline.break_data --issue schema_drift
python -m pipeline.validate_data
python -m pipeline.audit
python -m pipeline.generate_report
python -m pipeline.run_dbt --all
```

Test the database connection:

```bash
python -m pipeline.db
```

## What I Learned

Building run history into the project helped me think about validation as something worth tracking over time, not just checking once per run.

A few things that stood out:

- Moving rules into YAML made the project easier to extend and explain.
- Schema drift is a useful check, not just row counts or null values.
- Saving run history in PostgreSQL makes it easier to compare clean runs vs. broken runs.
- Markdown is good for humans; JSON is good for tools.
- dbt is a useful second layer for analytics modeling and transformation testing.

## Future Improvements

If I keep building on this project, I would likely add:

- duplicate primary key checks driven by the YAML config
- payment total vs. order item reconciliation
- a simple CLI command to list recent audit runs
- basic tests around validation and audit logic
- support for running multiple break scenarios in one pipeline execution
- more dbt marts and documentation

## Project Structure

```text
pipelineguard/
├── config/
│   └── validation_rules.yml
├── dbt_pipelineguard/
│   ├── dbt_project.yml
│   └── models/
│       ├── sources/
│       ├── staging/
│       └── marts/
├── pipeline/
│   ├── config.py
│   ├── db.py
│   ├── generate_data.py
│   ├── load_data.py
│   ├── break_data.py
│   ├── validate_data.py
│   ├── audit.py
│   ├── generate_report.py
│   ├── run_dbt.py
│   └── main.py
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_reset_tables.sql
│   └── 03_create_quality_audit_tables.sql
├── data/generated/
├── reports/
├── docs/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

Portfolio project focused on synthetic relational data, PostgreSQL, data quality validation, and a small dbt analytics layer.
