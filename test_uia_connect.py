"""
UIA test that connects to existing Notepad process.
"""
import sys
import time
import subprocess
import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows UI Automation stack.")


def test_uia_connect_notepad():
    from pywinauto.application import Application

    proc = subprocess.Popen(["notepad.exe"])
    time.sleep(2)

    try:
        app = Application(backend="uia").connect(process=proc.pid)
        window = app.top_window()

        edit = window.child_window(class_name="Edit", found_index=0)
        edit.set_focus()
        edit.type_keys("Hello from UIA Backend!", with_spaces=True, pause=0.05)

        time.sleep(1)
        text = edit.window_text()
        assert "Hello from UIA Backend!" in text

        window.close()
        time.sleep(0.5)
        try:
            app2 = Application(backend="uia").connect(title_re=".*Notepad")
            dlg = app2.top_window()
            btn = dlg.child_window(title="Don't Save", control_type="Button")
            btn.click()
        except Exception:
            pass
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"], capture_output=True, check=False)


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
