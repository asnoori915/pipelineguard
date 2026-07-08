import argparse
import sys

from pipeline.audit import save_quality_run
from pipeline.break_data import ISSUE_CHOICES, ISSUE_HANDLERS
from pipeline.db import get_engine
from pipeline.generate_data import main as generate_data
from pipeline.generate_report import main as generate_report
from pipeline.load_data import main as load_data
from pipeline.run_dbt import run_dbt_command
from pipeline.validate_data import print_results, run_all_checks


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full PipelineGuard data quality workflow."
    )
    parser.add_argument(
        "--break",
        dest="break_issue",
        choices=ISSUE_CHOICES,
        help=(
            "Optionally inject a data quality issue before validation. "
            "Supported values: missing_emails, negative_payments, "
            "future_order_dates, broken_foreign_keys, schema_drift."
        ),
    )
    parser.add_argument(
        "--run-dbt",
        action="store_true",
        help="Run dbt models and tests after report generation.",
    )
    args = parser.parse_args()

    print("Step 1/5: Generating clean synthetic data...")
    generate_data()
    print()

    print("Step 2/5: Loading data into PostgreSQL...")
    load_data()
    print()

    if args.break_issue:
        print(f"Step 3/5: Injecting broken data ({args.break_issue})...")
        engine = get_engine()
        ISSUE_HANDLERS[args.break_issue](engine)
    else:
        print("Step 3/5: Skipping data break injection.")
    print()

    print("Step 4/5: Validating data...")
    results = run_all_checks()
    print_results(results)
    run_id = save_quality_run(results, break_type=args.break_issue)
    print(f"Saved quality run: {run_id}")
    print()

    print("Step 5/5: Generating Markdown quality report...")
    generate_report()
    print()

    if args.run_dbt:
        print("Running dbt analytics layer...")
        print("Step 1/2: Running dbt models...")
        exit_code = run_dbt_command(["run"])
        if exit_code != 0:
            print("dbt run failed.")
            sys.exit(exit_code)

        print()
        print("Step 2/2: Running dbt tests...")
        exit_code = run_dbt_command(["test"])
        if exit_code != 0:
            print("dbt test failed.")
            sys.exit(exit_code)

        print("dbt completed successfully.")
        print()

    print("PipelineGuard workflow complete.")


if __name__ == "__main__":
    main()
