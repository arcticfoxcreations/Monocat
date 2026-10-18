@echo off
rem Monocat setup. Scans first, lists everything that is missing, asks ONE question, then installs it all.
rem Safe to run again at any time. REPAIR.bat runs this same script in repair mode.
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"
if /i "%MODE%"=="repair" (title Monocat repair) else (title Monocat setup)

echo.
if /i "%MODE%"=="repair" (echo  Monocat repair) else (echo  Monocat setup)
echo  ---------------
echo  Scanning this PC. Nothing is changed during the scan.
echo.

set "NEED_PY=0"
set "NEED_VENV=0"
set "NEED_PKG=0"
set "NEED_VLC=0"
set "NEED_SC=0"
set "NEED_ASSOC=0"
set "VENV_NEW=0"
set "PY="

rem ---------------------------------------------------------------- scan
if not exist "Monocat.exe" echo   [warning] Monocat.exe is missing from this folder. Shortcuts will not work until it is restored.
if not exist "main.py" (
    echo   main.py was not found. Run this file from inside the Monocat folder, not from inside the zip.
    pause
    exit /b 1
)

rem private environment
if not exist ".venv\Scripts\python.exe" goto :scan_novenv
".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if errorlevel 1 goto :scan_novenv
echo   [ok]      Private environment .venv
goto :scan_doctor

:scan_novenv
set "NEED_VENV=1"
set "NEED_PKG=1"
set "NEED_ASSOC=1"
set "VENV_NEW=1"
if exist ".venv" (echo   [broken]  Private environment .venv, it will be rebuilt) else (echo   [missing] Private environment .venv)
call :findpy
if defined PY goto :scan_pyok
set "NEED_PY=1"
echo   [missing] Python 3.10 or newer, 64-bit
goto :scan_novenv2
:scan_pyok
for /f "delims=" %%v in ('%PY% -c "import sys; print(sys.version.split()[0])"') do echo   [ok]      Python %%v, 64-bit
:scan_novenv2
echo   [missing] Python packages: PySide6-Essentials, python-vlc
if exist "vlc\libvlc.dll" if exist "vlc\plugins" (
    echo   [ok]      VLC engine files in the vlc folder
    goto :scan_shortcuts
)
set "NEED_VLC=1"
echo   [missing] VLC engine, unless a working VLC is already on this PC
goto :scan_shortcuts

:scan_doctor
".venv\Scripts\python.exe" tools\doctor.py
set "M=%errorlevel%"
set /a "NEED_PKG=M&1"
set /a "NEED_VLC=(M&2)/2"
set /a "NEED_ASSOC=(M&4)/4"

:scan_shortcuts
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\shortcuts.ps1" -Check >nul 2>nul
if errorlevel 1 (
    set "NEED_SC=1"
    echo   [missing] Desktop and Start menu shortcuts
) else (
    echo   [ok]      Desktop and Start menu shortcuts
)

rem ---------------------------------------------------------------- plan
set /a "TOTAL=NEED_PY+NEED_VENV+NEED_PKG+NEED_VLC+NEED_SC+NEED_ASSOC"
echo.
if "%TOTAL%"=="0" (
    echo  Everything is installed and working. Nothing to do.
    echo  If Monocat still misbehaves, run run-debug.bat and read the message it shows.
    echo.
    pause
    exit /b 0
)

echo  This will set up:
if "%NEED_PY%"=="1" echo    - Python 3.12 from the Python Software Foundation, installed with winget for your user only
if "%NEED_VENV%"=="1" echo    - A private environment in the .venv folder, inside this folder
if "%NEED_PKG%"=="1" echo    - PySide6-Essentials and python-vlc from PyPI, about 80 MB, into .venv
if "%NEED_VLC%"=="1" echo    - Monocat's own copy of the VLC engine from get.videolan.org, about 100 MB, checked with SHA-256,
if "%NEED_VLC%"=="1" echo      into the vlc folder. This does not install the VLC program.
if "%NEED_SC%"=="1" echo    - Desktop and Start menu shortcuts
if "%NEED_ASSOC%"=="1" echo    - The Open with entry and the cat icon for .mkv and .mov. Your default player is not changed.
echo.
echo  No administrator rights are needed. Anything you already have, such as your own Python or VLC,
echo  is never touched or removed.
echo.
choice /c YN /m "Install all of this now"
if errorlevel 2 (
    echo  Cancelled. Nothing was changed.
    exit /b 0
)

rem ---------------------------------------------------------------- do it
echo.
if "%NEED_PY%"=="0" goto :do_venv
echo [Python] Installing Python 3.12 ...
where winget >nul 2>nul
if errorlevel 1 goto :pymanual
winget install -e --id Python.Python.3.12 --scope user --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 goto :pymanual
echo python>".installed-python"
call :findpy
if not defined PY (
    echo          Python was installed, but Windows has not picked it up yet.
    echo          Close this window and run INSTALL.bat again. It will continue from here.
    pause
    exit /b 0
)
echo          Python is ready.
goto :do_venv

:pymanual
echo          Python could not be installed automatically.
echo          Install 64-bit Python 3.10 or newer from https://www.python.org/downloads/windows/
echo          tick "Add python.exe to PATH", then run INSTALL.bat again.
start "" https://www.python.org/downloads/windows/
pause
exit /b 1

:do_venv
if "%NEED_VENV%"=="0" goto :do_pkg
echo [Environment] Creating .venv ...
if exist ".venv" rmdir /s /q ".venv"
%PY% -m venv .venv
if errorlevel 1 (
    echo          Could not create the environment.
    pause
    exit /b 1
)
echo          Done.

:do_pkg
if "%NEED_PKG%"=="0" goto :do_vlc
echo [Packages] Installing PySide6-Essentials and python-vlc ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
if /i "%MODE%"=="repair" (
    ".venv\Scripts\python.exe" -m pip install --force-reinstall -r requirements.txt
) else (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
if errorlevel 1 (
    echo          Installing failed. Check your internet connection and run this file again.
    pause
    exit /b 1
)
echo          Done.
rem the VLC state could not be judged before the packages existed
".venv\Scripts\python.exe" tools\doctor.py >nul 2>nul
set "M=%errorlevel%"
set /a "NEED_VLC=(M&2)/2"

:do_vlc
if "%NEED_VLC%"=="0" goto :do_sc
echo [VLC engine] Downloading and checking the engine ...
if /i "%MODE%"=="repair" (
    ".venv\Scripts\python.exe" tools\get_vlc.py --yes --force
) else (
    ".venv\Scripts\python.exe" tools\get_vlc.py --yes
)
if errorlevel 1 (
    echo          The engine could not be downloaded. Check your internet connection and run this file again.
    echo          Alternatively install 64-bit VLC 3.0 from https://www.videolan.org/vlc/ and run this file again.
    pause
    exit /b 1
)

:do_sc
if "%NEED_SC%"=="0" goto :do_assoc
echo [Shortcuts] Creating Desktop and Start menu shortcuts ...
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\shortcuts.ps1"
if errorlevel 1 (echo          Could not create the shortcuts.) else (echo          Done.)

:do_assoc
if "%NEED_ASSOC%"=="0" goto :final
echo [Open with] Registering Monocat and the file icon ...
".venv\Scripts\python.exe" tools\assoc.py apply
if errorlevel 1 echo          Registration failed. Monocat still starts from the shortcut.

:final
echo.
echo  Final check:
".venv\Scripts\python.exe" tools\doctor.py
set "M=%errorlevel%"
echo.
if "%M%"=="0" (
    echo  Done. Start Monocat from the Desktop or Start menu.
) else (
    echo  Finished, but something above is still marked missing. Run REPAIR.bat, or run-debug.bat for details.
)
echo  UPDATE.bat gets newer versions. UNINSTALL.bat undoes the shortcuts, Open with entry and icons.
echo.
pause
exit /b 0

:findpy
set "PY="
where py >nul 2>nul && py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY exit /b 0
%PY% -c "import sys, struct; sys.exit(0 if sys.version_info >= (3, 10) and struct.calcsize('P') == 8 else 1)" >nul 2>nul
if errorlevel 1 set "PY="
exit /b 0
