@echo off
rem Monocat update. Checks the VLC engine, Monocat's own files and the Python packages first,
rem lists what is newer, asks ONE question, then updates it all and removes the old files.
rem Your settings, library and original file-icon backup are never touched.
setlocal EnableExtensions
cd /d "%~dp0"
title Monocat update
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

echo.
echo  Monocat update
echo  --------------

if not exist ".venv\Scripts\python.exe" (
    echo  Monocat is not set up in this folder yet. Run INSTALL.bat first, or REPAIR.bat if it broke.
    echo.
    pause
    exit /b 1
)

:waitclose
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\running.ps1" >nul 2>nul
if errorlevel 1 (
    echo  Monocat is running. Close it, then press any key to continue.
    pause >nul
    goto :waitclose
)

echo  Checking for updates. Nothing is changed during the check.
echo.
set "UP_VLC=0"
set "UP_APP=0"
set "UP_PKG=0"

echo  VLC engine:
".venv\Scripts\python.exe" tools\get_vlc.py --check
set "E=%errorlevel%"
if "%E%"=="10" set "UP_VLC=1"
if "%E%"=="1" echo    Could not check the VLC engine. Skipping it.
echo.

echo  Monocat:
".venv\Scripts\python.exe" tools\update.py --check
set "E=%errorlevel%"
if "%E%"=="10" set "UP_APP=1"
if "%E%"=="1" echo    Could not check for a new Monocat. Skipping it.
echo.

echo  Python packages:
".venv\Scripts\python.exe" -m pip install --upgrade --dry-run -r requirements.txt >"%TEMP%\monocat-pip.txt" 2>&1
findstr /c:"Would install" "%TEMP%\monocat-pip.txt" >nul 2>nul
if not errorlevel 1 set "UP_PKG=1"
del "%TEMP%\monocat-pip.txt" >nul 2>nul
if "%UP_PKG%"=="1" (echo    Newer packages are available.) else (echo    Up to date.)

set /a "TOTAL=UP_VLC+UP_APP+UP_PKG"
echo.
if "%TOTAL%"=="0" (
    echo  Everything is up to date. Nothing to do.
    echo.
    pause
    exit /b 0
)

echo  This will update:
if "%UP_VLC%"=="1" echo    - The bundled VLC engine, from get.videolan.org, checked with SHA-256. The old engine is deleted.
if "%UP_APP%"=="1" echo    - Monocat's program files, from its GitHub repository. A backup is kept in backup_before_update.
if "%UP_APP%"=="1" echo      Files the new version no longer has are removed.
if "%UP_PKG%"=="1" echo    - The Python packages in .venv, from PyPI. Old versions are replaced.
echo  Your settings, library and original file icons are kept.
echo.
choice /c YN /m "Update all of this now"
if errorlevel 2 (
    echo  Cancelled. Nothing was changed.
    exit /b 0
)

echo.
if "%UP_VLC%"=="0" goto :do_app
echo [VLC engine]
".venv\Scripts\python.exe" tools\get_vlc.py latest --yes
if errorlevel 1 (echo    The VLC engine was not updated. The current engine was left as it is.) else (echo    Done.)

:do_app
if "%UP_APP%"=="0" goto :do_pkg
echo [Monocat]
".venv\Scripts\python.exe" tools\update.py --yes
if errorlevel 1 (echo    Monocat was not updated. See the message above.) else (echo    Done.)

:do_pkg
if "%UP_PKG%"=="0" goto :verify
echo [Packages]
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 (echo    The package update failed. Monocat keeps working with the packages it has.) else (echo    Done.)

:verify
echo.
echo  Final check:
".venv\Scripts\python.exe" tools\doctor.py
echo.
echo  Update finished. Start Monocat from the Desktop or Start menu.
echo  If something broke, run REPAIR.bat.
echo.

rem Newer batch files were saved as NAME.bat.new. They are swapped in by a small helper after this
rem window closes, because a running batch file must not overwrite itself.
set "HASNEW=0"
for %%f in (*.bat.new) do set "HASNEW=1"
if "%HASNEW%"=="0" goto :end
>"%TEMP%\monocat-swap.bat" echo @echo off
>>"%TEMP%\monocat-swap.bat" echo timeout /t 2 /nobreak ^>nul
>>"%TEMP%\monocat-swap.bat" echo cd /d "%~dp0"
>>"%TEMP%\monocat-swap.bat" echo for %%%%f in (*.bat.new) do move /y "%%%%f" "%%%%~nf" ^>nul
>>"%TEMP%\monocat-swap.bat" echo del "%%~f0"
start "" /min cmd /c "%TEMP%\monocat-swap.bat"
echo  Newer batch files will be put in place as soon as you close this window.

:end
pause
exit /b 0
