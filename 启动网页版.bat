@echo off
rem ForeseeLearn 网页版启动器 - 双击即可运行
cd /d "%~dp0"
echo ========================================
echo   ForeseeLearn 学习助手 - 网页版
echo   启动后浏览器会自动打开，请勿关闭本窗口
echo   关闭本窗口 = 停止服务
echo ========================================
echo.
python web_app.py
pause
