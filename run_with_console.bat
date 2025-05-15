@echo off
echo Running THP Visualizer...
cd /d "%~dp0"
dist\THP_Visualizer\THP_Visualizer.exe
echo.
if %ERRORLEVEL% NEQ 0 (
    echo Application exited with error code: %ERRORLEVEL%
) else (
    echo Application exited normally.
)
pause