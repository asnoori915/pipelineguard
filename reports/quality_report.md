# PipelineGuard Data Quality Report

**Run timestamp:** 2026-07-05 12:22:15

## Summary

| Status | Count |
| --- | ---: |
| PASS | 5 |
| WARNING | 0 |
| FAIL | 1 |

## Detailed Check Results

| Check | Table | Status | Details |
| --- | --- | --- | --- |
| row_counts | all | PASS | customers: 500 (expected >= 500); products: 100 (expected >= 100); orders: 1000 (expected >= 1000); order_items: 2500 (expected >= 2500); payments: 1000 (expected >= 1000) |
| null_emails | customers | PASS | 0 of 500 customers (0.0%) have null email |
| negative_payment_amounts | payments | PASS | 0 payments have negative amounts |
| future_order_dates | orders | PASS | 0 orders have a future order_date |
| invalid_order_customer_references | staging_orders | FAIL | 10 rows in staging_orders reference a missing customer_id |
| invalid_payment_order_references | payments | PASS | 0 payments reference a missing order_id |

## Recommendations

- **invalid_order_customer_references** (FAIL): Fix or remove invalid rows in staging_orders before loading them into orders.
