import os
import json
import datetime
from logger import log_action
from trend_analyzer import analyze_trends

# --- Constants ---
EXECUTION_REPORT_FILE = "execution_report.json"
AGENT_MEMORY_FILE = "agent_memory.json"
ANALYSIS_PACKAGE_FILE = os.path.join("reports", "ai_analysis_package.json")
READY_FLAG_FILE = "READY_FOR_AI_ANALYSIS.flag"

def get_latest_report():
    """Loads the main execution report."""
    if not os.path.exists(EXECUTION_REPORT_FILE):
        return None
    try:
        with open(EXECUTION_REPORT_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_action(f"Error loading execution report: {e}", is_error=True)
        return None

def get_agent_goals():
    """Loads just the goals from the agent's memory."""
    if not os.path.exists(AGENT_MEMORY_FILE):
        return {}
    try:
        with open(AGENT_MEMORY_FILE, 'r') as f:
            memory = json.load(f)
            return memory.get("goals", {})
    except Exception as e:
        log_action(f"Error loading agent goals: {e}", is_error=True)
        return {}

def create_analysis_package():
    """
    Gathers all necessary data for AI analysis and creates a single package file.
    """
    log_action("Creating AI analysis package...")

    latest_report = get_latest_report()
    if not latest_report:
        log_action("Cannot create analysis package: no execution report found.", is_error=True)
        return

    trends = analyze_trends()
    goals = get_agent_goals()

    # Add current success rate to goals for context
    current_success_rate = latest_report.get("summary", {}).get("success_rate", 0)
    goals["current_success_rate"] = current_success_rate
    goals["action_needed"] = current_success_rate < goals.get("target_success_rate", 95.0)

    analysis_package = {
        "report_timestamp": latest_report.get("timestamp"),
        "execution_report": latest_report,
        "trends": trends,
        # For now, coverage gaps are a placeholder for future functionality
        "coverage_gaps": [
            "Note: Coverage analysis is not yet implemented."
        ],
        "agent_goals": goals
    }

    try:
        with open(ANALYSIS_PACKAGE_FILE, 'w') as f:
            json.dump(analysis_package, f, indent=4)
        log_action(f"Successfully created AI analysis package at {ANALYSIS_PACKAGE_FILE}")

        # Create a flag file to notify the user
        with open(READY_FLAG_FILE, 'w') as f:
            f.write(f"Package created at {datetime.datetime.now().isoformat()}")
        log_action(f"Created flag file: {READY_FLAG_FILE}")

    except Exception as e:
        log_action(f"Error writing analysis package: {e}", is_error=True)

if __name__ == '__main__':
    # For standalone testing of this module
    create_analysis_package()