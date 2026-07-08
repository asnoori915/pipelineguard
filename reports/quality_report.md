# PipelineGuard Data Quality Report

**Run timestamp:** 2026-07-08 12:56:16

## Summary

| Status | Count |
| --- | ---: |
| PASS | 6 |
| WARNING | 0 |
| FAIL | 1 |

## Detailed Check Results

| Check | Table | Status | Details |
| --- | --- | --- | --- |
| row_counts | all | PASS | customers: 500 (expected >= 500); products: 100 (expected >= 100); orders: 1000 (expected >= 1000); order_items: 2500 (expected >= 2500); payments: 1000 (expected >= 1000) |
| required_columns | all | PASS | All required columns exist for configured tables. |
| null_emails | customers | PASS | 0 of 500 customers (0.0%) have null email; allowed threshold is 5.0% |
| negative_payment_amounts | payments | FAIL | 25 rows with negative amount |
| future_order_dates | orders | PASS | 0 orders have a future order_date |
| invalid_order_customer_references | staging_orders | PASS | staging_orders does not exist; no staging foreign key issues found |
| invalid_payment_order_references | payments | PASS | 0 payments reference a missing order_id |

## Recommendations

- **negative_payment_amounts** (FAIL): Correct negative payment amounts or remove invalid payment records.
