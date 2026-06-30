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

echo [1/3] Building Docker image...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERR] Build failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
docker-compose up -d
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
echo    Logs : docker-compose logs -f
echo    Stop : docker-compose down
echo.
pause
