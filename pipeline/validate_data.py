from pathlib import Path

import yaml
from sqlalchemy import text
from tabulate import tabulate

from pipeline.db import get_engine

RULES_PATH = Path("config/validation_rules.yml")


def load_validation_rules(path: Path = RULES_PATH) -> dict:
    """Load validation rules from the YAML config file."""
    with path.open(encoding="utf-8") as rules_file:
        return yaml.safe_load(rules_file)


def _make_result(
    check_name: str,
    table: str,
    status: str,
    details: str,
    recommendation: str,
) -> dict:
    return {
        "check_name": check_name,
        "table": table,
        "status": status,
        "details": details,
        "recommendation": recommendation,
    }


def check_row_counts(engine, rules: dict) -> dict:
    tables = rules["tables"]
    counts = {}

    with engine.connect() as conn:
        for table_name, table_rules in tables.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            counts[table_name] = result.scalar()

    detail_parts = [
        f"{table}: {counts[table]} (expected >= {table_rules['min_rows']})"
        for table, table_rules in tables.items()
    ]
    details = "; ".join(detail_parts)

    if any(count == 0 for count in counts.values()):
        status = "FAIL"
        recommendation = "Reload the pipeline data because one or more tables are empty."
    elif any(
        counts[table] < table_rules["min_rows"]
        for table, table_rules in tables.items()
    ):
        status = "WARNING"
        recommendation = "Review the load step because row counts are below expected minimums."
    else:
        status = "PASS"
        recommendation = "No action needed."

    return _make_result("row_counts", "all", status, details, recommendation)


def check_required_columns(engine, rules: dict) -> dict:
    tables = rules["tables"]
    missing_columns = []

    with engine.connect() as conn:
        for table_name, table_rules in tables.items():
            existing_columns = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                    """
                ),
                {"table_name": table_name},
            ).scalars().all()
            existing_column_set = set(existing_columns)

            for column_name in table_rules["required_columns"]:
                if column_name not in existing_column_set:
                    missing_columns.append(f"{table_name}.{column_name}")

    if missing_columns:
        details = "Missing required columns: " + ", ".join(missing_columns)
        status = "FAIL"
        recommendation = "Update the database schema so all required columns exist."
    else:
        details = "All required columns exist for configured tables."
        status = "PASS"
        recommendation = "No action needed."

    return _make_result("required_columns", "all", status, details, recommendation)


def check_null_emails(engine, rules: dict) -> dict:
    customer_rules = rules["tables"]["customers"]
    threshold = (
        customer_rules.get("checks", {})
        .get("null_thresholds", {})
        .get("email", 0)
    )

    with engine.connect() as conn:
        null_count = conn.execute(
            text("SELECT COUNT(*) FROM customers WHERE email IS NULL")
        ).scalar()
        total_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()

    null_rate = (null_count / total_count) if total_count else 0
    null_rate_pct = null_rate * 100
    threshold_pct = threshold * 100
    details = (
        f"{null_count} of {total_count} customers ({null_rate_pct:.1f}%) have null email; "
        f"allowed threshold is {threshold_pct:.1f}%"
    )

    if total_count == 0:
        status = "FAIL"
        recommendation = "Reload customer data before checking null email rates."
    elif null_rate <= threshold:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = "Backfill missing customer emails or remove invalid customer records."

    return _make_result("null_emails", "customers", status, details, recommendation)


def check_negative_payment_amounts(engine, rules: dict) -> dict:
    payment_rules = rules["tables"]["payments"]
    non_negative_columns = payment_rules.get("checks", {}).get("non_negative", ["amount"])

    detail_parts = []
    total_negative = 0

    with engine.connect() as conn:
        for column_name in non_negative_columns:
            negative_count = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM payments WHERE {column_name} < 0"
                )
            ).scalar()
            total_negative += negative_count
            detail_parts.append(f"{negative_count} rows with negative {column_name}")

    details = "; ".join(detail_parts)

    if total_negative == 0:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = "Correct negative payment amounts or remove invalid payment records."

    return _make_result(
        "negative_payment_amounts",
        "payments",
        status,
        details,
        recommendation,
    )


def check_future_order_dates(engine, rules: dict) -> dict:
    table_name = "orders"
    if table_name not in rules["tables"]:
        return _make_result(
            "future_order_dates",
            table_name,
            "FAIL",
            f"{table_name} is not configured in validation rules.",
            "Add orders table rules to config/validation_rules.yml.",
        )

    with engine.connect() as conn:
        future_count = conn.execute(
            text(f"SELECT COUNT(*) FROM {table_name} WHERE order_date > CURRENT_DATE")
        ).scalar()

    details = f"{future_count} orders have a future order_date"

    if future_count == 0:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = "Fix order dates that are in the future."

    return _make_result(
        "future_order_dates",
        table_name,
        status,
        details,
        recommendation,
    )


def check_invalid_order_customer_references(engine, rules: dict) -> dict:
    staging_table = "staging_orders"
    customer_table = rules["tables"]["orders"]["foreign_keys"]["customer_id"][
        "references_table"
    ]
    customer_column = rules["tables"]["orders"]["foreign_keys"]["customer_id"][
        "references_column"
    ]

    with engine.connect() as conn:
        staging_exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                )
                """
            ),
            {"table_name": staging_table},
        ).scalar()

        if not staging_exists:
            invalid_count = 0
            details = (
                "staging_orders does not exist; no staging foreign key issues found"
            )
        else:
            invalid_count = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {staging_table} o
                    LEFT JOIN {customer_table} c
                        ON o.customer_id = c.{customer_column}
                    WHERE c.{customer_column} IS NULL
                    """
                )
            ).scalar()
            details = (
                f"{invalid_count} rows in staging_orders reference a missing customer_id"
            )

    if invalid_count == 0:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = (
            "Fix or remove invalid rows in staging_orders before loading them into orders."
        )

    return _make_result(
        "invalid_order_customer_references",
        staging_table,
        status,
        details,
        recommendation,
    )


def check_invalid_payment_order_references(engine, rules: dict) -> dict:
    payment_rules = rules["tables"]["payments"]
    foreign_key = payment_rules["foreign_keys"]["order_id"]
    reference_table = foreign_key["references_table"]
    reference_column = foreign_key["references_column"]

    with engine.connect() as conn:
        invalid_count = conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM payments p
                LEFT JOIN {reference_table} o
                    ON p.order_id = o.{reference_column}
                WHERE o.{reference_column} IS NULL
                """
            )
        ).scalar()

    details = f"{invalid_count} payments reference a missing order_id"

    if invalid_count == 0:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = "Repair or remove payments that point to non-existent orders."

    return _make_result(
        "invalid_payment_order_references",
        "payments",
        status,
        details,
        recommendation,
    )


def run_all_checks(engine=None, rules: dict | None = None) -> list[dict]:
    if engine is None:
        engine = get_engine()
    if rules is None:
        rules = load_validation_rules()

    checks = [
        check_row_counts,
        check_required_columns,
        check_null_emails,
        check_negative_payment_amounts,
        check_future_order_dates,
        check_invalid_order_customer_references,
        check_invalid_payment_order_references,
    ]

    return [check(engine, rules) for check in checks]


def print_results(results: list[dict]) -> None:
    print("\nPipelineGuard Validation Results\n")
    headers = ["check_name", "table", "status", "details", "recommendation"]
    rows = [[result[key] for key in headers] for result in results]
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    passed = sum(1 for result in results if result["status"] == "PASS")
    warnings = sum(1 for result in results if result["status"] == "WARNING")
    failed = sum(1 for result in results if result["status"] == "FAIL")
    print(f"\nSummary: {passed} passed, {warnings} warnings, {failed} failed")


if __name__ == "__main__":
    validation_results = run_all_checks()
    print_results(validation_results)
