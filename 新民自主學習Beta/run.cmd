@echo off
REM 导航到项目目录
cd /d "%~dp0"

REM 激活虚拟环境
call venv\Scripts\activate

REM 检查传入的参数
if "%1"=="clear" (
    REM 清除聊天记录
    python app.py clear
) else (
    REM 启动Flask应用程序
    python -m waitress --listen=0.0.0.0:8000 app:app
)

REM 保持命令行窗口打开
cmd /k
