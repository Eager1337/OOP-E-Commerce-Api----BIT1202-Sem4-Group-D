@echo off
echo =====================================================
echo   E-Commerce Inventory API — Auto Setup
echo   PROG315 | Limkokwing University | Sierra Leone
echo =====================================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Download from: https://python.org
    pause
    exit
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Installing all packages...
pip install fastapi==0.115.0 "uvicorn[standard]==0.32.0" sqlalchemy==2.0.36 psycopg2-binary==2.9.10 PyJWT==2.9.0 bcrypt "python-multipart==0.0.17" "pydantic==2.9.2" "pydantic-settings==2.6.1" "python-dotenv==1.0.1"

echo [4/4] Starting the server...
echo.
echo =====================================================
echo   Server is RUNNING!
echo   Open browser: http://localhost:8000/docs
echo   Press CTRL+C to stop
echo =====================================================
echo.
uvicorn app.main:app --reload
pause
