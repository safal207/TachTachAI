import os
import time
import math
import socket
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
    Checks for internet connectivity with resilient fallbacks.

    The function first attempts to ``ping`` the target using platform-specific
    arguments (Windows vs. Unix-like). If ``ping`` is unavailable or fails, the
    routine falls back to opening a TCP socket to the supplied host/port so the
    diagnostics report can still indicate connectivity status in restricted
    environments.

    :return: True if a ping or socket connection succeeds, False otherwise.
    """
    try:
        numeric_timeout = float(timeout)
        if numeric_timeout <= 0:
            raise ValueError
    except (TypeError, ValueError):
        log_action(
            f"Invalid timeout '{timeout}' received; defaulting to 3 seconds.",
            is_error=True,
        )
        numeric_timeout = 3.0

    system = platform.system()

    # Build the ping command using platform specific flags.
    if system == "Windows":
        # Windows uses "-n" for the packet count and expects timeout in ms via "-w".
        command = [
            "ping",
            "-n",
            "1",
            "-w",
            str(int(numeric_timeout * 1000)),
            host,
        ]
    else:
        # Unix-like systems use "-c" for packet count and timeout is in seconds via "-W".
        command = ["ping", "-c", "1", "-W", str(int(max(1, math.ceil(numeric_timeout)))), host]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=numeric_timeout + 1,
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        log_action("Network check failed: 'ping' command not found.", is_error=True)
    except subprocess.TimeoutExpired:
        log_action(
            f"Network check timed out after {numeric_timeout} seconds (ping).",
            is_error=True,
        )
    except Exception as e:
        log_action(f"Network check failed via ping: {e}", is_error=True)

    # Fallback to a socket-based connectivity test so environments without ping
    # (e.g., minimal containers) can still report accurate diagnostics.
    try:
        with socket.create_connection((host, port), timeout=numeric_timeout):
            return True
    except OSError as e:
        log_action(f"Network check failed via socket: {e}", is_error=True)

    return False

def take_diagnostic_screenshots(scenario_name, step_index):
    """
    Takes a series of 3 screenshots with a 1-second interval.
    This helps to see the state just before, during, and after a failure.
    :return: A list of paths to the saved screenshots.
    """
    log_action("Taking diagnostic screenshots...")
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    except OSError as e:
        log_action(
            f"Unable to ensure screenshots directory '{SCREENSHOTS_DIR}': {e}",
            is_error=True,
        )
        return []

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
