@echo off
echo ===== THP Visualizer Build Script =====

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found in PATH.
    pause
    exit /b 1
)

echo Checking PyInstaller installation...
pip show pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo Error installing PyInstaller.
        pause
        exit /b 1
    )
)

echo Checking for icon file...
if not exist icon.ico (
    echo Icon file not found. Creating a simple one...
    python create_icon.py
)

echo Cleaning previous build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo Building THP Visualizer executable...
pyinstaller --clean thp_visualizer.spec
if %ERRORLEVEL% NEQ 0 (
    echo Error: PyInstaller failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo Checking build results...
if exist dist\THP_Visualizer\THP_Visualizer.exe (
    echo Build successful! Executable created at dist\THP_Visualizer\THP_Visualizer.exe
) else (
    echo Error: Executable not found in expected location.
    echo Checking dist folder contents:
    dir dist /s
)

echo Done!
pause