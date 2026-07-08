import argparse
import subprocess
import sys
from pathlib import Path

DBT_PROJECT_DIR = Path(__file__).resolve().parent.parent / "dbt_pipelineguard"


def run_dbt_command(args: list[str]) -> int:
    """Run a dbt command from the dbt project directory."""
    command = ["dbt", *args]
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=DBT_PROJECT_DIR, check=False)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run dbt commands for the PipelineGuard analytics layer."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", action="store_true", help="Run dbt models.")
    group.add_argument("--test", action="store_true", help="Run dbt tests.")
    group.add_argument(
        "--all",
        action="store_true",
        help="Run dbt run, then dbt test.",
    )
    args = parser.parse_args()

    if args.run:
        print("Step 1/1: Running dbt models...")
        exit_code = run_dbt_command(["run"])
    elif args.test:
        print("Step 1/1: Running dbt tests...")
        exit_code = run_dbt_command(["test"])
    else:
        print("Step 1/2: Running dbt models...")
        exit_code = run_dbt_command(["run"])
        if exit_code != 0:
            print("dbt run failed.")
            sys.exit(exit_code)

        print()
        print("Step 2/2: Running dbt tests...")
        exit_code = run_dbt_command(["test"])

    if exit_code != 0:
        print("dbt command failed.")
        sys.exit(exit_code)

    print("dbt completed successfully.")


if __name__ == "__main__":
    main()
