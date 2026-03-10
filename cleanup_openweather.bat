@echo off
REM OpenWeather Cleanup Batch Script
REM Run this after starting PostgreSQL to complete the cleanup

echo ================================================
echo OpenWeather Cleanup Script
echo ================================================
echo.

REM Check if PostgreSQL is running
sc query postgresql-x64-16 >nul 2>&1
if %errorlevel% neq 0 (
    echo PostgreSQL is not running!
    echo Starting PostgreSQL...
    net start postgresql-x64-16
    echo Waiting for PostgreSQL to start...
    timeout /t 5 /nobreak >nul
)

echo.
echo Running database cleanup...
echo.

cd /d "%~dp0"
"C:\Users\ffx3nb\AppData\Local\Python\bin\python.exe" db\cleanup_openweather.py

echo.
echo ================================================
echo Cleanup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Restart the web application if running
echo 2. Verify data in web dashboard
echo.

pause

