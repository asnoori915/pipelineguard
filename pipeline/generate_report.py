import json
from datetime import datetime
from pathlib import Path

from pipeline.validate_data import run_all_checks

REPORT_TITLE = "PipelineGuard Data Quality Report"
REPORT_PATH = Path("reports/quality_report.md")
JSON_REPORT_PATH = Path("reports/quality_report.json")


def _escape_table_cell(value: str) -> str:
    """Keep Markdown table rows readable when details contain pipe characters."""
    return value.replace("|", "/")


def _overall_status(passed: int, warnings: int, failed: int) -> str:
    if failed > 0:
        return "FAIL"
    if warnings > 0:
        return "WARNING"
    return "PASS"


def _summarize_results(results: list[dict]) -> dict:
    passed = sum(1 for result in results if result["status"] == "PASS")
    warnings = sum(1 for result in results if result["status"] == "WARNING")
    failed = sum(1 for result in results if result["status"] == "FAIL")

    return {
        "total_checks": len(results),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "overall_status": _overall_status(passed, warnings, failed),
    }


def build_json_report(results: list[dict], run_timestamp: str) -> dict:
    summary = _summarize_results(results)

    return {
        "run_timestamp": run_timestamp,
        "overall_status": summary["overall_status"],
        "summary": {
            "total_checks": summary["total_checks"],
            "passed": summary["passed"],
            "warnings": summary["warnings"],
            "failed": summary["failed"],
        },
        "validation_results": results,
    }


def build_report(results: list[dict], run_timestamp: str) -> str:
    summary = _summarize_results(results)
    total_checks = summary["total_checks"]
    passed = summary["passed"]
    warnings = summary["warnings"]
    failed = summary["failed"]
    overall_status = summary["overall_status"]

    lines = [
        f"# {REPORT_TITLE}",
        "",
        f"**Run timestamp:** {run_timestamp}",
        "",
        "## Overall Status",
        "",
        f"**{overall_status}**",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Total checks | {total_checks} |",
        f"| Passed | {passed} |",
        f"| Warnings | {warnings} |",
        f"| Failed | {failed} |",
        "",
        "## Check Results",
        "",
        "| check_name | table | status | details | recommendation |",
        "| --- | --- | --- | --- | --- |",
    ]

    for result in results:
        lines.append(
            "| {check_name} | {table} | {status} | {details} | {recommendation} |".format(
                check_name=_escape_table_cell(result["check_name"]),
                table=_escape_table_cell(result["table"]),
                status=_escape_table_cell(result["status"]),
                details=_escape_table_cell(result["details"]),
                recommendation=_escape_table_cell(result["recommendation"]),
            )
        )

    lines.extend(["", "## Key Findings", ""])

    findings = [
        result for result in results if result["status"] in ("WARNING", "FAIL")
    ]
    if findings:
        for result in findings:
            lines.append(
                f"- **{result['check_name']}** ({result['status']}) on "
                f"`{result['table']}`: {result['details']}"
            )
            lines.append(f"  - Recommendation: {result['recommendation']}")
    else:
        lines.append("- No warnings or failures were found.")

    lines.extend(
        [
            "",
            "## How to Interpret This Report",
            "",
            "- **Overall Status** reflects the worst result in the run.",
            "- **PASS** means every check passed.",
            "- **WARNING** means at least one check needs review, but no checks failed.",
            "- **FAIL** means at least one check found a data quality issue that should be fixed.",
            "- Use **Check Results** to review every validation rule.",
            "- Use **Key Findings** to focus on the checks that need attention.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    results = run_all_checks()
    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(results, run_timestamp)
    json_report = build_json_report(results, run_timestamp)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    JSON_REPORT_PATH.write_text(
        json.dumps(json_report, indent=2),
        encoding="utf-8",
    )

    print(f"Report written to {REPORT_PATH}")
    print(f"Report written to {JSON_REPORT_PATH}")


if __name__ == "__main__":
    main()
