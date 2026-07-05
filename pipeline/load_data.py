from pathlib import Path

import pandas as pd
from sqlalchemy import text

from pipeline.db import get_engine

DATA_DIR = Path("data/generated")
RESET_SQL = Path("sql/02_reset_tables.sql")

TABLES = [
    ("customers", "customers.csv"),
    ("products", "products.csv"),
    ("orders", "orders.csv"),
    ("order_items", "order_items.csv"),
    ("payments", "payments.csv"),
]


def reset_tables(engine) -> None:
    """Clear all pipeline tables before loading fresh data."""
    sql = RESET_SQL.read_text()
    with engine.begin() as conn:
        conn.execute(text(sql))


def load_csv(engine, table_name: str, csv_path: Path) -> int:
    """Load one CSV file into the matching PostgreSQL table."""
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists="append", index=False)
    return len(df)


def main() -> None:
    engine = get_engine()

    reset_tables(engine)
    print("Reset existing tables.")

    for table_name, filename in TABLES:
        csv_path = DATA_DIR / filename
        row_count = load_csv(engine, table_name, csv_path)
        print(f"Loaded {row_count} rows into {table_name}")


if __name__ == "__main__":
    main()
