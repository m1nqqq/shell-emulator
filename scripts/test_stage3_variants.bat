@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Minimal VFS: one file, no motd =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\stage3_all.txt"
echo.

echo ===== 2. VFS with several files: text, binary base64, hidden, motd =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv" --script "%ROOT%\scripts\startup\stage3_all.txt"
echo.

echo ===== 3. Deep VFS: six levels of folders and files, motd =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv" --script "%ROOT%\scripts\startup\stage3_all.txt"
echo.

echo ===== 4. No --vfs: empty VFS =====
python "%ROOT%\src\main.py" --script "%ROOT%\scripts\startup\stage3_all.txt"
echo.
