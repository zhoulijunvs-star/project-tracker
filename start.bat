@echo off
chcp 65001 >nul
echo ========================================
echo   Project Tracker - Docker 部署
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

echo [1/3] 构建 Docker 镜像...
docker-compose build
if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo [2/3] 启动容器...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [错误] 启动失败
    pause
    exit /b 1
)

echo.
echo [3/3] 部署完成！
echo.
echo   访问地址: http://localhost:8000
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
pause
