@echo off
echo === ClaimGuard AI - Full Stack Network Start ===
echo.
echo Your devices on the same Wi-Fi can access:
echo   Patient Portal:   http://192.168.0.103:5174
echo   Admin Dashboard:  http://192.168.0.103:3000
echo   Backend API:      http://192.168.0.103:8000
echo.
echo [1] Setting up Python backend...
cd backend
pip install -r requirements.txt >nul 2>&1
if not exist .env copy .env.example .env 2>nul
echo.
echo [2] Starting backend server (network-accessible)...
start cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo.
echo [3] Starting Admin Dashboard (network-accessible)...
start cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo [4] Starting Patient Portal (network-accessible)...
start cmd /k "cd /d %~dp0frontend-portal && npm run dev"
echo.
echo === All 3 servers starting! ===
echo.
echo From THIS computer:
echo   Patient Portal:   http://localhost:5174
echo   Admin Dashboard:  http://localhost:3000
echo   API Docs:         http://localhost:8000/docs
echo.
echo From OTHER devices on same Wi-Fi:
echo   Patient Portal:   http://192.168.0.103:5174
echo   Admin Dashboard:  http://192.168.0.103:3000
echo.
pause
