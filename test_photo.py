import time
import cv2
import mediapipe as mp
import os

# Import your modules
from config import FocusConfig
from csv_logger import SessionCsvLogger
from focus_core import FocusAnalyzer
from text_render import draw_unicode_text

# MediaPipe drawing setup
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(255, 255, 255))

ZONE_UA = {
    "NORMAL": "NORMAL",
    "MID DOWN": "MID DOWN",
    "DEEP DOWN": "DEEP DOWN",
    "LOOKING UP": "LOOKING UP",
    "AWAY/TURNED": "AWAY/TURNED",
    "NO FACE": "NO FACE",
    "TOO CLOSE": "TOO CLOSE"
}

def run_photo_assistant():
    print("--- STEP 1: Initializing Config ---")
    cfg = FocusConfig()
    analyzer = FocusAnalyzer(cfg)
    
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    logger = SessionCsvLogger("logs/photo_session_temp.csv")

    print("--- STEP 2: Opening Camera ---")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera not available")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    analyzer.reset(time.time(), mode=cfg.experiment_mode)
    logger.start()

    print("--- STEP 3: Starting Photo Session Loop ---")
    print("!!! PRESS ESC TO EXIT !!!")

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    ) as face_mesh:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Failed to grab frame")
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            current_time = time.time()
            landmarks = None

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                landmarks = face_landmarks.landmark

                # Drawing face mesh landmarks
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=drawing_spec
                )

            metrics = analyzer.process(landmarks, w, h, current_time)

            # UI Rendering
            zone_label = ZONE_UA.get(metrics["zone"], metrics["zone"])
            frame = draw_unicode_text(frame, f"ZONE: {zone_label}", (30, h - 60), metrics["color"], rgb_input=False, font_size=32)
            frame = draw_unicode_text(frame, f"Focus: {metrics['focus_duration_sec']}s", (30, 20), (255, 255, 0), rgb_input=False, font_size=28)
            frame = draw_unicode_text(frame, f"State: {metrics['attention_state']}", (30, 125), (200, 200, 200), rgb_input=False, font_size=24)

            cv2.imshow("KPI Photo Mode", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break

    logger.stop()
    cap.release()
    cv2.destroyAllWindows()
    print("--- SESSION FINISHED ---")

if __name__ == "__main__":
    run_photo_assistant()