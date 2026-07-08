# PipelineGuard V2

PipelineGuard is a portfolio project I built to practice data quality validation with synthetic relational data in PostgreSQL.

Version 2 adds config-driven validation rules, schema drift detection, and a clearer quality report. The core idea is the same: generate data, load it, optionally break it on purpose, validate it, and review the results.

## Project Overview

PipelineGuard simulates a small e-commerce data pipeline with five related tables. It generates clean synthetic CSV files, loads them into PostgreSQL, runs validation checks, and writes a Markdown report.

What makes V2 different is that many validation rules live in a YAML config file instead of being hardcoded. That makes the checks easier to adjust and easier to explain.

The project also includes a data break simulator so I can inject common data quality issues and confirm the validation layer catches them.

## Why I Built This

The idea came from working with database-oriented synthetic data workflows and wanting to understand data quality validation more directly.

Generating and loading data is only part of the job. I also wanted practice checking whether the data is complete, consistent, and structurally correct before anything downstream depends on it.

PipelineGuard V2 helped me work on:

- relational schema design
- synthetic data generation with valid foreign keys
- SQL-based validation checks
- config-driven rules
- simple reporting for data quality results

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

## Architecture Flow

```text
generate_data → load_data → break_data (optional) → validate_data → generate_report
```

```text
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  generate_data  │────▶│   load_data     │────▶│   break_data     │
│  (CSV files)    │     │  (PostgreSQL)   │     │    (optional)    │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ generate_report │◀────│ validate_data   │◀────│   PostgreSQL     │
│ (Markdown)      │     │  (SQL + YAML)   │     │                  │
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
| `pipeline/generate_report.py` | Writes `reports/quality_report.md` |
| `pipeline/main.py` | Runs the full workflow |

## Database Tables

The schema is a simple e-commerce model:

| Table | Description |
| --- | --- |
| `customers` | Customer names, email, and signup timestamp |
| `products` | Product name, category, and price |
| `orders` | Orders linked to customers |
| `order_items` | Line items linked to orders and products |
| `payments` | Payments linked to orders |

The main tables use foreign keys to keep relationships valid.

For broken relationship testing, the project uses a separate `staging_orders` table without constraints. That lets the pipeline demonstrate invalid references without modifying protected production tables.

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

Each pipeline run starts clean. The loader resets the main tables and drops `staging_orders` if it exists from a previous broken foreign key test.

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

Example rule areas in the YAML file:

- `min_rows` for row count checks
- `required_columns` for schema validation
- `checks.null_thresholds` for null rate limits
- `checks.non_negative` for numeric validation
- `foreign_keys` for relationship checks

This keeps the validation logic readable and makes it easier to extend the project without rewriting Python for every rule change.

## Schema Drift Detection

PipelineGuard V2 compares the actual PostgreSQL columns for each configured table against the `required_columns` listed in `config/validation_rules.yml`.

For each table, the schema drift check returns:

- **PASS** if the schema matches exactly
- **WARNING** if there are unexpected extra columns
- **FAIL** if required columns are missing

This is useful for catching cases where a table changed over time but the pipeline rules did not.

You can trigger it intentionally with:

```bash
python -m pipeline.main --break schema_drift
```

That adds an unexpected column such as `legacy_customer_code` to `customers`, which validation reports as schema drift.

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

## Quality Report Output

The report is written to `reports/quality_report.md`.

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

Run with a specific data break:

```bash
python -m pipeline.main --break missing_emails
python -m pipeline.main --break negative_payments
python -m pipeline.main --break future_order_dates
python -m pipeline.main --break broken_foreign_keys
python -m pipeline.main --break schema_drift
```

Run individual steps:

```bash
python -m pipeline.generate_data
python -m pipeline.load_data
python -m pipeline.break_data --issue schema_drift
python -m pipeline.validate_data
python -m pipeline.generate_report
```

Test the database connection:

```bash
python -m pipeline.db
```

## What I Learned

V2 pushed me to think more clearly about how validation rules should be defined and maintained.

A few things that stood out:

- Moving rules into YAML made the project easier to extend and explain.
- Schema drift is a useful check, not just row counts or null values.
- Breaking the data on purpose is still one of the best ways to test validation.
- A simple Markdown report with overall status and key findings is enough to make results useful.

## Future Improvements

If I keep building on this project, I would likely add:

- duplicate primary key checks driven by the YAML config
- payment total vs. order item reconciliation
- JSON export for CI use
- basic tests around validation logic
- support for running multiple break scenarios in one pipeline execution

## Project Structure

```text
pipelineguard/
├── config/
│   └── validation_rules.yml
├── pipeline/
│   ├── config.py
│   ├── db.py
│   ├── generate_data.py
│   ├── load_data.py
│   ├── break_data.py
│   ├── validate_data.py
│   ├── generate_report.py
│   └── main.py
├── sql/
│   ├── 01_create_tables.sql
│   └── 02_reset_tables.sql
├── data/generated/
├── reports/
├── docs/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

Portfolio project focused on synthetic relational data, PostgreSQL, and practical data quality validation.
