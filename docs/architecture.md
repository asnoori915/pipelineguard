# PipelineGuard Architecture

PipelineGuard is a small data quality pipeline built around PostgreSQL. Each step has a clear job, and the workflow runs in order from data generation to reporting.

## End-to-End Flow

```text
Synthetic Data Generator
        ↓
CSV files in data/generated
        ↓
PostgreSQL Loader
        ↓
Optional Data Break Simulator
        ↓
Validation Checks
        ↓
Markdown Quality Report
```

## Component Overview

### Synthetic Data Generator

**Module:** `pipeline/generate_data.py`

Creates clean, relationally valid synthetic data for a simple e-commerce schema. It uses Faker and pandas to build CSV files for customers, products, orders, order_items, and payments.

Foreign keys are respected during generation so orders reference real customers, order items reference real orders and products, and payments reference real orders.

### CSV Files in `data/generated`

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

Loads the generated CSV files into PostgreSQL. Before loading, it runs `sql/02_reset_tables.sql` to clear existing data.

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

Supported issue types:

- `missing_emails`
- `negative_payments`
- `future_order_dates`
- `broken_foreign_keys`

This step is optional. In a normal clean run, the pipeline skips it. When enabled, it helps demonstrate how validation catches real-world problems.

Broken foreign key examples are written to a `staging_orders` table without constraints, so production tables stay protected while relationship checks can still be tested.

### Validation Checks

**Module:** `pipeline/validate_data.py`

Runs SQL-based checks against the database and returns a result for each check with:

- check name
- table
- status (`PASS`, `WARNING`, or `FAIL`)
- details
- recommendation

Current checks include row counts, null emails, negative payments, future order dates, and invalid foreign key references.

### Markdown Quality Report

**Module:** `pipeline/generate_report.py`

Uses the validation results to create `reports/quality_report.md`.

The report includes:

- project name
- run timestamp
- summary counts for pass, warning, and fail
- detailed check results
- recommendations

## Orchestration

**Module:** `pipeline/main.py`

Runs the full workflow from one command:

```bash
python -m pipeline.main
```

You can also inject a data break before validation:

```bash
python -m pipeline.main --break missing_emails
```

## Infrastructure

PostgreSQL runs in Docker Compose. Table creation scripts live in `sql/01_create_tables.sql` and are applied automatically when the database container starts.
