@echo off
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

REM Detect docker-compose command (v1: docker-compose, v2: docker compose)
set DOCKER_COMPOSE=docker compose
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    docker-compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERR] docker compose not found.
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE=docker-compose
)

echo [1/3] Building Docker image...
%DOCKER_COMPOSE% build
if %errorlevel% neq 0 (
    echo [ERR] Build failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
%DOCKER_COMPOSE% up -d
if %errorlevel% neq 0 (
    echo [ERR] Start failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Deploy complete!
echo.
echo    Open: http://localhost:8000
echo.
echo Commands:
echo    Logs : %DOCKER_COMPOSE% logs -f
echo    Stop : %DOCKER_COMPOSE% down
echo.
pause
