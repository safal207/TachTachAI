"""
UIA calculator test.
"""
import sys
import time
import subprocess
import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows UI Automation stack.")


def test_calculator_addition():
    from pywinauto import Desktop

    subprocess.Popen("calc.exe")
    time.sleep(3)

    try:
        calc = Desktop(backend="uia").window(title="Calculator")
        calc.wait("visible", timeout=10)

        calc.child_window(title="Five", control_type="Button").click()
        calc.child_window(title="Plus", control_type="Button").click()
        calc.child_window(title="Three", control_type="Button").click()
        calc.child_window(title="Equals", control_type="Button").click()
        time.sleep(0.5)

        result = calc.child_window(auto_id="CalculatorResults", control_type="Text")
        result_text = result.window_text()
        assert "8" in result_text

        calc.close()
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "CalculatorApp.exe"], capture_output=True, check=False)


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
