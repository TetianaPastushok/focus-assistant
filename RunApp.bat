@echo off
REM KPI Focus Assistant Launcher
REM Запускає додаток через Python вenv

cd /d "%~dp0"

REM Перевіряємо наявність venv
if not exist "venv310\Scripts\python.exe" (
    echo Помилка: venv310 не знайдено
    echo Встановіть залежності спочатку
    pause
    exit /b 1
)

REM Запускаємо додаток
echo Запуск KPI Focus Assistant...
start "" "venv310\Scripts\python.exe" app.py

REM Закриваємо консиль
exit /b 0
