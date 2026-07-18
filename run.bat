@echo off
:: ============================================================================
:: AO3 Backup Tool - Launcher
:: ============================================================================
:: Executes the main Python script (ao3_backup_tool.py) within the correct
:: execution environment.

:: Set the current working directory to the script's location to ensure
:: relative paths (e.g., list.txt, works/) resolve correctly.
cd /d "%~dp0"

:: Validate the Python installation.
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!]  Python was not found. Please install Python 3.10 or later
    echo       and ensure it is added to your system PATH.
    echo.
    pause
    exit /b 1
)

:: Execute the main application.
python ao3_backup_tool.py

:: Retain the console window if the application exits with a non-zero status
:: code to allow for error inspection.
if errorlevel 1 (
    echo.
    echo  [!]  The script exited with an error. See the traceback above.
    echo.
    pause
)
