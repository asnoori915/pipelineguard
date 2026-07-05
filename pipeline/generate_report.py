from datetime import datetime
from pathlib import Path

from pipeline.validate_data import run_all_checks

PROJECT_NAME = "PipelineGuard"
REPORT_PATH = Path("reports/quality_report.md")


def build_report(results: list[dict], run_timestamp: str) -> str:
    passed = sum(1 for result in results if result["status"] == "PASS")
    warnings = sum(1 for result in results if result["status"] == "WARNING")
    failed = sum(1 for result in results if result["status"] == "FAIL")

    lines = [
        f"# {PROJECT_NAME} Data Quality Report",
        "",
        f"**Run timestamp:** {run_timestamp}",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
        f"| PASS | {passed} |",
        f"| WARNING | {warnings} |",
        f"| FAIL | {failed} |",
        "",
        "## Detailed Check Results",
        "",
        "| Check | Table | Status | Details |",
        "| --- | --- | --- | --- |",
    ]

    for result in results:
        lines.append(
            f"| {result['check_name']} | {result['table']} | "
            f"{result['status']} | {result['details']} |"
        )

    lines.extend(["", "## Recommendations", ""])

    actionable_results = [
        result for result in results if result["status"] != "PASS"
    ]
    if actionable_results:
        for result in actionable_results:
            lines.append(
                f"- **{result['check_name']}** ({result['status']}): "
                f"{result['recommendation']}"
            )
    else:
        lines.append("- All checks passed. No action needed.")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    results = run_all_checks()
    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(results, run_timestamp)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
