import os
import json
from collections import defaultdict
from logger import log_action

# --- Constants ---
HISTORY_DIR = os.path.join("reports", "history")
TREND_ANALYSIS_WINDOW = 10 # Analyze the last 10 reports

def load_reports(limit=TREND_ANALYSIS_WINDOW):
    """Loads the most recent reports from the history directory."""
    if not os.path.exists(HISTORY_DIR):
        return []

    try:
        report_files = sorted(
            [os.path.join(HISTORY_DIR, f) for f in os.listdir(HISTORY_DIR) if f.endswith('.json')],
            key=os.path.getmtime,
            reverse=True
        )

        reports = []
        for report_file in report_files[:limit]:
            with open(report_file, 'r') as f:
                reports.append(json.load(f))
        return reports
    except Exception as e:
        log_action(f"Error loading historical reports: {e}", is_error=True)
        return []

def analyze_trends():
    """
    Analyzes historical data to find failure patterns, flaky tests, and performance trends.
    :return: A dictionary containing trend analysis insights.
    """
    log_action("Starting trend analysis...")
    reports = load_reports()

    if not reports:
        return {"summary": "No historical data to analyze."}

    failure_counts = defaultdict(int)
    status_history = defaultdict(list)
    perf_regressions = defaultdict(int)

    for report in reports:
        for test in report.get("tests", []):
            test_name = test.get("name")
            status = test.get("status")
            if not test_name or not status:
                continue

            status_history[test_name].append(status)
            if status == "FAILED":
                failure_counts[test_name] += 1

            if test.get("performance", {}).get("has_regression"):
                perf_regressions[test_name] += 1

    # Identify flaky tests (alternating PASS/FAIL in recent history)
    flaky_tests = []
    for test_name, history in status_history.items():
        if len(history) > 2 and len(set(history)) > 1:
             # A simple heuristic: if it has both passed and failed recently
             if "PASSED" in history and "FAILED" in history:
                flaky_tests.append({
                    "name": test_name,
                    "history": history
                })

    # Find most frequent failures
    top_failures = sorted(failure_counts.items(), key=lambda item: item[1], reverse=True)

    # Find consistent performance regressions
    persistent_perf_regressions = [
        {"name": name, "regression_count": count}
        for name, count in perf_regressions.items() if count > 1
    ]

    log_action("Trend analysis complete.")
    return {
        "analysis_window": len(reports),
        "flaky_tests": flaky_tests,
        "top_failures": [{"name": name, "fail_count": count} for name, count in top_failures[:3]],
        "persistent_perf_regressions": persistent_perf_regressions
    }

if __name__ == '__main__':
    # For standalone testing of this module
    trends = analyze_trends()
    print(json.dumps(trends, indent=2))