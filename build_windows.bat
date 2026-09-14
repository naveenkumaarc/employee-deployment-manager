@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
if errorlevel 1 goto :error

python tools\generate_icons.py
if errorlevel 1 goto :error

python -m pytest -q
if errorlevel 1 goto :error

python -m PyInstaller --noconfirm --clean DeploymentDesk.spec
if errorlevel 1 goto :error

echo.
echo Build complete: dist\DeploymentDesk.exe
exit /b 0

:error
echo.
echo Build failed. Review the message above.
pause
exit /b 1
