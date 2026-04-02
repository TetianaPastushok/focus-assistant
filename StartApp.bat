@echo off
chcp 65001 >nul
REM ============================================================
REM KPI Focus Assistant - Launcher Script
REM ============================================================
REM Це скрипт запускає додаток без потреби VS Code
REM Просто подвійний клік на цей файл - програма запуститься!
REM ============================================================

setlocal enabledelayedexpansion

REM Отримуємо шлях до скрипту
set "SCRIPT_DIR=%~dp0"
cd /d "!SCRIPT_DIR!"

REM Перевіряємо наявність Python venv
if not exist "venv310\Scripts\python.exe" (
    echo.
    echo ❌ ПОМИЛКА: Віртуальне середовище не знайдено!
    echo    Шукав у: !SCRIPT_DIR!venv310
    echo.
    echo Будь ласка, встановіть залежності:
    echo   python -m venv venv310
    echo   venv310\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Проверяем наличие app.py
if not exist "app.py" (
    echo ❌ ПОМИЛКА: app.py не знайдено!
    pause
    exit /b 1
)

REM Запускаємо додаток
echo.
echo 🚀 Запуск KPI Focus Assistant...
echo    Чекайте, зараз відкриється вікно...
echo.

start "" "!SCRIPT_DIR!venv310\Scripts\python.exe" "!SCRIPT_DIR!app.py"

REM Невелику затримку перед закриттям консолі
timeout /t 2 /nobreak >nul

exit /b 0
