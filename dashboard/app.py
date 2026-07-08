import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.db import get_engine


@st.cache_data
def load_recent_runs() -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            run_id,
            run_timestamp,
            break_type,
            overall_status,
            total_checks,
            passed_checks,
            warning_checks,
            failed_checks
        FROM quality_runs
        ORDER BY run_timestamp DESC
        LIMIT 10
    """
    return pd.read_sql(query, engine)


@st.cache_data
def load_check_results(run_id: str) -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT
            check_name,
            table_name,
            status,
            details,
            recommendation
        FROM quality_check_results
        WHERE run_id = %(run_id)s
        ORDER BY id
    """
    return pd.read_sql(query, engine, params={"run_id": run_id})


def main() -> None:
    st.set_page_config(page_title="PipelineGuard Dashboard", layout="wide")
    st.title("PipelineGuard Data Quality Dashboard")

    try:
        recent_runs = load_recent_runs()
    except Exception as exc:
        st.error(f"Could not connect to PostgreSQL: {exc}")
        st.stop()

    if recent_runs.empty:
        st.info("No quality runs found yet. Run `python -m pipeline.main` first.")
        st.stop()

    latest_run = recent_runs.iloc[0]

    st.subheader("Latest Run Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Run ID", latest_run["run_id"])
    col2.metric("Timestamp", str(latest_run["run_timestamp"]))
    col3.metric("Break Type", latest_run["break_type"] or "None")
    col4.metric("Overall Status", latest_run["overall_status"])

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Checks", int(latest_run["total_checks"]))
    col6.metric("Passed Checks", int(latest_run["passed_checks"]))
    col7.metric("Warning Checks", int(latest_run["warning_checks"]))
    col8.metric("Failed Checks", int(latest_run["failed_checks"]))

    st.subheader("Status Metrics")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Passed", int(latest_run["passed_checks"]))
    metric_col2.metric("Warnings", int(latest_run["warning_checks"]))
    metric_col3.metric("Failed", int(latest_run["failed_checks"]))

    st.subheader("Recent Runs")
    st.dataframe(recent_runs, use_container_width=True)

    run_options = recent_runs["run_id"].tolist()
    selected_run_id = st.selectbox(
        "Select a run to view check results",
        options=run_options,
        index=0,
    )

    st.subheader("Check Results")
    check_results = load_check_results(selected_run_id)
    st.dataframe(check_results, use_container_width=True)

    st.subheader("Latest Run Status Chart")
    chart_data = pd.DataFrame(
        {
            "count": [
                int(latest_run["passed_checks"]),
                int(latest_run["warning_checks"]),
                int(latest_run["failed_checks"]),
            ]
        },
        index=["Passed", "Warnings", "Failed"],
    )
    st.bar_chart(chart_data)


if __name__ == "__main__":
    main()
