::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFBpQQQ2MAE+1EbsQ5+n//NaBrU4IR90+a5zSyaCPLvRd40brFQ==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFBpQQQ2MAE+/Fb4I5/jHxNqunWsSV/csR67Iyb2dNOEd/gvhbZNN
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
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
