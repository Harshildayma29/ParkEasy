@echo off
cd /d "%~dp0"
title ParkEasy - Student Project
where py >nul 2>&1
if not errorlevel 1 goto run_with_py
where python >nul 2>&1
if not errorlevel 1 goto run_with_python
echo Python is not installed or not on your PATH.
echo Install Python 3 from https://www.python.org/downloads/
echo During installation, tick "Add Python to PATH".
goto finished

:run_with_py
echo Starting ParkEasy... browser URL: http://127.0.0.1:5000/
py -3 server.py
goto finished

:run_with_python
echo Starting ParkEasy... browser URL: http://127.0.0.1:5000/
python server.py

:finished
echo.
echo This window stays open so you can read any error messages.
pause
