from dataclasses import dataclass
from typing import Optional


# MediaPipe Face Mesh landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
NOSE_TIP = 1
CHIN = 152
FOREHEAD = 10
LEFT_CHEEK = 234
RIGHT_CHEEK = 454
INNER_LEFT_EYE = 263  # For eye distance calculation
INNER_RIGHT_EYE = 33  # For eye distance calculation


@dataclass(frozen=True)
class FocusConfig:
    thresh_normal: float = 0.15
    thresh_mid_down: float = 0.12
    thresh_deep_down: float = 0.09
    pitch_limit_up: float = 1.20
    pitch_limit_mid: float = 0.80
    pitch_limit_deep: float = 0.70
    yaw_limit: float = 0.30
    consec_frames: int = 2
    bpm_min: int = 8
    bpm_max: int = 25
    perclos_high: float = 25.0  # Increased threshold to reduce false positives
    bpm_window_sec: int = 60
    perclos_window_sec: int = 60
    notify_interval_sec: int = 60

    # Weighted focus score: FocusScore = w1 * Gaze + w2 * (1 - PERCLOS)
    focus_w_gaze: float = 0.7
    focus_w_alertness: float = 0.3

    # Adaptive intervention timing
    session_warmup_sec: int = 10  # Warmup period before evaluation begins
    warning_grace_sec: int = 10  # Continuous inattention before WARNING
    warning_accum_sec: int = 16  # Total inattention seconds before WARNING
    warning_window_sec: int = 20
    warning_cooldown_sec: int = 30
    critical_grace_sec: int = 20  # Continuous inattention before CRITICAL
    critical_accum_sec: int = 24
    critical_cooldown_sec: int = 120
    recovery_reset_sec: int = 6  # Continuous focus needed to reset alert state
    pose_smoothing_frames: int = 15  # More smoothing for zone classification
    away_hold_sec: float = 2.0

    # Posture warning thresholds (seconds of sustained bad posture)
    mid_down_warning_sec: float = 45.0
    deep_down_warning_sec: float = 20.0
    too_close_warning_sec: float = 15.0
    too_close_distance_px: float = 180.0

    # Experiment mode: assistant = interventions enabled, baseline = measurement only
    experiment_mode: str = "assistant"

    focused_zones: tuple[str, ...] = ("NORMAL", "MID DOWN", "DEEP DOWN")

    # Gemini API key (optional)
    gemini_api_key: Optional[str] = "Enter your API key"