@echo off
rem Monocat repair. Runs the same scan as INSTALL.bat in repair mode: it checks Python, the .venv
rem environment, the packages, the VLC engine, the shortcuts and the Open with entry, and fixes
rem whatever is broken after one question. Damaged packages are reinstalled, a damaged engine is downloaded again.
call "%~dp0INSTALL.bat" repair
exit /b %errorlevel%
