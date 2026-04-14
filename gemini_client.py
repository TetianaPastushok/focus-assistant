from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

try:
    from google import genai
except ImportError:
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None


class GeminiClient:
    """Client for generating dynamic advice using Google Gemini AI.
    
    Supports both new google.genai and legacy google.generativeai packages.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """Initialize Gemini client with API key."""
        if genai is None:
            raise ImportError("Install Google Generative AI: pip install google-genai or pip install google-generativeai")
        
        if hasattr(genai, 'configure'):
            # Legacy API
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
        else:
            # New API
            self.client = genai.Client(api_key=api_key)
            self.model_name = model
        self.history: list[str] = []  # Історія останніх 3 порад для уникнення повторів

    def _get_time_of_day(self) -> str:
        """Визначає час доби."""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "ранок"
        elif 12 <= hour < 18:
            return "день"
        elif 18 <= hour < 22:
            return "вечір"
        else:
            return "ніч"

    def _build_prompt(self, metrics: dict, context: Optional[dict] = None) -> str:
        """Будує промпт для Gemini на основі метрик."""
        time_of_day = self._get_time_of_day()
        focus_score = metrics.get("focus_score", 0.5)
        perclos = metrics.get("perclos", 0.0)
        bpm = metrics.get("bpm", 15)
        zone = metrics.get("zone", "NORMAL")
        attention_state = metrics.get("attention_state", "NORMAL")
        continuous_inattention = metrics.get("continuous_inattention_sec", 0)
        distractions = metrics.get("distractions", 0)

        # Контекст: попередні поради, щоб уникнути повторів
        prev_advice = "; ".join(self.history[-3:]) if self.history else "немає"

        prompt = f"""
Ти — інтелектуальний асистент для підтримки продуктивності. Давай коротку пораду (1-2 речення) українською мовою на основі даних користувача.
Уникай повторення попередніх порад: {prev_advice}.

Дані:
- Час доби: {time_of_day}
- Рівень фокусу: {focus_score:.2f} (0-1, де 1 — ідеальний)
- PERCLOS: {perclos:.1f}% (відсоток закритих очей, >15% — втома)
- BPM: {bpm} (моргання за хвилину, норма 8-25)
- Зона: {zone} (NORMAL — добре, інші — відволікання)
- Стан уваги: {attention_state} (NORMAL, WARNING, CRITICAL)
- Безперервне відволікання: {continuous_inattention:.1f} с
- Загальні відволікання: {distractions}

Порада має бути мотиваційною, конкретною та адаптованою до часу доби. Якщо пізно — радь відпочити. Якщо низький фокус — пропоную перерву або вправу.
"""
        return prompt.strip()

    def generate_advice(self, metrics: dict, context: Optional[dict] = None) -> str:
        """Генерує пораду через Gemini."""
        prompt = self._build_prompt(metrics, context)
        try:
            response = self.model.generate_content(prompt)
            advice = response.text.strip()
            self.history.append(advice)  # Додаємо в історію
            if len(self.history) > 5:  # Обмежуємо історію
                self.history.pop(0)
            return advice
        except Exception as e:
            print(f"Помилка Gemini: {e}")
            return "Спробуйте зосередитися на завданні. Якщо втомилися — зробіть коротку перерву."


# Приклад використання
if __name__ == "__main__":
    # Замініть на свій API ключ
    client = GeminiClient(api_key="YOUR_API_KEY")
    sample_metrics = {
        "focus_score": 0.4,
        "perclos": 20.0,
        "bpm": 10,
        "zone": "AWAY/TURNED",
        "attention_state": "WARNING",
        "continuous_inattention_sec": 15.0,
        "distractions": 5,
    }
    advice = client.generate_advice(sample_metrics)
    print(advice)