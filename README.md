# SIGNAL — Django + MySQL Live Audio Translator

This project is the Django conversion of the uploaded Flask SIGNAL application. It keeps the existing landing page, authentication screens, and live translation dashboard while adding:

- Django authentication with persistent users
- MySQL configuration through `.env`
- Password-reset OTP generation, expiry, attempt limits, and email delivery
- Django Channels WebSocket communication
- Translation sessions and transcript history saved in MySQL
- Server-side system-audio, microphone, and combined capture on Windows
- Text-to-speech playback using Edge TTS

## Requirements

- Python 3.12 or newer
- MySQL 8 or MariaDB with `utf8mb4`
- Windows 10/11 for system-audio capture through WASAPI

The web application can start on Linux, but the included server-side audio-capture module is Windows-specific. On a hosted Linux server, it cannot capture audio playing on a visitor's computer.

## 1. Create the MySQL database

```sql
CREATE DATABASE signal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'signal_user'@'localhost' IDENTIFIED BY 'StrongPasswordHere';
GRANT ALL PRIVILEGES ON signal_db.* TO 'signal_user'@'localhost';
FLUSH PRIVILEGES;
```

## 2. Configure the project

Windows Command Prompt:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `.env`:

```env
MYSQL_DATABASE=signal_db
MYSQL_USER=signal_user
MYSQL_PASSWORD=StrongPasswordHere
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

## 3. Migrate and run

```bat
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Django's development server supports ASGI/Channels because Daphne is installed.

## Password reset OTP

The default email backend prints the OTP email in the terminal. Configure SMTP variables in `.env` to send real email.

## Important audio behavior

The included audio service captures the audio devices on the computer running Django. For local use, run Django on the same Windows computer where Zoom, YouTube, Teams, or microphone audio is playing.

For a public hosted version, browser-side audio capture or a Windows desktop companion agent is required.

## Temporary SQLite test

For a fast test without MySQL, set:

```env
USE_SQLITE=True
```

Do not use that setting when you want MySQL.
