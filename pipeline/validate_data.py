from sqlalchemy import text
from tabulate import tabulate

from pipeline.db import get_engine

EXPECTED_ROW_COUNTS = {
    "customers": 500,
    "products": 100,
    "orders": 1000,
    "order_items": 2500,
    "payments": 1000,
}


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


def check_row_counts(engine) -> dict:
    counts = {}
    with engine.connect() as conn:
        for table_name, expected_count in EXPECTED_ROW_COUNTS.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            counts[table_name] = result.scalar()

    detail_parts = [
        f"{table}: {counts[table]} (expected >= {expected})"
        for table, expected in EXPECTED_ROW_COUNTS.items()
    ]
    details = "; ".join(detail_parts)

    if any(count == 0 for count in counts.values()):
        status = "FAIL"
        recommendation = "Reload the pipeline data because one or more tables are empty."
    elif any(
        counts[table] < expected for table, expected in EXPECTED_ROW_COUNTS.items()
    ):
        status = "WARNING"
        recommendation = "Review the load step because row counts are below expected minimums."
    else:
        status = "PASS"
        recommendation = "No action needed."

    return _make_result("row_counts", "all", status, details, recommendation)


def check_null_emails(engine) -> dict:
    with engine.connect() as conn:
        null_count = conn.execute(
            text("SELECT COUNT(*) FROM customers WHERE email IS NULL")
        ).scalar()
        total_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()

    null_rate = (null_count / total_count * 100) if total_count else 0
    details = f"{null_count} of {total_count} customers ({null_rate:.1f}%) have null email"

    if null_count == 0:
        status = "PASS"
        recommendation = "No action needed."
    else:
        status = "FAIL"
        recommendation = "Backfill missing customer emails or remove invalid customer records."

    return _make_result("null_emails", "customers", status, details, recommendation)


def check_negative_payment_amounts(engine) -> dict:
    with engine.connect() as conn:
        negative_count = conn.execute(
            text("SELECT COUNT(*) FROM payments WHERE amount < 0")
        ).scalar()

    details = f"{negative_count} payments have negative amounts"

    if negative_count == 0:
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


def check_future_order_dates(engine) -> dict:
    with engine.connect() as conn:
        future_count = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE order_date > CURRENT_DATE")
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
        "orders",
        status,
        details,
        recommendation,
    )


def check_invalid_order_customer_references(engine) -> dict:
    with engine.connect() as conn:
        staging_exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'staging_orders'
                )
                """
            )
        ).scalar()

        if not staging_exists:
            invalid_count = 0
            details = (
                "No staging_orders table found; no broken order customer references detected."
            )
        else:
            invalid_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM staging_orders o
                    LEFT JOIN customers c ON o.customer_id = c.customer_id
                    WHERE c.customer_id IS NULL
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
        "staging_orders",
        status,
        details,
        recommendation,
    )


def check_invalid_payment_order_references(engine) -> dict:
    with engine.connect() as conn:
        invalid_count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM payments p
                LEFT JOIN orders o ON p.order_id = o.order_id
                WHERE o.order_id IS NULL
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


def run_all_checks(engine=None) -> list[dict]:
    if engine is None:
        engine = get_engine()

    checks = [
        check_row_counts,
        check_null_emails,
        check_negative_payment_amounts,
        check_future_order_dates,
        check_invalid_order_customer_references,
        check_invalid_payment_order_references,
    ]

    return [check(engine) for check in checks]


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
