@echo off
setlocal
cd /d "%~dp0"

:: ============================================================================
:: ConvertFlow Desktop - Development Run Script
:: ============================================================================

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
    echo A ConvertFlow Desktop Python 3.12-t igenyel. Telepitsd a Python 3.12-t, majd futtasd ujra a run.bat fajlt.
    pause
    exit /b 1
)

:: Create/update virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo Virtualis korneyzet letrehozasa...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Nem sikerult letrehozni a virtualis korneyzetet.
        pause
        exit /b 1
    )
)

:: Install/update dependencies
echo Fuggetlensegek ellenorzese...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Hiba a fuggetlensegek telepitesenel.
    pause
    exit /b 1
)

:: Check FFmpeg
if not exist "tools\ffmpeg\ffmpeg.exe" (
    echo.
    echo FIGYELEM: FFmpeg nem talalhato!
    echo Masold be az ffmpeg.exe es ffprobe.exe fajlokat a tools\ffmpeg mappaba.
    echo Letoltes: https://www.gyan.dev/ffmpeg/builds/
    echo.
)

:: Run application
echo.
echo ConvertFlow Desktop inditasa...
echo.
".venv\Scripts\python.exe" main.py