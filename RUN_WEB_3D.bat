@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================================
echo   MEP AI COMPANY 3D - DEMO LOCAL
 echo ====================================================
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "MEP AI 3D SERVER" cmd /k "node server.mjs"
  timeout /t 2 >nul
  start "" "http://localhost:8766"
  goto :done
)
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "MEP AI 3D SERVER" cmd /k "py -m http.server 8766 --bind 127.0.0.1"
  timeout /t 2 >nul
  start "" "http://localhost:8766"
  goto :done
)
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "MEP AI 3D SERVER" cmd /k "python -m http.server 8766 --bind 127.0.0.1"
  timeout /t 2 >nul
  start "" "http://localhost:8766"
  goto :done
)
echo Can cai Node.js hoac Python 3 de chay ung dung.
pause
:done
