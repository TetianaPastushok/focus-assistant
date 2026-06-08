from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

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
        self.history: list[str] = []  # History of recent advice to avoid repetition

    def _get_time_of_day(self) -> str:
        """Return the current time of day label."""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 20:
            return "day"
        elif 20 <= hour < 23:
            return "evening"
        else:
            return "night"
            
    def _build_prompt(self, metrics: dict, context: Optional[dict] = None) -> str:
        """Build the Gemini prompt from current metrics."""
        time_of_day = self._get_time_of_day()
        focus_score = metrics.get("focus_score", 0.5)
        perclos = metrics.get("perclos", 0.0)
        bpm = metrics.get("bpm", 15)
        zone = metrics.get("zone", "NORMAL")
        attention_state = metrics.get("attention_state", "NORMAL")
        continuous_inattention = metrics.get("continuous_inattention_sec", 0)
        distractions = metrics.get("distractions", 0)
        
        # Determine the main trigger reason (distraction, fatigue, posture, etc.)
        reason = metrics.get("intervention_reason", "UNKNOWN")

        # Provide recent advice context to avoid repetition
        prev_advice = "; ".join(self.history[-3:]) if self.history else "none"

        prompt = f"""
Ти — турботливий інтелектуальний асистент для підтримки продуктивності. Давай коротку пораду (1-2 речення) українською мовою на основі даних користувача.
Уникай повторення попередніх порад: {prev_advice}.

ГОЛОВНА ПРИЧИНА ЗВЕРНЕННЯ ДО КОРИСТУВАЧА: {reason}
(Де коди означають: 
BAD_POSTURE - довго сидить з нахиленою головою/сутулиться, 
FATIGUE - закриває очі/впадає в мікросон, 
DISTRACTION - дивиться вбік,
TOO_CLOSE - сидить аномально близько до екрана).

Поточні дані:
- Час доби: {time_of_day}
- Рівень фокусу: {focus_score:.2f} (0-1, де 1 — ідеальний)
- PERCLOS (втома): {perclos:.1f}%
- BPM (моргання): {bpm}
- Зона погляду: {zone}
- Стан уваги: {attention_state}

ПРАВИЛА ГЕНЕРАЦІЇ ПОРАДИ:
1. Якщо причина BAD_POSTURE: ОБОВ'ЯЗКОВО скажи вирівняти спину, підняти голову або розім'яти шию.
2. Якщо причина FATIGUE: порадь покліпати, подивитися вдалечінь або зробити гімнастику для очей.
3. Якщо причина DISTRACTION: м'яко нагадай повернутися до роботи.
4. Якщо причина TOO_CLOSE: терміново попроси відсунутися від екрана на безпечну відстань (60-70 см), щоб захистити зір.
5. Порада має бути емпатичною, дружньою та, за потреби, мотиваційною. Без зайвої води та вітань.
"""
        return prompt.strip()

    def generate_advice(self, metrics: dict, context: Optional[dict] = None) -> str:
        """Generate advice via Gemini."""
        prompt = self._build_prompt(metrics, context)
        try:
            # Select the API version in use
            if hasattr(self, 'model'):
                # Legacy API
                response = self.model.generate_content(prompt)
                advice = response.text.strip()
            elif hasattr(self, 'client'):
                # New API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                advice = response.text.strip()
            else:
                raise ValueError("AI model is not initialized.")

            self.history.append(advice)  # Track advice history
            if len(self.history) > 5:
                self.history.pop(0)
            return advice
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "Спробуйте зосередитися на завданні. Якщо втомилися — зробіть коротку перерву."


if __name__ == "__main__":
    
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