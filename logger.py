import datetime

LOG_FILE = "history.log"

def log_action(message, is_error=False):
    """
    Logs a message to both the console and the history.log file.
    It prepends a timestamp to each message.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add a prefix for errors to make them easy to spot
    prefix = "[ERROR]" if is_error else "[INFO]"

    log_message = f"{timestamp} {prefix}: {message}"

    # Print to console (for immediate user feedback)
    print(log_message)

    # Append to the log file (for the agent's "memory")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    except Exception as e:
        # If logging fails, print an error to the console so the user knows.
        print(f"{timestamp} [CRITICAL]: Failed to write to log file: {e}")