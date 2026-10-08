@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Deep VFS: all modes of ls, cd, cal, whoami, find =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv" --script "%ROOT%\scripts\startup\stage4_all.txt"
echo.

echo ===== 2. VFS with several files, hidden file and binary data =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv" --script "%ROOT%\scripts\startup\stage4_files.txt"
echo.
