"""
Simple UIA smoke test to verify pywinauto works.
"""
import sys
import time
import subprocess
import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows UI Automation stack.")


def test_uia_simple_smoke():
    from pywinauto.application import Application

    app = Application(backend="uia").start("notepad.exe", timeout=10)
    window = app.window(title_re=".*Notepad")
    window.wait("visible", timeout=10)

    edit = window.child_window(class_name="Edit", found_index=0)
    edit.wait("visible", timeout=5)
    edit.type_keys("Hello from UIA test!", with_spaces=True)

    time.sleep(1)
    text = edit.window_text()
    assert "Hello from UIA test!" in text

    window.close()
    time.sleep(0.5)
    try:
        dialog = app.window(title_re=".*Notepad")
        dont_save_btn = dialog.child_window(title="Don't Save", control_type="Button")
        dont_save_btn.click()
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
