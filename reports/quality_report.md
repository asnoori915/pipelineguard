# PipelineGuard Data Quality Report

**Run timestamp:** 2026-07-08 13:32:40

## Overall Status

**PASS**

## Summary

| Metric | Count |
| --- | ---: |
| Total checks | 11 |
| Passed | 11 |
| Warnings | 0 |
| Failed | 0 |

## Check Results

| check_name | table | status | details | recommendation |
| --- | --- | --- | --- | --- |
| row_counts | all | PASS | customers: 500 (expected >= 500); products: 100 (expected >= 100); orders: 1000 (expected >= 1000); order_items: 2500 (expected >= 2500); payments: 1000 (expected >= 1000) | No action needed. |
| schema_drift | customers | PASS | Schema matches required_columns. | No action needed. |
| schema_drift | products | PASS | Schema matches required_columns. | No action needed. |
| schema_drift | orders | PASS | Schema matches required_columns. | No action needed. |
| schema_drift | order_items | PASS | Schema matches required_columns. | No action needed. |
| schema_drift | payments | PASS | Schema matches required_columns. | No action needed. |
| null_emails | customers | PASS | 0 of 500 customers (0.0%) have null email; allowed threshold is 5.0% | No action needed. |
| negative_payment_amounts | payments | PASS | 0 rows with negative amount | No action needed. |
| future_order_dates | orders | PASS | 0 orders have a future order_date | No action needed. |
| invalid_order_customer_references | staging_orders | PASS | staging_orders does not exist; no staging foreign key issues found | No action needed. |
| invalid_payment_order_references | payments | PASS | 0 payments reference a missing order_id | No action needed. |

## Key Findings

- No warnings or failures were found.

## How to Interpret This Report

- **Overall Status** reflects the worst result in the run.
- **PASS** means every check passed.
- **WARNING** means at least one check needs review, but no checks failed.
- **FAIL** means at least one check found a data quality issue that should be fixed.
- Use **Check Results** to review every validation rule.
- Use **Key Findings** to focus on the checks that need attention.
