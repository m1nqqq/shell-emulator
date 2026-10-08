@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Minimal VFS, interactive mode, exit from stdin: no motd =====
echo exit| python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv"
echo.

echo ===== 2. VFS with several files, interactive mode: motd is shown =====
echo exit| python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv"
echo.

echo ===== 3. Deep VFS, interactive mode: motd is shown =====
echo exit| python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv"
echo.

echo ===== 4. All three VFS variants with vfs-info =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
echo.
