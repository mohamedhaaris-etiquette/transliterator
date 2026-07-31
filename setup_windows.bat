@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
    py -3.13 -m venv venv
    if errorlevel 1 py -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist .env copy .env.example .env

echo.
echo Setup completed.
echo 1. Update MySQL credentials in .env
echo 2. Run: python manage.py migrate
echo 3. Run: python manage.py createsuperuser
echo 4. Run: python manage.py runserver
pause
