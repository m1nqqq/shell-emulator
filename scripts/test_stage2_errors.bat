@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Valid run with --vfs and --script, for comparison =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\only_exit.txt"
echo exit code: %errorlevel%
echo.

echo ===== 2. Startup script with failing commands =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\stage2_errors.txt"
echo exit code: %errorlevel%
echo.

echo ===== 3. Startup script does not exist =====
python "%ROOT%\src\main.py" --script "%ROOT%\scripts\startup\missing.txt"
echo exit code: %errorlevel%
echo.

echo ===== 4. Startup script path is a directory =====
python "%ROOT%\src\main.py" --script "%ROOT%\scripts"
echo exit code: %errorlevel%
echo.

echo ===== 5. Unknown parameter =====
python "%ROOT%\src\main.py" --bogus
echo exit code: %errorlevel%
echo.

echo ===== 6. Parameter without value =====
python "%ROOT%\src\main.py" --script
echo exit code: %errorlevel%
echo.
