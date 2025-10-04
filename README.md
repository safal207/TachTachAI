# TachTachAI - Smart GUI Test Automation Framework

AI-powered GUI testing framework that uses image recognition, OCR, and self-healing capabilities to automate desktop application testing.

## Features

- 🤖 **AI-Assisted Testing**: Intelligent test execution with self-healing
- 🖼️ **Image Recognition**: Find and click UI elements using screenshots
- 📝 **OCR Text Detection**: Locate and interact with text on screen
- 📊 **Performance Tracking**: Monitor test execution performance
- 🔄 **Self-Healing**: Automatic retry with adjusted parameters
- 📸 **Visual Regression Testing**: Compare screenshots for UI changes
- 📈 **Detailed Reports**: Comprehensive test reports with diagnostics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/safal207/TachTachAI.git
cd TachTachAI
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (required for text recognition):

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to your PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Quick Start

### 1. Learn UI Elements

Teach the framework about UI elements by capturing screenshots:

```bash
python learn.py
```

This will guide you through capturing and naming UI elements.

### 2. Create Test Scenarios

Use the scenario manager to create test workflows:

```bash
python scenario_manager.py
```

### 3. Run Tests

Execute your test scenarios:

```bash
# Run all scenarios
python test_runner.py

# Run specific scenario
python smart_cursor.py --run-scenario "login_test"
```

## Core Commands

### Smart Cursor Commands

```bash
# Click on a learned image
python smart_cursor.py --find-image <name>

# Click on text
python smart_cursor.py --find-text <text>

# Type text
python smart_cursor.py --type <text>

# Wait
python smart_cursor.py --wait <seconds>

# Assert image exists
python smart_cursor.py --assert-image <name>

# Assert text exists
python smart_cursor.py --assert-text <text>

# Wait for image to appear
python smart_cursor.py --wait-for-image <name> <timeout>

# Wait for text to appear
python smart_cursor.py --wait-for-text <text> <timeout>

# Check status
python smart_cursor.py --status
```

## Project Structure

```
TachTachAI/
├── smart_cursor.py         # Main automation engine
├── learn.py                # UI element learning tool
├── test_runner.py          # Test execution engine
├── scenario_manager.py     # Test scenario management
├── command_interface.py    # Command handler
├── diagnostics.py          # Failure diagnostics
├── performance_tracker.py  # Performance monitoring
├── logger.py               # Logging utilities
├── knowledge_base/         # Learned UI elements and scenarios
│   ├── kb.json            # Image knowledge base
│   ├── scenarios.json     # Test scenarios
│   └── visual_baselines/  # Visual regression baselines
└── reports/                # Test reports and screenshots
    ├── screenshots/       # Diagnostic screenshots
    └── history/          # Historical reports
```

## Example Scenario

```json
{
  "login_test": [
    {"action": "find-image", "target": "username_field"},
    {"action": "type", "target": "testuser"},
    {"action": "find-image", "target": "password_field"},
    {"action": "type", "target": "password123"},
    {"action": "find-image", "target": "login_button"},
    {"action": "wait", "target": "2"},
    {"action": "assert-text", "target": "Welcome"}
  ]
}
```

## Data-Driven Testing

Run tests with multiple data sets using CSV files:

```python
from test_runner import run_data_driven_suite

# CSV format: username,password
results = run_data_driven_suite("login_test", "login_data.csv")
```

## Visual Regression Testing

Create visual baselines and detect UI changes:

```bash
python smart_cursor.py --assert-visuals "homepage"
```

First run creates a baseline, subsequent runs compare against it.

## AI-Assisted Mode

The framework can work with AI recommendations:

1. AI generates test recommendations in `recommendations.json`
2. `command_interface.py` executes approved recommendations
3. Results are packaged for AI analysis

## Troubleshooting

### Common Issues

**OCR not working:**
- Ensure Tesseract is installed and in PATH
- Verify with: `tesseract --version`

**Image recognition failing:**
- Adjust confidence levels in `smart_cursor.py` (lines 66, 74)
- Ensure screen resolution matches learned images
- Re-learn UI elements if application updated

**Tests hanging:**
- Check timeout values in scenarios
- Verify application is responsive
- Review logs in `history.log`

## Configuration

Edit constants in respective files:
- `smart_cursor.py`: Image confidence, paths
- `diagnostics.py`: Screenshot settings
- `test_runner.py`: Python command, directories

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- GitHub Issues: https://github.com/safal207/TachTachAI/issues
- Check `history.log` for debugging information
