# 🚀 Запуск KPI Focus Assistant

## Варіант 1: Батник (рекомендовано) — просто подвійний клік

**Файл:** `StartApp.bat`

1. Знайдіть файл `StartApp.bat` у папці проекту
2. Подвійний клік на нього
3. Програма запуститься автоматично! 🎉

---

## Варіант 2: Через терміна PowerShell

```powershell
cd c:\Users\admin\Desktop\diplom_project
.\venv310\Scripts\Activate.ps1
python app.py
```

---

## Варіант 3: Через командний рядок (cmd)

```cmd
cd c:\Users\admin\Desktop\diplom_project
venv310\Scripts\activate.bat
python app.py
```

---

## Варіант 4: Швидкий запуск (без осі окна)

```cmd
c:\Users\admin\Desktop\diplom_project\venv310\Scripts\python.exe app.py
```

---

## 📋 Що робити потім

Після запуску додатка:

1. **Натисніть "Почати сесію"** → камера включиться
2. **Працюйте** 10-15 хвилин (дані записуватимуться в CSV)
3. **Натисніть "Зупинити"** → дані збережено в `session_log.csv`
4. **Аналіз**: 
   ```
   python analytics.py --csv session_log.csv --out my_report
   ```

---

## ❓ Якщо щось не працює

**Помилка "python: not found"**
- Переконайтесь, що venv310 встановлено
- Встановіть: `python -m venv venv310 && venv310\Scripts\pip install -r requirements.txt`

**Камера не включається**
- Перевірте, чи камера підключена та увімкнена
- Дайте дозвіл додатку на доступ до камери (Windows)

**Помилка з MediaPipe**
- Встановіть: `pip install mediapipe opencv-python`

---

**Все готово! Насолоджуйтесь асистентом! 😊**
