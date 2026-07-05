# PipelineGuard

PipelineGuard is a data engineering portfolio project that simulates a small e-commerce data pipeline. It generates synthetic relational data, loads it into PostgreSQL, optionally injects realistic data quality issues, runs validation checks, and produces a Markdown quality report.

The goal is to show how I think about **data quality end to end** — not just moving data, but verifying that it is complete, consistent, and safe to use downstream.

## Why I Built This

I built PipelineGuard because I wanted a hands-on project focused on **data quality**, not just ETL mechanics. In real pipelines, bad data often shows up as missing values, invalid relationships, impossible dates, or incorrect amounts. Those problems are easy to miss if you only check whether a job finished successfully.

This project let me practice:

- Designing a simple relational schema
- Generating realistic synthetic data with valid foreign keys
- Writing SQL-based validation checks
- Building a repeatable workflow I could explain clearly in an interview

It reflects my interest in data engineering and making pipelines more trustworthy before data reaches dashboards, models, or reports.

## Tech Stack

| Layer | Tools |
| --- | --- |
| Language | Python |
| Database | PostgreSQL 16 |
| Infrastructure | Docker Compose |
| Data generation | pandas, Faker |
| Database access | SQLAlchemy, psycopg2 |
| Configuration | python-dotenv |
| Reporting | Markdown, tabulate |

## Architecture

PipelineGuard follows a linear workflow: generate, load, optionally break, validate, and report.

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

**Pipeline modules**

| Module | Purpose |
| --- | --- |
| `pipeline/config.py` | Loads database settings from `.env` |
| `pipeline/db.py` | SQLAlchemy engine and connection helpers |
| `pipeline/generate_data.py` | Creates clean synthetic CSV files |
| `pipeline/load_data.py` | Resets tables and loads CSVs into PostgreSQL |
| `pipeline/break_data.py` | Injects data quality issues for testing |
| `pipeline/validate_data.py` | Runs validation checks against the database |
| `pipeline/generate_report.py` | Writes `reports/quality_report.md` |
| `pipeline/main.py` | Runs the full workflow from one command |

## Database Tables

The schema models a simple e-commerce store:

| Table | Description |
| --- | --- |
| `customers` | Customer profile data including email and signup timestamp |
| `products` | Product catalog with category and price |
| `orders` | Orders linked to customers |
| `order_items` | Line items linked to orders and products |
| `payments` | Payments linked to orders |

Foreign keys enforce referential integrity across the main tables. For broken relationship testing, the project also uses a `staging_orders` table without constraints so invalid references can be demonstrated safely.

## Data Break Simulator

PipelineGuard includes a **data break simulator** that injects realistic data quality issues on purpose. This makes it possible to test whether validation checks actually catch problems.

Supported issue types:

| Issue | What it simulates |
| --- | --- |
| `missing_emails` | Customer records with null email addresses |
| `negative_payments` | Payment rows with negative amounts |
| `future_order_dates` | Orders dated in the future |
| `broken_foreign_keys` | Order rows in `staging_orders` that reference non-existent customers |

Production tables stay protected by PostgreSQL constraints. Broken foreign key examples are loaded into `staging_orders` so the pipeline can still demonstrate relationship validation without fighting database constraints.

## Validation Checks

Each check returns a result with `PASS`, `WARNING`, or `FAIL` status, plus details and a recommendation.

| Check | Table | What it validates |
| --- | --- | --- |
| Row counts | all | Expected minimum row counts per table |
| Null emails | `customers` | Customers missing email addresses |
| Negative payment amounts | `payments` | Payments with amount less than zero |
| Future order dates | `orders` | Orders with dates after today |
| Invalid order customer references | `staging_orders` | Orders pointing to missing customers |
| Invalid payment order references | `payments` | Payments pointing to missing orders |

## How to Run the Project

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts PostgreSQL and runs the SQL files in `sql/` to create the base tables.

### 2. Configure environment variables

```bash
cp .env.example .env
```

### 3. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the full pipeline

```bash
python -m pipeline.main
```

## Example Commands

Run the full workflow with clean data:

```bash
python -m pipeline.main
```

Run the workflow and inject a specific data quality issue:

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

After a clean run, `reports/quality_report.md` looks like this:

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

Building PipelineGuard helped me connect data generation, loading, and validation in one repeatable workflow.

A few takeaways:

- **Validation should be explicit.** Finishing a load step does not mean the data is trustworthy.
- **Referential integrity matters.** Relationship checks catch issues that row counts alone will miss.
- **Testing bad data is useful.** The break simulator made it much easier to confirm that checks fail for the right reasons.
- **Simple reporting goes a long way.** A Markdown summary with recommendations is easy to review and share.

## Future Improvements

Possible next steps for this project:

- Add duplicate primary key and schema drift checks
- Validate order totals against payment amounts
- Add a CLI flag to run multiple break scenarios in one execution
- Export validation results to JSON for CI/CD pipelines
- Schedule recurring quality checks with a lightweight orchestrator
- Add basic unit tests for validation logic

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

Built as a portfolio project to practice data engineering, relational modeling, and data quality validation.
