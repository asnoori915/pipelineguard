import os
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)

OUTPUT_DIR = Path("data/generated")

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
PAYMENT_STATUSES = ["paid", "pending", "failed"]
PRODUCT_CATEGORIES = ["electronics", "clothing", "home", "books", "sports"]


def generate_customers(n: int = 500) -> pd.DataFrame:
    rows = []
    for customer_id in range(1, n + 1):
        rows.append(
            {
                "customer_id": customer_id,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
            }
        )
    return pd.DataFrame(rows)


def generate_products(n: int = 100) -> pd.DataFrame:
    rows = []
    for product_id in range(1, n + 1):
        rows.append(
            {
                "product_id": product_id,
                "product_name": fake.catch_phrase(),
                "category": fake.random_element(PRODUCT_CATEGORIES),
                "price": round(fake.pyfloat(min_value=5, max_value=500, right_digits=2), 2),
            }
        )
    return pd.DataFrame(rows)


def generate_orders(customers_df: pd.DataFrame, n: int = 1000) -> pd.DataFrame:
    customer_ids = customers_df["customer_id"].tolist()
    rows = []
    for order_id in range(1, n + 1):
        rows.append(
            {
                "order_id": order_id,
                "customer_id": fake.random_element(customer_ids),
                "order_date": fake.date_between(start_date="-1y", end_date="today"),
                "status": fake.random_element(ORDER_STATUSES),
            }
        )
    return pd.DataFrame(rows)


def generate_order_items(
    orders_df: pd.DataFrame, products_df: pd.DataFrame, n: int = 2500
) -> pd.DataFrame:
    order_ids = orders_df["order_id"].tolist()
    product_prices = products_df.set_index("product_id")["price"].to_dict()
    product_ids = list(product_prices.keys())

    rows = []
    for order_item_id in range(1, n + 1):
        product_id = fake.random_element(product_ids)
        rows.append(
            {
                "order_item_id": order_item_id,
                "order_id": fake.random_element(order_ids),
                "product_id": product_id,
                "quantity": fake.random_int(min=1, max=5),
                "unit_price": product_prices[product_id],
            }
        )
    return pd.DataFrame(rows)


def generate_payments(
    orders_df: pd.DataFrame, order_items_df: pd.DataFrame, n: int = 1000
) -> pd.DataFrame:
    order_totals = (
        order_items_df.assign(line_total=order_items_df["quantity"] * order_items_df["unit_price"])
        .groupby("order_id")["line_total"]
        .sum()
        .round(2)
    )

    order_ids = orders_df["order_id"].tolist()
    if n > len(order_ids):
        n = len(order_ids)

    selected_order_ids = fake.random_elements(
        elements=order_ids, length=n, unique=True
    )

    rows = []
    for payment_id, order_id in enumerate(selected_order_ids, start=1):
        amount = order_totals.get(order_id, round(fake.pyfloat(min_value=10, max_value=500, right_digits=2), 2))
        payment_status = fake.random_element(PAYMENT_STATUSES)
        rows.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": float(amount),
                "payment_status": payment_status,
                "paid_at": fake.date_time_between(start_date="-1y", end_date="now")
                if payment_status == "paid"
                else None,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)
    payments = generate_payments(orders, order_items)

    datasets = {
        "customers.csv": customers,
        "products.csv": products,
        "orders.csv": orders,
        "order_items.csv": order_items,
        "payments.csv": payments,
    }

    for filename, df in datasets.items():
        filepath = OUTPUT_DIR / filename
        df.to_csv(filepath, index=False)
        print(f"Generated {len(df)} rows -> {filepath}")


if __name__ == "__main__":
    main()
