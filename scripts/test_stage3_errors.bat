@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set "ROOT=%~dp0.."

echo ===== 1. Valid VFS variants for comparison: minimal, files, deep =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\minimal.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\files.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\deep.csv" --script "%ROOT%\scripts\startup\stage3_info.txt"
echo.

echo ===== 2. VFS file not found =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\missing.csv"
echo exit code: %errorlevel%
echo.

echo ===== 3. VFS path is a directory =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs"
echo exit code: %errorlevel%
echo.

echo ===== 4. Empty file =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\empty.csv"
echo exit code: %errorlevel%
echo.

echo ===== 5. Wrong header =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\bad_header.csv"
echo exit code: %errorlevel%
echo.

echo ===== 6. Wrong number of columns =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\bad_columns.csv"
echo exit code: %errorlevel%
echo.

echo ===== 7. Unknown element type =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\bad_type.csv"
echo exit code: %errorlevel%
echo.

echo ===== 8. Invalid base64 data =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\bad_base64.csv"
echo exit code: %errorlevel%
echo.

echo ===== 9. Unknown encoding name =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\bad_encoding_name.csv"
echo exit code: %errorlevel%
echo.

echo ===== 10. Relative path inside the VFS file =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\relative_path.csv"
echo exit code: %errorlevel%
echo.

echo ===== 11. Duplicate path =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\duplicate.csv"
echo exit code: %errorlevel%
echo.

echo ===== 12. File used as a folder =====
python "%ROOT%\src\main.py" --vfs "%ROOT%\scripts\vfs\invalid\file_as_dir.csv"
echo exit code: %errorlevel%
echo.
