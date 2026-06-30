@echo off
setlocal enabledelayedexpansion
echo ========================================
echo    Project Tracker - Docker Deploy
echo ========================================
echo.

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] Docker not running. Start Docker Desktop first.
    pause
    exit /b 1
)

docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    set DC=docker compose
) else (
    docker-compose version >nul 2>&1
    if %errorlevel% equ 0 (
        set DC=docker-compose
    ) else (
        echo [ERR] docker compose not found.
        pause
        exit /b 1
    )
)

echo [1/3] Building Docker image...
!DC! build
if %errorlevel% neq 0 (
    echo [ERR] Build failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
!DC! up -d
if %errorlevel% neq 0 (
    echo [ERR] Start failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Deploy complete!
echo    Open: http://localhost:8000
echo.
echo Commands:
echo    Logs : !DC! logs -f
echo    Stop : !DC! down
echo.
pause
endlocal
