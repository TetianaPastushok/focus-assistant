from __future__ import annotations

import csv
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionCsvLogger:
    """Writes focus metrics to CSV once per second."""

    def __init__(self, path: str = "session_log.csv") -> None:
        self.path = Path(path)
        self._file = None
        self._writer = None
        self._last_second = None

    def start(self) -> None:
        self.stop()
        
        # 1. Створюємо папку 'logs', якщо її ще немає
        log_dir = self.path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Генеруємо унікальну назву файлу з поточною датою та часом
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{self.path.stem}_{now_str}{self.path.suffix}"
        
        # 3. Вказуємо шлях до нового файлу В СЕРЕДИНІ папки logs
        actual_path = log_dir / unique_filename
        
        self._file = actual_path.open("w", newline="", buffering=1, encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(
            [
                "TimestampISO",
                "Time",
                "Blinks",
                "BPM",
                "PERCLOS",
                "Focus_Duration_Sec",
                "Distractions",
                "Focus_Score",
                "Zone",
                "Mode",
                "Attention_State",
                "Continuous_Inattention_Sec",
                "Accumulated_Inattention_Sec",
                "Intervention_Level",
                "Intervention_Reason",
                "Intervention_Message",
                "Event_Type",
            ]
        )
        self._last_second = None
        logger.info(f"Session logging started: {actual_path}")

    def stop(self) -> None:
        if self._file:
            self._file.close()
            logger.info("Session logging stopped")
        self._file = None
        self._writer = None
        self._last_second = None

    def log_once_per_second(self, current_time: float, metrics: dict) -> bool:
        if not self._writer:
            return False

        current_second = int(current_time)
        if current_second == self._last_second:
            return False

        self._last_second = current_second
        now = datetime.now()
        self._writer.writerow(
            [
                now.isoformat(timespec="seconds"),
                time.strftime("%H:%M:%S", time.localtime(current_time)),
                metrics["blinks_total"],
                metrics["bpm"],
                metrics["perclos"],
                metrics["focus_duration_sec"],
                metrics["distractions"],
                metrics["focus_score"],
                metrics["zone"],
                metrics.get("mode", ""),
                metrics.get("attention_state", ""),
                metrics.get("continuous_inattention_sec", 0.0),
                metrics.get("accumulated_inattention_sec", 0.0),
                metrics.get("intervention_level", ""),
                metrics.get("intervention_reason", ""),
                metrics.get("intervention_message", ""),
                metrics.get("event_type", ""),
            ]
        )
        return True
