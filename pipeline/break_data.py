import argparse

from sqlalchemy import text

from pipeline.db import get_engine

ISSUE_CHOICES = [
    "missing_emails",
    "negative_payments",
    "future_order_dates",
    "broken_foreign_keys",
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
    """Point a sample of orders at a customer_id that does not exist."""
    with engine.begin() as conn:
        # Temporarily disable FK enforcement so invalid references can be inserted.
        conn.execute(text("SET session_replication_role = 'replica'"))
        result = conn.execute(
            text(
                """
                UPDATE orders
                SET customer_id = 999999
                WHERE order_id IN (
                    SELECT order_id
                    FROM orders
                    LIMIT 10
                )
                """
            )
        )
        conn.execute(text("SET session_replication_role = 'origin'"))

    print(
        "Injected broken_foreign_keys: updated "
        f"{result.rowcount} orders to use customer_id 999999 (invalid reference)."
    )


ISSUE_HANDLERS = {
    "missing_emails": inject_missing_emails,
    "negative_payments": inject_negative_payments,
    "future_order_dates": inject_future_order_dates,
    "broken_foreign_keys": inject_broken_foreign_keys,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject data quality issues into PostgreSQL for testing."
    )
    parser.add_argument(
        "--issue",
        required=True,
        choices=ISSUE_CHOICES,
        help="Type of data quality issue to inject.",
    )
    args = parser.parse_args()

    engine = get_engine()
    ISSUE_HANDLERS[args.issue](engine)


if __name__ == "__main__":
    main()
