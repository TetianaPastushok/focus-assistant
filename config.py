from dataclasses import dataclass
from typing import Optional


LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
NOSE_TIP = 1
CHIN = 152
FOREHEAD = 10
LEFT_CHEEK = 234
RIGHT_CHEEK = 454


@dataclass(frozen=True)
class FocusConfig:
    thresh_normal: float = 0.15
    thresh_mid_down: float = 0.12
    thresh_deep_down: float = 0.09
    pitch_limit_up: float = 1.25
    pitch_limit_mid: float = 0.75
    pitch_limit_deep: float = 0.60
    yaw_limit: float = 0.30
    consec_frames: int = 2
    bpm_min: int = 8
    bpm_max: int = 25
    perclos_high: float = 25.0  # Підвищуємо з 15% до 25% для менше помилкових спрацьовувань
    bpm_window_sec: int = 60
    perclos_window_sec: int = 60
    notify_interval_sec: int = 60

    # Weighted focus score: FocusScore = w1 * Gaze + w2 * (1 - PERCLOS)
    focus_w_gaze: float = 0.7
    focus_w_alertness: float = 0.3

    # Adaptive intervention logic
    session_warmup_sec: int = 25  # Дозволяємо користувачу розправитися перед перевіркою
    warning_grace_sec: int = 8  # Час безперервної втрати уваги до WARNING
    warning_accum_sec: int = 12  # Накопичуємо 12 сек втрати перед попередженням
    warning_window_sec: int = 20
    warning_cooldown_sec: int = 30
    critical_grace_sec: int = 16  # 16 сек знехтування перед CRITICAL
    critical_accum_sec: int = 18
    critical_cooldown_sec: int = 120
    recovery_reset_sec: int = 6  # 6 сек зосередженості перед скиданням
    pose_smoothing_frames: int = 15  # Збільшуємо з 7 до 15 для стабільнішої класифікації зони
    away_hold_sec: float = 0.8

    # "assistant" -> interventions enabled, "baseline" -> only measurement
    experiment_mode: str = "assistant"

    focused_zones: tuple[str, ...] = ("NORMAL", "MID DOWN", "DEEP DOWN")

    # Gemini API key (optional, for dynamic advice)
    gemini_api_key: Optional[str] = "AIzaSyAaA55EWsvyW5SFV6jwDTnNu5V7gQiHbrg"
