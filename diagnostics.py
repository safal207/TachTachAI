import os
import time
import subprocess
import datetime
import platform
import pyautogui
import psutil
from logger import log_action

# --- Constants ---
REPORTS_DIR = "reports"
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")

def get_system_stats():
    """
    Retrieves current system CPU and RAM usage.
    :return: A dictionary with 'cpu_usage' and 'ram_usage' percentages.
    """
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        return {"cpu_usage": f"{cpu}%", "ram_usage": f"{ram}%"}
    except Exception as e:
        log_action(f"Could not retrieve system stats: {e}", is_error=True)
        return {"cpu_usage": "N/A", "ram_usage": "N/A"}

def check_network(host="8.8.8.8", port=53, timeout=3):
    """
    Checks for internet connectivity by attempting to reach a DNS host via ``ping``.
    The invocation is tailored to the underlying platform (Windows vs. Unix-like
    systems) so that timeouts are respected consistently.
    :return: True if the command succeeds, False otherwise.
    """
    try:
        system = platform.system()

        # Build the ping command using platform specific flags.
        if system == "Windows":
            # Windows uses "-n" for the packet count and expects timeout in ms via "-w".
            command = [
                "ping",
                "-n",
                "1",
                "-w",
                str(int(timeout * 1000)),
                host,
            ]
        else:
            # Unix-like systems use "-c" for packet count and timeout is in seconds via "-W".
            command = ["ping", "-c", "1", "-W", str(int(timeout)), host]

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        log_action("Network check failed: 'ping' command not found.", is_error=True)
        return False
    except Exception as e:
        log_action(f"Network check failed: {e}", is_error=True)
        return False

def take_diagnostic_screenshots(scenario_name, step_index):
    """
    Takes a series of 3 screenshots with a 1-second interval.
    This helps to see the state just before, during, and after a failure.
    :return: A list of paths to the saved screenshots.
    """
    log_action("Taking diagnostic screenshots...")
    paths = []
    base_filename = f"{scenario_name}_step_{step_index + 1}_failure"

    for i in range(3):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}_shot_{i+1}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        try:
            pyautogui.screenshot(filepath)
            paths.append(filepath)
            log_action(f"  -> Screenshot {i+1} saved to: {filepath}")
            if i < 2: # Don't sleep after the last screenshot
                time.sleep(1)
        except Exception as e:
            log_action(f"Failed to take screenshot {i+1}: {e}", is_error=True)

    return paths

def run_diagnostics(scenario_name, step_index):
    """
    Runs all diagnostic checks and returns a consolidated report dictionary.
    """
    log_action("--- Running Failure Diagnostics ---")

    stats = get_system_stats()
    network_ok = check_network()
    screenshots = take_diagnostic_screenshots(scenario_name, step_index)

    diagnostics_report = {
        "screenshots": screenshots,
        "network_available": network_ok,
        "cpu_usage": stats["cpu_usage"],
        "ram_usage": stats["ram_usage"]
    }

    log_action("--- Diagnostics Finished ---")
    return diagnostics_report