import uuid
from datetime import datetime

from sqlalchemy import text

from pipeline.db import get_engine


def calculate_overall_status(results: list[dict]) -> str:
    """Return the overall run status based on individual check results."""
    if any(result["status"] == "FAIL" for result in results):
        return "FAIL"
    if any(result["status"] == "WARNING" for result in results):
        return "WARNING"
    return "PASS"


def save_quality_run(results: list[dict], break_type: str | None = None) -> str:
    """Save one validation run and its check results to PostgreSQL."""
    engine = get_engine()
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.now()

    total_checks = len(results)
    passed_checks = sum(1 for result in results if result["status"] == "PASS")
    warning_checks = sum(1 for result in results if result["status"] == "WARNING")
    failed_checks = sum(1 for result in results if result["status"] == "FAIL")
    overall_status = calculate_overall_status(results)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO quality_runs (
                    run_id,
                    run_timestamp,
                    break_type,
                    overall_status,
                    total_checks,
                    passed_checks,
                    warning_checks,
                    failed_checks
                )
                VALUES (
                    :run_id,
                    :run_timestamp,
                    :break_type,
                    :overall_status,
                    :total_checks,
                    :passed_checks,
                    :warning_checks,
                    :failed_checks
                )
                """
            ),
            {
                "run_id": run_id,
                "run_timestamp": run_timestamp,
                "break_type": break_type,
                "overall_status": overall_status,
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "warning_checks": warning_checks,
                "failed_checks": failed_checks,
            },
        )

        for result in results:
            conn.execute(
                text(
                    """
                    INSERT INTO quality_check_results (
                        run_id,
                        check_name,
                        table_name,
                        status,
                        details,
                        recommendation
                    )
                    VALUES (
                        :run_id,
                        :check_name,
                        :table_name,
                        :status,
                        :details,
                        :recommendation
                    )
                    """
                ),
                {
                    "run_id": run_id,
                    "check_name": result["check_name"],
                    "table_name": result["table"],
                    "status": result["status"],
                    "details": result["details"],
                    "recommendation": result["recommendation"],
                },
            )

    return run_id


if __name__ == "__main__":
    from pipeline.validate_data import run_all_checks

    validation_results = run_all_checks()
    saved_run_id = save_quality_run(validation_results)
    print(f"Saved quality run {saved_run_id}")
