@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel%==0 (
    pyw -3 main.py
    if %errorlevel%==0 exit /b 0
)

where pythonw >nul 2>nul
if %errorlevel%==0 (
    pythonw main.py
    if %errorlevel%==0 exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 main.py
    pause
    exit /b %errorlevel%
)

python main.py
pause
