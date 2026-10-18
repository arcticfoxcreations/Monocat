@echo off
rem Starts Monocat with a console so you can read any error message.
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py %*
pause
