@echo off
cd /d "%~dp0"
echo [V5.7] Neu chua cai, chay: python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8766
pause
