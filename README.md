# Automated Testing Application

This is an automated testing application with a graphical user interface (GUI) built with Python and Tkinter.

## Project Structure
```
ATA_V2/
├── src/                    # Source code directory
│   ├── gui/               # GUI-related code (Tkinter Control Panel, dialogs)
│   ├── tests/             # Test case recording and running logic
│   ├── utils/             # Utility functions (config, logging, etc.)
│   └── Doc/               # Document generation utilities
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## Setup Instructions

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python src/gui/control_panel.py
   ```
   Or, if you have a main entry point:
   ```bash
   python src/main.py
   ```

## Features
- GUI interface for test management (Tkinter-based)
- Automated test execution and result logging
- Test case recording with screenshots and metadata
- Test result viewing and log management
- Test image updating and folder navigation
- Word document report generation from test results

## Troubleshooting
- **'str' object cannot be interpreted as an integer:**
  - This usually means a string was passed where an integer was expected (e.g., in `str.replace`). Check your code for correct argument types.
- **AttributeError: 'float' object has no attribute 'timestamp':**
  - This means you called `.timestamp()` on a float. Only call `.timestamp()` on `datetime` objects, not on floats (like those returned by `os.path.getctime`).
- **No GUI appears or errors about Tkinter:**
  - Ensure you are running the correct file and have Tkinter installed (it is included with most Python distributions).

## Development Status
- Core GUI and test management implemented
- Test recording and execution functional
- Result viewing and log management available
- Word document export implemented
- Further enhancements and bug fixes ongoing 