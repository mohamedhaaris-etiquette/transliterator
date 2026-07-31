CREATE DATABASE IF NOT EXISTS signal_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'signal_user'@'localhost'
  IDENTIFIED BY 'ChangeThisStrongPassword';

GRANT ALL PRIVILEGES ON signal_db.* TO 'signal_user'@'localhost';
FLUSH PRIVILEGES;
