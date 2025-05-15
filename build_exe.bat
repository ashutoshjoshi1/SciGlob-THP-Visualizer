@echo off
echo Building THP Visualizer executable...
echo Current directory: %CD%
pyinstaller --clean thp_visualizer.spec
if %ERRORLEVEL% NEQ 0 (
    echo Error: PyInstaller failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
echo PyInstaller completed successfully.
echo Checking if dist folder exists...
if exist dist (
    echo dist folder exists.
    echo Checking contents of dist folder:
    dir dist
    echo Checking if dist\THP_Visualizer folder exists:
    if exist dist\THP_Visualizer (
        echo dist\THP_Visualizer folder exists.
        echo Contents of dist\THP_Visualizer:
        dir dist\THP_Visualizer
    ) else (
        echo dist\THP_Visualizer folder does not exist!
    )
) else (
    echo dist folder does not exist!
)
echo Done!
pause
