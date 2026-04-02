import time

import cv2
import mediapipe as mp

from config import FocusConfig
from csv_logger import SessionCsvLogger
from focus_core import FocusAnalyzer
from text_render import draw_unicode_text


ZONE_UA = {
    "NORMAL": "НОРМА",
    "MID DOWN": "НИЖЧЕ НОРМИ",
    "DEEP DOWN": "СИЛЬНО ВНИЗ",
    "LOOKING UP": "ПОГЛЯД ВГОРУ",
    "AWAY/TURNED": "ВІДВЕРНУВСЯ",
    "NO FACE": "ОБЛИЧЧЯ НЕМАЄ",
}


def run_console_assistant():
    cfg = FocusConfig()
    analyzer = FocusAnalyzer(cfg)
    logger = SessionCsvLogger("session_log.csv")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Камера недоступна")
        return

    analyzer.reset(time.time(), mode=cfg.experiment_mode)
    logger.start()

    with mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
    ) as face_mesh:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            current_time = time.time()
            landmarks = None
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark

            metrics = analyzer.process(landmarks, w, h, current_time)

            zone_label = ZONE_UA.get(metrics["zone"], metrics["zone"])
            frame = draw_unicode_text(
                frame,
                f"ЗОНА: {zone_label}",
                (30, h - 60),
                metrics["color"],
                rgb_input=False,
                font_size=32,
            )
            frame = draw_unicode_text(
                frame,
                f"Фокус: {metrics['focus_duration_sec']}с",
                (30, 20),
                (255, 255, 0),
                rgb_input=False,
                font_size=28,
            )
            frame = draw_unicode_text(
                frame,
                f"Відволікання: {metrics['distractions']}  BPM: {metrics['bpm']}",
                (30, 55),
                (0, 255, 0),
                rgb_input=False,
                font_size=28,
            )
            frame = draw_unicode_text(
                frame,
                f"PERCLOS: {metrics['perclos']}  Коеф.: {metrics['focus_score']}",
                (30, 90),
                (255, 100, 0),
                rgb_input=False,
                font_size=28,
            )
            frame = draw_unicode_text(
                frame,
                f"Стан: {metrics['attention_state']}  Режим: {metrics['mode']}",
                (30, 125),
                (200, 200, 200),
                rgb_input=False,
                font_size=24,
            )

            if metrics["event_type"]:
                print(f"[{metrics['event_type']}] {metrics['intervention_message']}")

            logger.log_once_per_second(current_time, metrics)

            cv2.imshow("KPI Фокус Асистент", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    logger.stop()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_console_assistant()
