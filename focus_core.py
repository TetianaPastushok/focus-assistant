from collections import deque
from math import hypot
from typing import Optional

from config import (
    CHIN,
    FOREHEAD,
    LEFT_CHEEK,
    LEFT_EYE,
    NOSE_TIP,
    RIGHT_CHEEK,
    RIGHT_EYE,
    FocusConfig,
)

try:
    from gemini_client import GeminiClient
except ImportError:
    GeminiClient = None


"""
FocusAnalyzer: Core class for real-time focus monitoring using computer vision and AI.

This class analyzes facial landmarks from webcam frames to compute focus metrics
such as PERCLOS (Percentage of Eye Closure), EAR (Eye Aspect Ratio), and head pose.
It provides interventions (warnings/critical alerts) and optional AI-generated advice.
"""

class FocusAnalyzer:
    """
    Analyzes user focus based on facial features and provides personalized interventions.

    Attributes:
        cfg (FocusConfig): Configuration parameters for thresholds and modes.
        mode (str): Current experiment mode ('assistant' or 'baseline').
        gemini_client (GeminiClient): AI client for dynamic advice generation.
        enable_ai (bool): Flag to enable/disable AI-powered interventions.
    """

    def __init__(self, cfg: Optional[FocusConfig] = None, mode: Optional[str] = None, gemini_api_key: Optional[str] = None, enable_ai: bool = True):
        """
        Initialize the FocusAnalyzer.

        Args:
            cfg: Configuration object with thresholds and settings.
            mode: Experiment mode ('assistant' for interventions, 'baseline' for measurement only).
            gemini_api_key: API key for Google Gemini AI.
            enable_ai: Enable AI-generated advice (default: True).
        """
        self.cfg = cfg or FocusConfig()
        self.mode = mode or self.cfg.experiment_mode
        self.gemini_client = GeminiClient(gemini_api_key) if GeminiClient and gemini_api_key else None
        self.enable_ai = enable_ai
        self.reset(0.0)
        self._last_ear_value = 0.5
        self._blink_in_progress = False
        
        self._pending_intervention = None
        self._pending_intervention_time = 0.0

    def set_enable_ai(self, enable: bool):
        """
        Enable or disable AI-powered advice generation.

        Args:
            enable: True to use AI for dynamic interventions, False for static messages.
        """
        self.enable_ai = enable

    def reset(self, start_time: float, mode: Optional[str] = None) -> None:
        if mode is not None:
            self.mode = mode

        self.session_start_time = start_time
        self.blink_count = 0
        self.distraction_count = 0
        self.focus_start_time = start_time
        self.current_focus_duration = 0.0
        self.last_zone = "NORMAL"

        self._blink_timestamps = deque()
        self._perclos_window = deque()
        self._window_closed = 0
        self._window_total = 0

        self._last_process_time = None
        self._inattention_window = deque()
        self._window_inattention_sec = 0.0
        self._window_total_sec = 0.0
        self._continuous_inattention_start = None
        self._continuous_focus_start = start_time
        self._yaw_history = deque(maxlen=max(1, self.cfg.pose_smoothing_frames))
        self._pitch_history = deque(maxlen=max(1, self.cfg.pose_smoothing_frames))
        self._away_candidate_since = None

        self.attention_state = "NORMAL"
        self._last_warning_time = 0.0
        self._last_critical_time = 0.0
        self._recovered_since_critical = True
        self._zone_change_time = start_time  # Час останної зміни зони (для уникнення false blinks)
        
        # Для виявлення моргання как переходу EAR від HIGH -> LOW -> HIGH
        self._ear_state = "OPEN"  # "OPEN" або "CLOSED"
        self._last_ear_value = 0.5
        self._blink_in_progress = False

    @staticmethod
    def calculate_ear(landmarks, eye_indices, width: int, height: int) -> float:
        coords = [(int(landmarks[idx].x * width), int(landmarks[idx].y * height)) for idx in eye_indices]
        v1 = hypot(coords[1][0] - coords[5][0], coords[1][1] - coords[5][1])
        v2 = hypot(coords[2][0] - coords[4][0], coords[2][1] - coords[4][1])
        h_dist = hypot(coords[0][0] - coords[3][0], coords[0][1] - coords[3][1])
        return (v1 + v2) / (2.0 * h_dist) if h_dist else 0.0

    @staticmethod
    def get_head_pose(landmarks) -> tuple[float, float]:
        nose = landmarks[NOSE_TIP]
        chin = landmarks[CHIN]
        forehead = landmarks[FOREHEAD]
        l_cheek = landmarks[LEFT_CHEEK]
        r_cheek = landmarks[RIGHT_CHEEK]

        dist_top = hypot(nose.x - forehead.x, nose.y - forehead.y)
        dist_bottom = hypot(nose.x - chin.x, nose.y - chin.y)
        pitch = dist_bottom / dist_top if dist_top else 1.0

        nose_to_left = hypot(nose.x - l_cheek.x, nose.y - l_cheek.y)
        nose_to_right = hypot(nose.x - r_cheek.x, nose.y - r_cheek.y)
        den = nose_to_left + nose_to_right
        yaw = abs(nose_to_left - nose_to_right) / den if den else 0.0
        return pitch, yaw

    def _classify_zone(self, pitch: float, yaw: float) -> tuple[str, tuple[int, int, int], float]:
        if yaw > self.cfg.yaw_limit:
            return "AWAY/TURNED", (255, 0, 0), 0.05
        if pitch > self.cfg.pitch_limit_up:
            return "LOOKING UP", (255, 165, 0), 0.05
        if pitch < self.cfg.pitch_limit_deep:
            return "DEEP DOWN", (255, 0, 0), self.cfg.thresh_deep_down
        if pitch < self.cfg.pitch_limit_mid:
            return "MID DOWN", (255, 165, 0), self.cfg.thresh_mid_down
        return "NORMAL", (0, 255, 0), self.cfg.thresh_normal

    def _smooth_pose(self, pitch: float, yaw: float) -> tuple[float, float]:
        self._pitch_history.append(pitch)
        self._yaw_history.append(yaw)
        smooth_pitch = sum(self._pitch_history) / len(self._pitch_history)
        smooth_yaw = sum(self._yaw_history) / len(self._yaw_history)
        return smooth_pitch, smooth_yaw

    def _detect_blink_motion(self, current_ear: float, current_zone: str) -> bool:
        """
        Виявляє справжнє моргання як перехід стану: OPEN -> CLOSED -> OPEN.
        Рахує як моргання тільки в зонах NORMAL та MID DOWN (не в DEEP DOWN/AWAY тощо).
        Повертає True якщо в цьому кадрі завершено моргання.
        """
        # Не рахуємо моргання 0.2 сек після зміни зони (це артефакт рухання голови)
        current_time = getattr(self, '_current_time', self._zone_change_time)
        time_since_zone_change = current_time - self._zone_change_time
        if time_since_zone_change < 0.2:
            return False
        
        # Визначаємо, чи очі в цьому кадрі закрити або відкрити
        # EAR = Eye Aspect Ratio
        # Нормально відкриті очі: 0.2-0.35
        # Закриті очі: < 0.10
        # Для стабільності використовуємо гістерезис: 0.10 (close) до 0.15 (open)
        open_threshold = 0.12  # Мінімум для визнання очей відкритими після закриття
        close_threshold = 0.08  # Максимум для визнання очей закритими
        
        if current_ear < close_threshold:
            new_ear_state = "CLOSED"
        elif current_ear > open_threshold:
            new_ear_state = "OPEN"
        else:
            # Гістерезис: залишаємо попередній стан
            new_ear_state = self._ear_state
        
        # Виявляємо переходи стану
        blink_detected = False
        
        if self._ear_state == "OPEN" and new_ear_state == "CLOSED":
            # Очі починають закриватися (перша фаза моргання)
            self._blink_in_progress = True
        elif self._ear_state == "CLOSED" and new_ear_state == "OPEN" and self._blink_in_progress:
            # Очі відкриваються після закриття (завершення моргання)
            if current_zone in ("NORMAL", "MID DOWN"):
                blink_detected = True
            self._blink_in_progress = False
        # Note: We don't reset _blink_in_progress when eyes stay CLOSED
        # That would cancel the blink motion detection mid-blink
        
        # Оновлюємо стан для наступного кадру
        self._ear_state = new_ear_state
        self._last_ear_value = current_ear
        
        return blink_detected

    def _apply_away_hold(
        self,
        current_time: float,
        raw_zone: str,
        raw_color: tuple[int, int, int],
        raw_threshold: float,
    ) -> tuple[str, tuple[int, int, int], float]:
        if raw_zone == "AWAY/TURNED":
            if self._away_candidate_since is None:
                self._away_candidate_since = current_time
            elapsed = current_time - self._away_candidate_since
            if elapsed >= self.cfg.away_hold_sec:
                return raw_zone, raw_color, raw_threshold

            # Keep previous focused-like state during hold to avoid false AWAY triggers.
            if self.last_zone in self.cfg.focused_zones:
                if self.last_zone == "NORMAL":
                    return "NORMAL", (0, 255, 0), self.cfg.thresh_normal
                if self.last_zone == "MID DOWN":
                    return "MID DOWN", (255, 165, 0), self.cfg.thresh_mid_down
                if self.last_zone == "DEEP DOWN":
                    return "DEEP DOWN", (255, 0, 0), self.cfg.thresh_deep_down
                return "NORMAL", (0, 255, 0), self.cfg.thresh_normal
            return "NORMAL", (0, 255, 0), self.cfg.thresh_normal

        self._away_candidate_since = None
        return raw_zone, raw_color, raw_threshold

    def _prune_windows(self, current_time: float) -> None:
        bpm_cutoff = current_time - self.cfg.bpm_window_sec
        while self._blink_timestamps and self._blink_timestamps[0] < bpm_cutoff:
            self._blink_timestamps.popleft()

        perclos_cutoff = current_time - self.cfg.perclos_window_sec
        while self._perclos_window and self._perclos_window[0][0] < perclos_cutoff:
            _, was_closed = self._perclos_window.popleft()
            self._window_total -= 1
            self._window_closed -= was_closed

    def _update_inattention_windows(self, current_time: float, inattentive: bool) -> tuple[float, float, float]:
        dt = 0.0
        if self._last_process_time is not None:
            dt = max(0.0, current_time - self._last_process_time)
            dt = min(dt, 1.0)
        self._last_process_time = current_time

        inattentive_dt = dt if inattentive else 0.0
        self._window_inattention_sec += inattentive_dt
        self._window_total_sec += dt
        self._inattention_window.append((current_time, inattentive_dt, dt))

        cutoff = current_time - self.cfg.warning_window_sec
        while self._inattention_window and self._inattention_window[0][0] < cutoff:
            _, old_inattentive_dt, old_dt = self._inattention_window.popleft()
            self._window_inattention_sec -= old_inattentive_dt
            self._window_total_sec -= old_dt

        if inattentive:
            if self._continuous_inattention_start is None:
                self._continuous_inattention_start = current_time
            self._continuous_focus_start = None
        else:
            self._continuous_inattention_start = None
            if self._continuous_focus_start is None:
                self._continuous_focus_start = current_time

        continuous_inattention_sec = (
            0.0 if self._continuous_inattention_start is None else current_time - self._continuous_inattention_start
        )
        continuous_focus_sec = 0.0 if self._continuous_focus_start is None else current_time - self._continuous_focus_start
        return continuous_inattention_sec, max(0.0, self._window_inattention_sec), continuous_focus_sec

    def _build_intervention(self, level: str, reason: str, metrics: dict) -> dict:
        if self.enable_ai and self.gemini_client:
            # Динамічна порада через Gemini
            advice = self.gemini_client.generate_advice(metrics)
        else:
            # Статичні повідомлення (як раніше)
            messages = {
                ("WARNING", "DISTRACTION"): "Ви почали відволікатися. Спробуйте повернути увагу до задачі.",
                ("WARNING", "FATIGUE"): "Ознаки втоми очей. Переведіть погляд вдалечінь на 20 секунд.",
                ("WARNING", "MIXED"): "Концентрація знижується. Зробіть коротку паузу на 1-2 хвилини.",
                ("CRITICAL", "DISTRACTION"): "Стійка втрата концентрації. Рекомендовано коротку перерву 3-5 хвилин.",
                ("CRITICAL", "FATIGUE"): "Високий рівень втоми. Зробіть перерву та вправи для очей.",
                ("CRITICAL", "MIXED"): "Критичне падіння фокусу. Зупиніться на коротку відновлювальну перерву.",
            }
            advice = messages.get((level, reason), "Зосередьтеся на завданні.")

        return {
            "intervention_level": level,
            "intervention_reason": reason,
            "intervention_message": advice,
            "event_type": f"{level}_{reason}",
            "should_notify": level == "CRITICAL",
        }

    def _evaluate_attention_state(
        self,
        current_time: float,
        inattentive: bool,
        continuous_inattention_sec: float,
        accumulated_inattention_sec: float,
        continuous_focus_sec: float,
        zone: str,
        perclos: float,
        focus_score: float,
        bpm: int,
    ) -> Optional[dict]:
        prev_state = self.attention_state
        warning_hit = (
            continuous_inattention_sec >= self.cfg.warning_grace_sec
            or accumulated_inattention_sec >= self.cfg.warning_accum_sec
        )
        critical_hit = (
            continuous_inattention_sec >= self.cfg.critical_grace_sec
            or accumulated_inattention_sec >= self.cfg.critical_accum_sec
        )

        if not inattentive:
            if continuous_focus_sec >= self.cfg.recovery_reset_sec:
                self.attention_state = "NORMAL"
                self._recovered_since_critical = True
        else:
            if critical_hit:
                self.attention_state = "CRITICAL"
            elif warning_hit and self.attention_state == "NORMAL":
                self.attention_state = "WARNING"

        if self.mode != "assistant":
            return None

        if current_time - self.session_start_time < self.cfg.session_warmup_sec:
            return None

        if zone not in self.cfg.focused_zones and perclos > self.cfg.perclos_high:
            reason = "MIXED"
        elif perclos > self.cfg.perclos_high:
            reason = "FATIGUE"
        else:
            reason = "DISTRACTION"

        if self.attention_state == "WARNING" and prev_state == "NORMAL":
            if current_time - self._last_warning_time >= self.cfg.warning_cooldown_sec:
                self._last_warning_time = current_time
                return self._build_intervention("WARNING", reason, {
                    "focus_score": focus_score,
                    "perclos": perclos,
                    "bpm": bpm,
                    "zone": zone,
                    "attention_state": self.attention_state,
                    "continuous_inattention_sec": continuous_inattention_sec,
                    "distractions": self.distraction_count,
                })

        if self.attention_state == "CRITICAL" and prev_state != "CRITICAL":
            cooldown_ready = (current_time - self._last_critical_time) >= self.cfg.critical_cooldown_sec
            if cooldown_ready or self._recovered_since_critical:
                self._last_critical_time = current_time
                self._recovered_since_critical = False
                return self._build_intervention("CRITICAL", reason, {
                    "focus_score": focus_score,
                    "perclos": perclos,
                    "bpm": bpm,
                    "zone": zone,
                    "attention_state": self.attention_state,
                    "continuous_inattention_sec": continuous_inattention_sec,
                    "distractions": self.distraction_count,
                })

        return None

    def _zone_gaze_score(self, zone: str) -> float:
        """Convert the detected head/gaze zone into a normalized gaze score."""
        zone_scores = {
            "NORMAL": 1.0,
            "MID DOWN": 0.85,
            "DEEP DOWN": 0.7,
            "LOOKING UP": 0.5,
            "AWAY/TURNED": 0.0,
            "NO FACE": 0.0,
        }
        return zone_scores.get(zone, 0.0)

    def _compute_focus_score(self, gaze_score: float, perclos: float, bpm: int) -> float:
        alertness_score = max(0.0, 1.0 - (perclos / 100.0))
        weights_sum = self.cfg.focus_w_gaze + self.cfg.focus_w_alertness
        if weights_sum <= 0:
            weights_sum = 1.0
        w_gaze = self.cfg.focus_w_gaze / weights_sum
        w_alertness = self.cfg.focus_w_alertness / weights_sum
        score = (w_gaze * gaze_score) + (w_alertness * alertness_score)
        if bpm < self.cfg.bpm_min or bpm > self.cfg.bpm_max:
            score -= 0.1
        return max(0.1, round(score, 2))

    def process(self, landmarks, width: int, height: int, current_time: float) -> dict:
        """
        Process facial landmarks to compute focus metrics and determine intervention level.

        Args:
            landmarks: MediaPipe facial landmarks.
            width: Frame width.
            height: Frame height.
            current_time: Current timestamp.

        Returns:
            dict: Analysis results including zone, metrics, and intervention data.
        """
        zone = "NO FACE"
        color = (255, 0, 0)
        pitch = 0.0
        yaw = 0.0
        left_ear = 0.0
        right_ear = 0.0
        active_ear = 0.0

        if landmarks is not None:
            pitch, yaw = self.get_head_pose(landmarks)
            pitch, yaw = self._smooth_pose(pitch, yaw)
            left_ear = self.calculate_ear(landmarks, LEFT_EYE, width, height)
            right_ear = self.calculate_ear(landmarks, RIGHT_EYE, width, height)
            active_ear = max(left_ear, right_ear) if yaw > self.cfg.yaw_limit else (left_ear + right_ear) / 2.0
            raw_zone, raw_color, raw_threshold = self._classify_zone(pitch, yaw)
            zone, color, threshold = self._apply_away_hold(current_time, raw_zone, raw_color, raw_threshold)

            is_closed = 1 if active_ear < threshold else 0
            self._window_total += 1
            self._window_closed += is_closed
            self._perclos_window.append((current_time, is_closed))

            # Виявляємо справжнє моргання як перехід: OPEN -> CLOSED -> OPEN
            self._current_time = current_time  # Для доступу в методі _detect_blink_motion
            blink_detected = self._detect_blink_motion(active_ear, raw_zone)
            if blink_detected:
                self.blink_count += 1
                self._blink_timestamps.append(current_time)

        if zone in self.cfg.focused_zones:
            self.current_focus_duration = current_time - self.focus_start_time
        else:
            if self.last_zone in self.cfg.focused_zones:
                self.distraction_count += 1
            self.focus_start_time = current_time
            self.current_focus_duration = 0.0
        
        # Записуємо час зміни зони
        if zone != self.last_zone:
            self._zone_change_time = current_time
        
        self.last_zone = zone

        self._prune_windows(current_time)

        bpm = len(self._blink_timestamps)
        perclos = (self._window_closed / self._window_total) * 100 if self._window_total else 0.0
        gaze_score = self._zone_gaze_score(zone)
        focus_score = self._compute_focus_score(gaze_score, perclos, bpm)

        # Стан неуважності базується ТІЛЬКИ на позі голови та закритих очах
        inattentive = (
            zone not in self.cfg.focused_zones
            or perclos > self.cfg.perclos_high
        )
        continuous_inattention_sec, accumulated_inattention_sec, continuous_focus_sec = self._update_inattention_windows(
            current_time,
            inattentive,
        )

        intervention = self._evaluate_attention_state(
            current_time=current_time,
            inattentive=inattentive,
            continuous_inattention_sec=continuous_inattention_sec,
            accumulated_inattention_sec=accumulated_inattention_sec,
            continuous_focus_sec=continuous_focus_sec,
            zone=zone,
            perclos=perclos,
            focus_score=focus_score,
            bpm=bpm,
        )

        # Якщо є нове повідомлення, "заморожуємо" його на 1.5 секунди для логера
        if intervention:
            self._pending_intervention = intervention
            self._pending_intervention_time = current_time
            
        # Якщо повідомлення старе (більше 1.5 сек), очищаємо його
        if self._pending_intervention and (current_time - self._pending_intervention_time) > 1.5:
            self._pending_intervention = None
            
        # Визначаємо, що саме передавати в метрики (нове або "заморожене")
        active_intervention = intervention or self._pending_intervention

        # Захист від порожніх словників:
        int_level = active_intervention.get("intervention_level", "") if active_intervention else ""
        int_reason = active_intervention.get("intervention_reason", "") if active_intervention else ""
        int_msg = active_intervention.get("intervention_message", "") if active_intervention else ""
        int_event = active_intervention.get("event_type", "") if active_intervention else ""

        return {
            "zone": zone,
            "color": color,
            "pitch": pitch,
            "yaw": yaw,
            "bpm": bpm,
            "perclos": round(perclos, 2),
            "focus_score": focus_score,
            "gaze_score": gaze_score,
            "focus_duration_sec": int(self.current_focus_duration),
            "distractions": self.distraction_count,
            "blinks_total": self.blink_count,
            "attention_state": self.attention_state,
            "mode": self.mode,
            "continuous_inattention_sec": round(continuous_inattention_sec, 2),
            "accumulated_inattention_sec": round(accumulated_inattention_sec, 2),
            
            # Тільки для нотифікацій
            "should_notify": bool(intervention and intervention.get("should_notify")),
            
            # Для логера
            "intervention_level": int_level,
            "intervention_reason": int_reason,
            "intervention_message": int_msg,
            "event_type": int_event,
            
            "ear_left": left_ear if landmarks else 0.0,
            "ear_right": right_ear if landmarks else 0.0,
            "ear_active": active_ear if landmarks else 0.0,
        }