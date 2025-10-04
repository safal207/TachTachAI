import os
import platform
from logger import log_action

# --- OS-specific imports and setup ---
if platform.system() == "Windows":
    from pywinauto.application import Application
    UIA_ENABLED = True
    log_action("Windows OS detected. UIA backend enabled.")
else:
    UIA_ENABLED = False
    log_action("Non-Windows OS detected. UIA backend is DISABLED.", is_error=True)

# --- Global state (simplified for this MVP) ---
_app = None
_main_window = None
_last_found_element = None

# --- Application Management ---

def start_app(path, timeout=30):
    """Starts an application and connects to its main window."""
    global _app, _main_window
    if not UIA_ENABLED: return False
    try:
        log_action(f"Starting app: {path}")
        _app = Application(backend="uia").start(path)
        _main_window = _app.top_window()
        _main_window.wait('visible', timeout=timeout)
        log_action(f"Successfully started app and connected to window: '{_main_window.window_text()}'")
        return True
    except Exception as e:
        log_action(f"Failed to start application {path}: {e}", is_error=True)
        return False

def connect_to_app(title, timeout=30):
    """Connects to an already running application by its window title."""
    global _app, _main_window
    if not UIA_ENABLED: return False
    try:
        log_action(f"Connecting to app with title: '{title}'")
        _app = Application(backend="uia").connect(title_re=f".*{title}.*", timeout=timeout)
        _main_window = _app.top_window()
        _main_window.wait('visible', timeout=timeout)
        log_action(f"Successfully connected to window: '{_main_window.window_text()}'")
        return True
    except Exception as e:
        log_action(f"Failed to connect to application with title '{title}': {e}", is_error=True)
        return False

# --- Element Finding ---

def find_element_by_name(name, timeout=10):
    """Finds an element and stores it as the last found element."""
    global _last_found_element
    if not _main_window:
        log_action("Not connected to any window. Call start_app or connect_to_app first.", is_error=True)
        return None
    try:
        element = _main_window.child_window(title=name, found_index=0)
        element.wait('visible', timeout=timeout)
        log_action(f"Found element by name='{name}': {element}")
        _last_found_element = element
        return element
    except Exception:
        log_action(f"Element with name='{name}' not found.", is_error=True)
        _last_found_element = None
        return None

def find_element_by_automation_id(automation_id, timeout=10):
    """Finds an element and stores it as the last found element."""
    global _last_found_element
    if not _main_window:
        log_action("Not connected to any window. Call start_app or connect_to_app first.", is_error=True)
        return None
    try:
        element = _main_window.child_window(auto_id=automation_id, found_index=0)
        element.wait('visible', timeout=timeout)
        log_action(f"Found element by auto_id='{automation_id}': {element}")
        _last_found_element = element
        return element
    except Exception:
        log_action(f"Element with auto_id='{automation_id}' not found.", is_error=True)
        _last_found_element = None
        return None

# --- Element Interaction ---

def click_element(element=None):
    """Clicks a UIA element. If element is not provided, clicks the last found element."""
    target_element = element or _last_found_element
    if not target_element:
        log_action("No element to click. Find an element first.", is_error=True)
        return False
    try:
        target_element.click_input()
        log_action(f"Clicked element: {target_element}")
        return True
    except Exception as e:
        log_action(f"Failed to click element {target_element}: {e}", is_error=True)
        return False

def type_into_element(text, element=None):
    """Types text into a UIA element. If element is not provided, uses the last found one."""
    target_element = element or _last_found_element
    if not target_element:
        log_action("No element to type into. Find an element first.", is_error=True)
        return False
    try:
        target_element.type_keys(text, with_spaces=True)
        log_action(f"Typed '{text}' into element: {target_element}")
        return True
    except Exception as e:
        log_action(f"Failed to type into element {target_element}: {e}", is_error=True)
        return False

def get_element_text(element=None):
    """Gets the text from a UIA element. If element is not provided, uses the last found one."""
    target_element = element or _last_found_element
    if not target_element:
        log_action("No element to get text from. Find an element first.", is_error=True)
        return None
    try:
        text = target_element.window_text()
        log_action(f"Got text from element {target_element}: '{text}'")
        return text
    except Exception as e:
        log_action(f"Failed to get text from element {target_element}: {e}", is_error=True)
        return None

# --- Stub functions for non-Windows systems ---
def _disabled_stub(*args, **kwargs):
    log_action("UIA backend is disabled on this OS. This command is a no-op.", is_error=True)
    # Return a value that makes sense for the caller (e.g., False for success-based, None for object-based)
    return None

if not UIA_ENABLED:
    start_app = connect_to_app = find_element_by_name = find_element_by_automation_id = get_element_text = _disabled_stub
    # For functions that should return a boolean
    click_element = type_into_element = lambda *a, **k: False