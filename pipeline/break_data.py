import argparse

from sqlalchemy import text

from pipeline.db import get_engine

ISSUE_CHOICES = [
    "missing_emails",
    "negative_payments",
    "future_order_dates",
    "broken_foreign_keys",
    "schema_drift",
]


def inject_missing_emails(engine) -> None:
    """Set email to NULL for a sample of customers."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE customers
                SET email = NULL
                WHERE customer_id IN (
                    SELECT customer_id
                    FROM customers
                    WHERE email IS NOT NULL
                    LIMIT 50
                )
                """
            )
        )

    print(
        f"Injected missing_emails: cleared email for {result.rowcount} customers."
    )


def inject_negative_payments(engine) -> None:
    """Flip a sample of payment amounts to negative values."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE payments
                SET amount = -ABS(amount)
                WHERE payment_id IN (
                    SELECT payment_id
                    FROM payments
                    LIMIT 25
                )
                """
            )
        )

    print(
        f"Injected negative_payments: set negative amount on {result.rowcount} payments."
    )


def inject_future_order_dates(engine) -> None:
    """Move a sample of orders to dates in the future."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE orders
                SET order_date = CURRENT_DATE + INTERVAL '30 days'
                WHERE order_id IN (
                    SELECT order_id
                    FROM orders
                    LIMIT 50
                )
                """
            )
        )

    print(
        f"Injected future_order_dates: moved {result.rowcount} orders to a future date."
    )


def inject_broken_foreign_keys(engine) -> None:
    """Load orders with invalid customer_id values into staging_orders."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS staging_orders"))
        conn.execute(
            text(
                """
                CREATE TABLE staging_orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER NOT NULL,
                    order_date DATE NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
        )
        result = conn.execute(
            text(
                """
                INSERT INTO staging_orders (order_id, customer_id, order_date, status)
                SELECT order_id, 999999, order_date, status
                FROM orders
                LIMIT 10
                """
            )
        )

    print(
        "Injected broken_foreign_keys: inserted "
        f"{result.rowcount} rows into staging_orders with customer_id 999999 "
        "(invalid reference)."
    )


def inject_schema_drift(engine) -> None:
    """Add an unexpected column to the customers table."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE customers
                ADD COLUMN IF NOT EXISTS legacy_customer_code TEXT
                """
            )
        )

    print(
        "Injected schema_drift: added unexpected column legacy_customer_code to customers."
    )


ISSUE_HANDLERS = {
    "missing_emails": inject_missing_emails,
    "negative_payments": inject_negative_payments,
    "future_order_dates": inject_future_order_dates,
    "broken_foreign_keys": inject_broken_foreign_keys,
    "schema_drift": inject_schema_drift,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject data quality issues into PostgreSQL for testing."
    )
    parser.add_argument(
        "--issue",
        required=True,
        choices=ISSUE_CHOICES,
        help=(
            "Type of data quality issue to inject. "
            "Supported values: missing_emails, negative_payments, "
            "future_order_dates, broken_foreign_keys, schema_drift."
        ),
    )
    args = parser.parse_args()

    engine = get_engine()
    ISSUE_HANDLERS[args.issue](engine)


if __name__ == "__main__":
    main()
