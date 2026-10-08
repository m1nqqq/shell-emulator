@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."
set "COPY=%TEMP%\vfs_before.csv"

echo ===== 1. Deep VFS: all modes of touch =====
copy /y "%ROOT%\scripts\vfs\deep.csv" "%COPY%" >nul
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv" --script "%ROOT%\scripts\startup\stage5_all.txt"
fc /b "%ROOT%\scripts\vfs\deep.csv" "%COPY%" >nul && echo VFS file is unchanged: all changes were made in memory only
del "%COPY%"
echo.

echo ===== 2. VFS with several files, hidden file and folders =====
copy /y "%ROOT%\scripts\vfs\files.csv" "%COPY%" >nul
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv" --script "%ROOT%\scripts\startup\stage5_files.txt"
fc /b "%ROOT%\scripts\vfs\files.csv" "%COPY%" >nul && echo VFS file is unchanged: all changes were made in memory only
del "%COPY%"
echo.
