# PipelineGuard

PipelineGuard is a data engineering portfolio project that validates synthetic relational data in PostgreSQL.

The project generates clean synthetic data, intentionally injects common data quality issues, validates the database, and produces a Markdown quality report.

## Why I Built This

I built PipelineGuard to practice data engineering concepts around relational databases, synthetic data validation, and data quality monitoring. The project is inspired by real workflow testing experience where validating generated data structure, relationships, and quality is just as important as generating the data itself.

## Tech Stack

- Python

- PostgreSQL

- Docker Compose

- SQL

- pandas

- Faker

## Core Features

- Generate synthetic relational data

- Load data into PostgreSQL

- Inject realistic data quality issues

- Validate row counts, nulls, duplicates, foreign keys, negative values, and future dates

- Generate a Markdown data quality report

## Database Tables

- customers

- products

- orders

- order_items

- payments

## Project Status

In progress.