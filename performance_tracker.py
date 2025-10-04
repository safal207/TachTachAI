import os
import json
import time
from logger import log_action

# --- Constants ---
BASELINE_DIR = os.path.join("knowledge_base", "performance_baselines")
REGRESSION_THRESHOLD = 20.0  # Percentage

# --- File Operations ---

def load_baseline(test_name):
    """Loads the performance baseline for a given test."""
    baseline_path = os.path.join(BASELINE_DIR, f"{test_name}.json")
    if not os.path.exists(baseline_path):
        return None
    try:
        with open(baseline_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_action(f"Error loading baseline file {baseline_path}: {e}", is_error=True)
        return None

def save_baseline(test_name, data):
    """Saves performance data as the new baseline for a test."""
    if not os.path.exists(BASELINE_DIR):
        os.makedirs(BASELINE_DIR)

    baseline_path = os.path.join(BASELINE_DIR, f"{test_name}.json")
    try:
        with open(baseline_path, 'w') as f:
            json.dump(data, f, indent=4)
        log_action(f"Performance baseline saved for '{test_name}' at {baseline_path}")
    except Exception as e:
        log_action(f"Error saving baseline file {baseline_path}: {e}", is_error=True)

def delete_baseline(test_name):
    """Deletes a performance baseline file, forcing it to be recreated."""
    baseline_path = os.path.join(BASELINE_DIR, f"{test_name}.json")
    if os.path.exists(baseline_path):
        try:
            os.remove(baseline_path)
            log_action(f"Successfully deleted performance baseline for '{test_name}'.")
            return True
        except Exception as e:
            log_action(f"Error deleting baseline for '{test_name}': {e}", is_error=True)
            return False
    else:
        log_action(f"Baseline for '{test_name}' not found. Nothing to delete.")
        return True # It's not an error if it's already gone

# --- Core Logic Class ---

class PerformanceTracker:
    """A class to track and analyze the performance of a test run."""

    def __init__(self, test_name):
        self.test_name = test_name
        self._timers = {}
        self.results = {
            "total_duration_ms": 0,
            "steps": [],
            "has_regression": False
        }
        self.baseline = load_baseline(test_name)
        log_action(f"PerformanceTracker initialized for '{test_name}'. Baseline {'found' if self.baseline else 'not found'}.")

    def start_step(self, step_index):
        """Starts the timer for a specific step."""
        self._timers[step_index] = time.perf_counter()

    def stop_step(self, step_index):
        """Stops the timer for a step, calculates duration, and analyzes performance."""
        if step_index not in self._timers:
            return

        end_time = time.perf_counter()
        start_time = self._timers.pop(step_index)
        duration_ms = (end_time - start_time) * 1000

        # Get baseline for this specific step
        baseline_ms = None
        if self.baseline and "steps" in self.baseline and step_index < len(self.baseline["steps"]):
            baseline_ms = self.baseline["steps"][step_index].get("duration_ms")

        # Detect regression
        regression, slowdown_percent = self._detect_regression(duration_ms, baseline_ms)
        if regression:
            self.results["has_regression"] = True

        step_result = {
            "step": step_index + 1,
            "duration_ms": round(duration_ms, 2),
            "baseline_ms": baseline_ms,
            "regression": regression
        }
        if slowdown_percent is not None:
            step_result["slowdown_percent"] = slowdown_percent

        self.results["steps"].append(step_result)

    def finalize(self):
        """Calculates total duration and returns the final performance report."""
        self.results["total_duration_ms"] = sum(step["duration_ms"] for step in self.results["steps"])

        # If no baseline existed, the current run becomes the new baseline.
        if self.baseline is None:
            log_action(f"Creating initial performance baseline for '{self.test_name}'.")
            save_baseline(self.test_name, self.results)

        return self.results

    def _detect_regression(self, current_ms, baseline_ms):
        """
        Compares current duration with baseline and checks for regression.
        :return: A tuple (bool: is_regression, float: slowdown_percentage|None)
        """
        if baseline_ms is None or current_ms <= 0 or baseline_ms <= 0:
            return False, None

        percentage_diff = ((current_ms - baseline_ms) / baseline_ms) * 100

        if percentage_diff > REGRESSION_THRESHOLD:
            return True, round(percentage_diff, 2)

        return False, round(percentage_diff, 2)