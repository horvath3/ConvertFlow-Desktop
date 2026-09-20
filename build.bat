@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ============================================================================
:: ConvertFlow Desktop - Build Script
:: Creates folder-based distribution and portable ZIP
:: ============================================================================

set "VERSION=1.0.0"
set "BUILD_DATE=%date:~-4%%date:~3,2%%date:~0,2%"
set "PYTHON_CMD="

:: Find Python 3.12
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 --version >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if "%PYTHON_CMD%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if "%PYTHON_CMD%"=="" (
    echo Python nem talalhato. Telepitsd a Python 3.12-t: https://www.python.org/downloads/
    pause
    exit /b 1
)

%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
    echo A build Python 3.12-t igenyel. Telepitsd a Python 3.12-t, majd futtasd ujra.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo ConvertFlow Desktop v%VERSION% - Build
echo ============================================================================
echo.

:: Create/update virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Virtualis korneyzet letrehozasa...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Hiba a virtualis korneyzet letrehozasanak soran.
        pause
        exit /b 1
    )
) else (
    echo [1/5] Virtualis korneyzet letezik, atugorva...
)

:: Install dependencies
echo [2/5] Fuggetlensegek telepitese...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Hiba a fuggetlensegek telepitesenel.
    pause
    exit /b 1
)

:: Generate version file
echo [3/5] Verzio informacio generalasa...
".venv\Scripts\python.exe" -c "
import json
from pathlib import Path
version_info = {
    'version': '%VERSION%',
    'build_date': '%BUILD_DATE%',
    'name': 'ConvertFlow Desktop',
    'author': 'ConvertFlow'
}
Path('version.json').write_text(json.dumps(version_info, indent=2))
print('Version file created')
"

:: Build with PyInstaller
echo [4/5] PyInstaller build futtatasa...
".venv\Scripts\pyinstaller.exe" ConvertFlowDesktop.spec --noconfirm
if errorlevel 1 (
    echo Hiba a PyInstaller build soran.
    pause
    exit /b 1
)

:: Copy FFmpeg binaries
echo [5/5] FFmpeg binarisok masolasa...
if not exist "dist\ConvertFlowDesktop\tools\ffmpeg" mkdir "dist\ConvertFlowDesktop\tools\ffmpeg"
if exist "tools\ffmpeg\ffmpeg.exe" copy /Y "tools\ffmpeg\ffmpeg.exe" "dist\ConvertFlowDesktop\tools\ffmpeg\" >nul
if exist "tools\ffmpeg\ffprobe.exe" copy /Y "tools\ffmpeg\ffprobe.exe" "dist\ConvertFlowDesktop\tools\ffmpeg\" >nul

:: Copy version file to dist
if exist "version.json" copy /Y "version.json" "dist\ConvertFlowDesktop\" >nul

echo.
echo ============================================================================
echo Build kesz!
echo ============================================================================
echo.
echo Futtathato: dist\ConvertFlowDesktop\ConvertFlowDesktop.exe
echo.

:: Create portable ZIP
echo Portable ZIP letrehozasa...
powershell -Command ^
    "Compress-Archive -Path 'dist\ConvertFlowDesktop\*' -DestinationPath 'dist\ConvertFlowDesktop-%VERSION%-portable.zip' -Force"

if exist "dist\ConvertFlowDesktop-%VERSION%-portable.zip" (
    echo.
    echo Portable ZIP kesz: dist\ConvertFlowDesktop-%VERSION%-portable.zip
    for %%f in ("dist\ConvertFlowDesktop-%VERSION%-portable.zip") do echo Meret: %%~zf byte
) else (
    echo Figyelem: ZIP letrehozasa sikertelen (PowerShell szukseges)
)

echo.
echo Build befejezve!
echo.
pause