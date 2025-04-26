@echo off
setlocal

set APP_FILE=main.py
set REQUIREMENTS_FILE=requirements.txt
set VENV_DIR=venv

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM Activate virtual environment
call %VENV_DIR%\Scripts\activate.bat

REM Install requirements
echo Installing dependencies from %REQUIREMENTS_FILE%...
pip install -r %REQUIREMENTS_FILE%

echo Starting the %APP_FILE%...
python %APP_FILE%

endlocal
