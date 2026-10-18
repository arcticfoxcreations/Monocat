@echo off
rem Removes what INSTALL.bat added: shortcuts, the Open with entry, and the changed file icons.
rem Optionally removes your Monocat settings, and Python if INSTALL.bat installed it. Both default to No.
rem The VLC engine lives in the vlc folder inside Monocat and goes away when you delete the folder.
setlocal EnableExtensions
cd /d "%~dp0"
title Monocat uninstall

echo.
echo  Monocat uninstall
echo  -----------------
echo  This will:
echo    - restore the original .mkv and .mov icons
echo    - remove the Open with entry
echo    - remove the Desktop and Start menu shortcuts
echo  It does not delete this folder or your settings. You are asked about those afterwards.
echo.
choice /c YN /m "Uninstall now"
if errorlevel 2 (
    echo  Cancelled. Nothing was changed.
    exit /b 0
)

set "PYX="
if exist ".venv\Scripts\python.exe" ".venv\Scripts\python.exe" -c "import sys" >nul 2>nul && set "PYX=.venv\Scripts\python.exe"
if not defined PYX where py >nul 2>nul && py -3 -c "import sys" >nul 2>nul && set "PYX=py -3"
if not defined PYX where python >nul 2>nul && python -c "import sys" >nul 2>nul && set "PYX=python"

echo.
if defined PYX goto :restore
echo  No working Python was found, so the file icons could not be restored automatically.
echo  Reinstalling VLC restores its original icon.
goto :shortcuts
:restore
%PYX% tools\assoc.py restore

:shortcuts
powershell -NoProfile -ExecutionPolicy Bypass -Command "foreach($d in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))){ Remove-Item -LiteralPath (Join-Path $d 'Monocat.lnk') -ErrorAction SilentlyContinue; Remove-Item -LiteralPath (Join-Path $d 'Mono Player.lnk') -ErrorAction SilentlyContinue }"
echo  Shortcuts removed.

if not exist "%APPDATA%\Monocat" goto :python
echo.
echo  Your settings, library and watch history are in %%APPDATA%%\Monocat.
choice /c YN /n /m "Delete them too [Y/N]? "
if errorlevel 2 goto :python
rmdir /s /q "%APPDATA%\Monocat"
echo  Settings deleted.

:python
if not exist ".installed-python" goto :finish
echo.
echo  INSTALL.bat installed Python 3.12 for you. Other programs on this PC may also use it.
echo  If you are unsure, keep it. A Python you installed yourself is never touched.
where winget >nul 2>nul
if errorlevel 1 goto :finish
choice /c YN /n /m "Remove the Python that INSTALL.bat installed [Y/N]? "
if errorlevel 2 goto :finish
winget uninstall -e --id Python.Python.3.12
if not errorlevel 1 del ".installed-python"

:finish
echo.
echo  Done. You can now delete this folder. That also removes the bundled VLC engine in the vlc folder.
echo.
pause
exit /b 0
