import os
import time
import argparse
import json
import datetime
from logger import log_action
from test_runner import run_scenario_based_suite
from analysis_packager import create_analysis_package

# --- Constants ---
REPORT_FILE = "execution_report.json"
HISTORY_DIR = os.path.join("reports", "history")
FRAMEWORK_VERSION = "5.0"

# --- Core Functions ---

def archive_report():
    """If a report file exists, move it to the history folder with a timestamp."""
    if os.path.exists(REPORT_FILE):
        try:
            os.makedirs(HISTORY_DIR, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = os.path.join(HISTORY_DIR, f"report_{timestamp}.json")
            os.rename(REPORT_FILE, archive_path)
            log_action(f"Archived previous report to {archive_path}")
        except Exception as e:
            log_action(f"Could not archive previous report: {e}", is_error=True)

def write_report(data):
    """Archives the old report and writes the new one."""
    archive_report()
    log_action("Writing new execution report.")
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log_action(f"Failed to write report: {e}", is_error=True)

def _format_test_report(test_results):
    """Helper function to format the final JSON report from test results."""
    passed = sum(1 for r in test_results if r['status'] == 'PASSED')
    failed = len(test_results) - passed
    success_rate = (passed / len(test_results) * 100) if test_results else 100
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "framework_version": FRAMEWORK_VERSION,
        "summary": {"total": len(test_results), "passed": passed, "failed": failed, "success_rate": round(success_rate, 2)},
        "tests": test_results
    }

# --- Main Scheduler Loop ---

def main(interval_seconds):
    """
    Main scheduler loop to run tests and generate analysis packages periodically.
    """
    log_action(f"Scheduler started. Will run tests every {interval_seconds} seconds.")

    while True:
        log_action("--- Scheduler: Starting new test cycle. ---")

        # 1. Run all scenario-based tests
        test_results = run_scenario_based_suite()

        if test_results:
            # 2. Write the execution report
            report_data = _format_test_report(test_results)
            write_report(report_data)

            # 3. Create the analysis package for the AI Lead
            create_analysis_package()
        else:
            log_action("No tests were run in this cycle.")

        log_action(f"--- Scheduler: Cycle complete. Waiting for {interval_seconds} seconds. ---")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated QA Test Scheduler.")
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="The interval in seconds between test runs. Default is 3600 (1 hour)."
    )
    args = parser.parse_args()

    main(args.interval)