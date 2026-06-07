@echo off
echo ========================================================
echo        NAVEEN-AI JOB AGENT COMMAND CENTER
echo ========================================================
echo.
echo [1/2] Launching FastAPI Backend on http://localhost:8000...
start cmd /k "cd /d %~dp0 && .\venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000"

echo [2/2] Launching Vite Dev Server on http://localhost:5173...
start cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo ========================================================
echo Setup complete. Access the dashboard at:
echo - Local:   http://localhost:5173
echo - Network: http://192.168.0.105:5173
echo ========================================================
echo.
pause
