@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title toon-shorts-factory - setup
if not exist logs mkdir logs
set "LOG=%~dp0logs\setup.log"
echo ==== SETUP %date% %time% ==== > "%LOG%"
set "TOOLS=%~dp0tools"
if not exist "%TOOLS%" mkdir "%TOOLS%"

echo ============================================================
echo  1/4  PYTHON
echo ============================================================
set "PY="
call :find_python
if defined PY goto py_ok
echo Python not found. Installing Python 3.12...
where winget >nul 2>&1
if not errorlevel 1 (
  winget install --id Python.Python.3.12 -e --scope user --silent --accept-source-agreements --accept-package-agreements >> "%LOG%" 2>&1
  call :find_python
)
if defined PY goto py_ok
echo winget failed or missing. Downloading the official installer from python.org...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TOOLS%\python-installer.exe'" >> "%LOG%" 2>&1
if exist "%TOOLS%\python-installer.exe" (
  "%TOOLS%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0 >> "%LOG%" 2>&1
  call :find_python
)
if not defined PY (
  echo [ERROR] Could not install Python. See logs\setup.log
  goto fim
)
:py_ok
echo [OK] Python: %PY%
"%PY%" --version

echo.
echo ============================================================
echo  2/4  FFMPEG (installed inside tools\, nothing system-wide)
echo ============================================================
if exist "%TOOLS%\ffmpeg\bin\ffmpeg.exe" goto ff_ok
echo Downloading ffmpeg (about 100 MB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; $z='%TOOLS%\ffmpeg.zip'; try { Invoke-WebRequest -UseBasicParsing 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $z } catch { Invoke-WebRequest -UseBasicParsing 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile $z }; $d='%TOOLS%\ffmpeg_tmp'; if (Test-Path $d) { Remove-Item $d -Recurse -Force }; Expand-Archive $z $d -Force; $b = Get-ChildItem $d -Recurse -Filter ffmpeg.exe | Select-Object -First 1; New-Item -ItemType Directory -Force '%TOOLS%\ffmpeg' | Out-Null; Move-Item -LiteralPath ($b.DirectoryName) -Destination '%TOOLS%\ffmpeg\bin' -Force; Remove-Item $d -Recurse -Force; Remove-Item $z -Force" >> "%LOG%" 2>&1
if not exist "%TOOLS%\ffmpeg\bin\ffmpeg.exe" (
  echo [ERROR] Could not download ffmpeg. See logs\setup.log
  goto fim
)
:ff_ok
set "PATH=%TOOLS%\ffmpeg\bin;%PATH%"
for /f "tokens=1-3" %%a in ('ffmpeg -hide_banner -version ^| findstr /b "ffmpeg"') do echo [OK] %%a %%b %%c

echo.
echo ============================================================
echo  3/4  VISUAL C++ RUNTIME (needed by the subtitle renderer)
echo ============================================================
if exist "%SystemRoot%\System32\msvcp140.dll" (
  echo [OK] Visual C++ already installed
) else (
  echo Installing the Visual C++ Redistributable. If Windows asks for permission, click YES.
  where winget >nul 2>&1 && winget install --id Microsoft.VCRedist.2015+.x64 -e --silent --accept-source-agreements --accept-package-agreements >> "%LOG%" 2>&1
  if not exist "%SystemRoot%\System32\msvcp140.dll" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%TOOLS%\vc_redist.x64.exe'" >> "%LOG%" 2>&1
    if exist "%TOOLS%\vc_redist.x64.exe" "%TOOLS%\vc_redist.x64.exe" /install /quiet /norestart >> "%LOG%" 2>&1
  )
)

echo.
echo ============================================================
echo  4/4  VIRTUAL ENVIRONMENT AND PACKAGES
echo ============================================================
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" --version >nul 2>&1
  if errorlevel 1 (
    echo The existing .venv is broken. Renaming it to .venv_old
    if exist ".venv_old" rmdir /s /q ".venv_old"
    ren ".venv" ".venv_old"
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating .venv ...
  "%PY%" -m venv .venv >> "%LOG%" 2>&1
)
if not exist ".venv\Scripts\python.exe" ( echo [ERROR] Could not create .venv & goto fim )
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%LOG%" 2>&1
echo Installing packages (a few minutes)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 ( echo [ERROR] pip failed. See logs\setup.log & goto fim )
echo [OK] Packages installed

if not exist secrets mkdir secrets
echo.
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m toonshorts check
echo.
echo SETUP DONE. Next: put your keys in secrets\ (see secrets\README.md) and follow the README.
:fim
echo ==== FIM %date% %time% ==== >> "%LOG%"
echo.
pause
exit /b

:find_python
set "PY="
for %%v in (313 312 311 310) do (
  if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
  if not defined PY if exist "%ProgramFiles%\Python%%v\python.exe" set "PY=%ProgramFiles%\Python%%v\python.exe"
)
exit /b
