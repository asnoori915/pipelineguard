# PipelineGuard Architecture

PipelineGuard is a small data quality pipeline built around PostgreSQL. Each step has a clear job, and the workflow runs from data generation through validation, reporting, and optional analytics modeling with dbt.

## End-to-End Flow

```text
Synthetic Data Generator
        ↓
PostgreSQL Raw Tables
        ↓
Data Break Simulator (optional)
        ↓
Python Validation Engine
        ↓
Quality Reports + Audit Tables
        ↓
dbt Staging Models
        ↓
dbt Mart Models
        ↓
dbt Tests
```

The dbt layer is optional. It runs after the Python pipeline when `--run-dbt` is provided or when dbt is run manually.

## Component Overview

### Synthetic Data Generator

**Module:** `pipeline/generate_data.py`

Creates clean, relationally valid synthetic data for a simple e-commerce schema. It uses Faker and pandas to build CSV files for customers, products, orders, order_items, and payments.

Foreign keys are respected during generation so orders reference real customers, order items reference real orders and products, and payments reference real orders.

### PostgreSQL Raw Tables

**Module:** `pipeline/load_data.py`

Loads generated CSV files into PostgreSQL raw tables in the `public` schema. Before loading, it:

- runs `sql/02_reset_tables.sql` to clear existing data
- drops `staging_orders` if it exists
- removes simulator artifacts such as `legacy_customer_code`

Tables are loaded in dependency order:

1. customers
2. products
3. orders
4. order_items
5. payments

Database connection settings come from `.env` through `pipeline/config.py` and `pipeline/db.py`.

### Data Break Simulator

**Module:** `pipeline/break_data.py`

Injects realistic data quality issues on purpose so validation can be tested.

Supported break types:

- `missing_emails`
- `negative_payments`
- `future_order_dates`
- `broken_foreign_keys`
- `schema_drift`

This step is optional. In a normal clean run, the pipeline skips it.

#### How `staging_orders` is used for broken foreign key simulation

The main `orders` table is protected by PostgreSQL foreign key constraints. Instead of breaking those tables directly, the simulator creates a separate `staging_orders` table without foreign keys and loads invalid customer references there.

Validation checks `staging_orders` with SQL joins to find broken relationships.

#### How schema drift simulation works

The `schema_drift` break adds an unexpected column such as `legacy_customer_code` to `customers`. Validation compares actual PostgreSQL columns against `required_columns` in `config/validation_rules.yml` and reports a **WARNING** for extra columns.

### Python Validation Engine

**Module:** `pipeline/validate_data.py`

**Config:** `config/validation_rules.yml`

Validation rules are loaded from YAML. That file defines:

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

Current checks include row counts, schema drift, null emails, negative payments, future order dates, and invalid foreign key references.

#### Why config-driven validation is useful

Validation rules often change over time. Using YAML keeps the rules easier to read, update, and explain without changing Python code for every rule adjustment.

### Quality Reports + Audit Tables

**Modules:** `pipeline/generate_report.py`, `pipeline/audit.py`

After validation, PipelineGuard writes:

- `reports/quality_report.md`
- `reports/quality_report.json`

It also saves run history to PostgreSQL:

- `quality_runs` — one row per pipeline run
- `quality_check_results` — one row per validation check

This gives both human-readable reports and queryable audit history.

### dbt Staging Models

**Project:** `dbt_pipelineguard/models/staging/`

dbt reads from the raw `public` schema tables and builds staging views in the `analytics` schema.

Examples:

- `stg_customers`
- `stg_products`
- `stg_orders`
- `stg_order_items`
- `stg_payments`

Staging models apply light SQL transformations such as casts, simple flags like `is_paid`, and calculated fields like `line_total`.

### dbt Mart Models

**Project:** `dbt_pipelineguard/models/marts/`

Mart models are materialized as tables and built from staging models.

Examples:

- `fact_orders` — one row per order with totals and payment info
- `customer_order_summary` — one row per customer with order and spend metrics
- `payment_quality_summary` — payment quality metrics in one summary row

These models turn raw operational data into analytics-ready datasets.

### dbt Tests

**Project:** `dbt_pipelineguard/models/sources/`, `staging/`, and `marts/`

dbt tests add another layer of checks during transformation.

They include:

- `not_null` and `unique` on primary keys
- `not_null` on important foreign keys
- `relationships` between staging models
- `accepted_values` for order and payment statuses
- basic mart tests on key summary columns

## How dbt Adds Value

dbt complements the Python validation engine in three main ways:

### SQL transformation

dbt handles the SQL layer for cleaning and preparing data after it lands in PostgreSQL. Staging models document how raw tables are transformed before analytics use.

### Analytics modeling

Mart models create reusable business tables such as order facts and customer summaries. This makes downstream analysis easier than querying raw tables directly.

### Additional data tests

Python validation focuses on pipeline-level quality checks and reporting. dbt adds transformation-time tests that confirm keys, relationships, and expected values still hold during modeling.

Together, the two layers check data at different points:

- Python validation asks whether the loaded dataset is usable
- dbt tests ask whether the transformed analytics models are trustworthy

## Orchestration

**Module:** `pipeline/main.py`

Run the Python pipeline:

```bash
python -m pipeline.main
```

Run with a data break:

```bash
python -m pipeline.main --break missing_emails
python -m pipeline.main --break schema_drift
```

Run the full pipeline plus dbt:

```bash
python -m pipeline.main --run-dbt
```

Run dbt manually:

```bash
python -m pipeline.run_dbt --all
```

## How This Relates to Real Data Engineering Workflows

PipelineGuard follows a simplified version of a common pattern:

1. **Generate or ingest data**
2. **Load raw tables**
3. **Validate quality**
4. **Store audit history and reports**
5. **Transform data for analytics**
6. **Test transformed models**

In production systems, these steps may span ingestion tools, orchestration, dbt projects, and custom validation frameworks. PipelineGuard keeps the same ideas on a smaller scale:

- synthetic data stands in for source data
- PostgreSQL holds both raw and analytics layers
- Python validation stands in for pipeline quality checks
- audit tables stand in for run history
- dbt stands in for analytics modeling and transformation tests

The goal is not to replicate an enterprise platform. It is to practice how raw data, validation, and analytics modeling fit together.

## Infrastructure

PostgreSQL runs in Docker Compose. Table creation scripts live in `sql/01_create_tables.sql` and are applied automatically when the database container starts.

Validation rules live in `config/validation_rules.yml`.

The dbt project lives in `dbt_pipelineguard/` and uses the `pipelineguard` profile.
