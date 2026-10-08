@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Absolute paths for --vfs and --script =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\only_exit.txt"
echo.

echo ===== 2. Relative paths, run from the project root =====
pushd "%ROOT%"
python src\main.py --vfs scripts\vfs\minimal.csv --script scripts\startup\only_exit.txt
popd
echo.

echo ===== 3. Parameters in reverse order =====
python "%ROOT%\src\main.py" --script "%ROOT%\scripts\startup\only_exit.txt" --vfs "%ROOT%\scripts\vfs\minimal.csv"
echo.

echo ===== 4. Syntax --name=value =====
python "%ROOT%\src\main.py" --vfs="%ROOT%\scripts\vfs\minimal.csv" --script="%ROOT%\scripts\startup\stage2_basic.txt"
echo.

echo ===== 5. Only --script with a relative path =====
pushd "%ROOT%"
python src\main.py --script scripts\startup\stage2_basic.txt
popd
echo.
