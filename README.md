# PipelineGuard

PipelineGuard is a portfolio project I built to practice data quality validation with synthetic relational data in PostgreSQL.

It generates a small e-commerce dataset, loads it into the database, optionally breaks the data on purpose, runs validation checks, and writes a Markdown report with the results.

## Why I Built This

The idea came from working with database-oriented synthetic data workflows and noticing how much time goes into generating and loading data — but less into checking whether that data is actually usable.

I wanted a small project where I could focus on that second part: validating row counts, null values, bad dates, invalid relationships, and other common issues that show up in real datasets.

PipelineGuard gave me a simple place to practice:

- building a relational schema
- generating synthetic data with valid foreign keys
- writing SQL validation checks
- putting the whole flow into one repeatable script

It is not meant to be production infrastructure. It is a learning project that helped me get more comfortable thinking about data quality as part of the pipeline, not something you only worry about after something breaks downstream.

## Tech Stack

- Python
- PostgreSQL 16
- Docker Compose
- SQL
- pandas
- Faker
- SQLAlchemy
- python-dotenv
- tabulate

## Architecture

The pipeline runs in a straight line:

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
│ (Markdown)      │     │  (SQL checks)   │     │                  │
└─────────────────┘     └─────────────────┘     └──────────────────┘
```

| Module | What it does |
| --- | --- |
| `pipeline/config.py` | Loads database settings from `.env` |
| `pipeline/db.py` | SQLAlchemy connection helpers |
| `pipeline/generate_data.py` | Builds clean CSV files with Faker and pandas |
| `pipeline/load_data.py` | Resets tables and loads CSVs into PostgreSQL |
| `pipeline/break_data.py` | Injects data quality issues for testing |
| `pipeline/validate_data.py` | Runs validation checks |
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

The main tables use foreign keys to keep relationships valid. For broken relationship testing, the project uses a separate `staging_orders` table without constraints so invalid references can be demonstrated without modifying protected production tables.

## Data Break Simulator

One thing I wanted in this project was a way to test validation, not just happy-path data.

The break simulator injects realistic issues like:

| Issue | What it does |
| --- | --- |
| `missing_emails` | Clears email values for a sample of customers |
| `negative_payments` | Sets payment amounts to negative values |
| `future_order_dates` | Moves some orders into the future |
| `broken_foreign_keys` | Loads invalid customer references into `staging_orders` |

This made it much easier to confirm that the checks fail when they should.

## Validation Checks

Each check returns `PASS`, `WARNING`, or `FAIL`, along with details and a recommendation.

| Check | Table | What it looks for |
| --- | --- | --- |
| Row counts | all | Minimum expected rows per table |
| Null emails | `customers` | Missing email addresses |
| Negative payment amounts | `payments` | Payments below zero |
| Future order dates | `orders` | Orders dated after today |
| Invalid order customer references | `staging_orders` | Orders pointing to missing customers |
| Invalid payment order references | `payments` | Payments pointing to missing orders |

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
```

Run individual steps:

```bash
python -m pipeline.generate_data
python -m pipeline.load_data
python -m pipeline.break_data --issue negative_payments
python -m pipeline.validate_data
python -m pipeline.generate_report
```

Test the database connection:

```bash
python -m pipeline.db
```

## Example Quality Report Summary

After a clean run, `reports/quality_report.md` might look like this:

```markdown
# PipelineGuard Data Quality Report

**Run timestamp:** 2026-07-05 12:00:00

## Summary

| Status | Count |
| --- | ---: |
| PASS | 6 |
| WARNING | 0 |
| FAIL | 0 |

## Recommendations

- All checks passed. No action needed.
```

After injecting missing emails:

```markdown
## Summary

| Status | Count |
| --- | ---: |
| PASS | 5 |
| WARNING | 0 |
| FAIL | 1 |

## Recommendations

- **null_emails** (FAIL): Backfill missing customer emails or remove invalid customer records.
```

## What I Learned

The most useful part of this project for me was connecting generation, loading, and validation in one workflow.

A few things that stood out:

- A successful load does not automatically mean the data is valid.
- Relationship checks matter, especially when row counts look fine.
- It helps to deliberately break the data and confirm your checks catch the issue.
- A simple Markdown report is enough to make results easy to review.

## Future Improvements

If I continue building on this project, I would likely add:

- duplicate primary key checks
- schema drift detection
- payment total vs. order item reconciliation
- JSON export for CI use
- basic tests around the validation logic

## Project Structure

```text
pipelineguard/
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
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

Portfolio project focused on synthetic relational data, PostgreSQL, and basic data quality validation.
