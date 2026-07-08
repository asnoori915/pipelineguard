# PipelineGuard V2 Architecture

PipelineGuard is a small data quality pipeline built around PostgreSQL. Each step has a clear job, and the workflow runs in order from data generation to reporting.

V2 adds config-driven validation, schema drift detection, and a clearer quality report.

## End-to-End Flow

```text
Synthetic Data Generator
        ↓
CSV files
        ↓
PostgreSQL Loader
        ↓
Optional Data Break Simulator
        ↓
Config-Driven Validation Engine
        ↓
Schema Drift Detection
        ↓
Markdown Quality Report
```

In practice, schema drift detection runs as part of the validation engine. It is shown separately here because it is one of the main additions in V2.

## Component Overview

### Synthetic Data Generator

**Module:** `pipeline/generate_data.py`

Creates clean, relationally valid synthetic data for a simple e-commerce schema. It uses Faker and pandas to build CSV files for customers, products, orders, order_items, and payments.

Foreign keys are respected during generation so orders reference real customers, order items reference real orders and products, and payments reference real orders.

### CSV Files

**Location:** `data/generated/`

These files are the handoff point between generation and loading. Each table gets its own CSV file, which makes the pipeline easy to inspect and rerun.

Example files:

- `customers.csv`
- `products.csv`
- `orders.csv`
- `order_items.csv`
- `payments.csv`

### PostgreSQL Loader

**Module:** `pipeline/load_data.py`

Loads the generated CSV files into PostgreSQL. Before loading, it runs `sql/02_reset_tables.sql` to clear existing data and drops `staging_orders` if it exists from a previous run.

Tables are loaded in dependency order:

1. customers
2. products
3. orders
4. order_items
5. payments

Database connection settings come from `.env` through `pipeline/config.py` and `pipeline/db.py`.

### Optional Data Break Simulator

**Module:** `pipeline/break_data.py`

Injects realistic data quality issues on purpose so validation can be tested.

Supported break types:

- `missing_emails`
- `negative_payments`
- `future_order_dates`
- `broken_foreign_keys`
- `schema_drift`

This step is optional. In a normal clean run, the pipeline skips it. When enabled, it helps demonstrate how validation catches real-world problems.

#### How `staging_orders` is used for broken foreign key simulation

The main `orders` table is protected by PostgreSQL foreign key constraints. That means invalid customer references cannot be inserted directly without disabling constraints or changing the schema.

Instead, the break simulator creates a separate `staging_orders` table without foreign keys and loads rows that reference a non-existent `customer_id`.

Validation then checks `staging_orders` with a SQL join to find broken relationships. This keeps the demo realistic while leaving the main tables intact.

Each pipeline run starts clean because the loader drops `staging_orders` before reloading data.

#### How schema drift simulation works

The `schema_drift` break adds an unexpected column to a table, such as:

```sql
ALTER TABLE customers ADD COLUMN IF NOT EXISTS legacy_customer_code TEXT;
```

Validation compares the actual PostgreSQL columns against the `required_columns` listed in `config/validation_rules.yml`.

If the table contains extra columns that are not in the config, validation returns a **WARNING**. If required columns are missing, validation returns a **FAIL**.

### Config-Driven Validation Engine

**Module:** `pipeline/validate_data.py`

**Config:** `config/validation_rules.yml`

Validation rules are loaded from YAML instead of being hardcoded in Python. That file defines:

- expected table names
- minimum row counts
- primary keys
- required columns
- null thresholds
- non-negative numeric checks
- foreign key checks where reasonable

Each check returns:

- check name
- table
- status (`PASS`, `WARNING`, or `FAIL`)
- details
- recommendation

Current checks include row counts, null emails, negative payments, future order dates, invalid foreign key references, and schema drift.

#### Why config-driven validation is useful

In real data engineering work, validation rules often change over time. Thresholds get adjusted, new columns are added, and teams want checks that are easy to review without digging through application code.

Using a YAML config makes the rules:

- easier to read
- easier to update
- easier to explain in documentation or interviews

It also mirrors how many teams separate pipeline logic from validation configuration.

### Schema Drift Detection

Schema drift detection compares each table's actual PostgreSQL columns against the `required_columns` in `config/validation_rules.yml`.

Results:

- **PASS** when the schema matches exactly
- **WARNING** when there are unexpected extra columns
- **FAIL** when required columns are missing

This helps catch cases where a database changed but the expected schema did not.

### Markdown Quality Report

**Module:** `pipeline/generate_report.py`

Uses the validation results to create `reports/quality_report.md`.

The report includes:

- title and run timestamp
- overall status
- summary counts for total checks, passed, warnings, and failed
- a full table of check results
- a **Key Findings** section for warnings and failures
- a short guide on how to interpret the report

## Orchestration

**Module:** `pipeline/main.py`

Runs the full workflow from one command:

```bash
python -m pipeline.main
```

You can also inject a data break before validation:

```bash
python -m pipeline.main --break missing_emails
python -m pipeline.main --break schema_drift
```

## How This Relates to Real Data Engineering Workflows

PipelineGuard is simplified, but it follows a pattern that shows up in real projects:

1. **Generate or ingest data** into a staging area
2. **Load it into a database**
3. **Validate structure and quality**
4. **Report issues before downstream use**

In production systems, those steps might involve orchestration tools, dbt tests, Great Expectations, or custom SQL checks. PipelineGuard keeps the same idea on a smaller scale:

- synthetic data stands in for source data
- PostgreSQL stands in for the warehouse or operational database
- YAML config stands in for maintainable validation rules
- the break simulator stands in for bad upstream changes or load errors
- the Markdown report stands in for data quality monitoring output

The goal is not to replicate an enterprise platform. It is to practice the workflow of checking data before trusting it.

## Infrastructure

PostgreSQL runs in Docker Compose. Table creation scripts live in `sql/01_create_tables.sql` and are applied automatically when the database container starts.

Validation rules live in `config/validation_rules.yml` and are read at runtime by the validation engine.
