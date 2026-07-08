# PipelineGuard Data Quality Report

**Run timestamp:** 2026-07-08 12:57:56

## Summary

| Status | Count |
| --- | ---: |
| PASS | 11 |
| WARNING | 0 |
| FAIL | 0 |

## Detailed Check Results

| Check | Table | Status | Details |
| --- | --- | --- | --- |
| row_counts | all | PASS | customers: 500 (expected >= 500); products: 100 (expected >= 100); orders: 1000 (expected >= 1000); order_items: 2500 (expected >= 2500); payments: 1000 (expected >= 1000) |
| schema_drift | customers | PASS | Schema matches required_columns. |
| schema_drift | products | PASS | Schema matches required_columns. |
| schema_drift | orders | PASS | Schema matches required_columns. |
| schema_drift | order_items | PASS | Schema matches required_columns. |
| schema_drift | payments | PASS | Schema matches required_columns. |
| null_emails | customers | PASS | 0 of 500 customers (0.0%) have null email; allowed threshold is 5.0% |
| negative_payment_amounts | payments | PASS | 0 rows with negative amount |
| future_order_dates | orders | PASS | 0 orders have a future order_date |
| invalid_order_customer_references | staging_orders | PASS | staging_orders does not exist; no staging foreign key issues found |
| invalid_payment_order_references | payments | PASS | 0 payments reference a missing order_id |

## Recommendations

- All checks passed. No action needed.
