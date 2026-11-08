@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\test.ps1"
set "exitCode=%ERRORLEVEL%"
echo.
if not "%exitCode%"=="0" echo Tests failed with exit code %exitCode%.
pause
exit /b %exitCode%
