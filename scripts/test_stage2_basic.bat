@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Only --script =====
python "%ROOT%\src\main.py" --script "%ROOT%\scripts\startup\stage2_basic.txt"
echo.

echo ===== 2. Only --vfs, exit comes from stdin =====
echo exit| python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv"
echo.

echo ===== 3. Both --vfs and --script =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\stage2_basic.txt"
echo.

echo ===== 4. No parameters, exit comes from stdin =====
echo exit| python "%ROOT%\src\main.py"
echo.
