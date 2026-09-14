@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the Python environment...
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -c "import PySide6, openpyxl" >nul 2>nul
if errorlevel 1 (
    echo Installing Deployment Desk requirements...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

python main.py
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Deployment Desk could not start. Review the message above.
pause
exit /b 1
