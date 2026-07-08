CREATE TABLE IF NOT EXISTS quality_runs (
    run_id TEXT PRIMARY KEY,
    run_timestamp TIMESTAMP NOT NULL,
    break_type TEXT,
    overall_status TEXT NOT NULL,
    total_checks INTEGER NOT NULL,
    passed_checks INTEGER NOT NULL,
    warning_checks INTEGER NOT NULL,
    failed_checks INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS quality_check_results (
    id SERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    recommendation TEXT,
    FOREIGN KEY (run_id) REFERENCES quality_runs(run_id)
);
