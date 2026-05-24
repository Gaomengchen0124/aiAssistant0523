@echo off
chcp 65001 >nul
title KOL 达人推荐系统 - 演示模式
color 0A

echo ============================================================
echo    AI KOL / 达人匹配助手 - 演示模式
echo ============================================================
echo.

REM 检查 cloudflared 是否存在
if not exist "cloudflared.exe" (
    echo [错误] 未找到 cloudflared.exe，请先下载：
    echo.
    echo   PowerShell 命令：
    echo   Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
    echo.
    echo 或者浏览器访问：https://github.com/cloudflare/cloudflared/releases/latest
    echo 下载 cloudflared-windows-amd64.exe 放到当前目录并重命名为 cloudflared.exe
    echo.
    pause
    exit /b 1
)

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保 Python 已安装并加入 PATH
    pause
    exit /b 1
)

REM 检查依赖
if not exist "web\app.py" (
    echo [错误] 未找到 web\app.py，请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/3] 检查完成，准备启动服务...
echo.

REM 启动 Flask 服务（后台）
echo [2/3] 启动 Flask 服务...
start "Flask Server" cmd /c "python web\app.py"

REM 等待 Flask 启动
timeout /t 3 /nobreak >nul

REM 启动 Cloudflare Tunnel
echo [3/3] 启动 Cloudflare Tunnel，正在生成公网链接...
echo.
echo ============================================================
echo    公网访问地址将在下方显示（请等待几秒）
echo ============================================================
echo.

cloudflared.exe tunnel --url http://localhost:5000

echo.
echo ============================================================
echo    Tunnel 已关闭，Flask 服务仍在运行
echo    请关闭 Flask Server 窗口以完全停止服务
echo ============================================================
pause
