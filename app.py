import time

import customtkinter as ctk
import cv2
import mediapipe as mp
from PIL import Image
from plyer import notification

from config import FocusConfig
from csv_logger import SessionCsvLogger
from focus_core import FocusAnalyzer
from text_render import draw_unicode_text
from tray_manager import TrayManager


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


ZONE_UA = {
    "NORMAL": "НОРМА",
    "MID DOWN": "НИЖЧЕ НОРМИ",
    "DEEP DOWN": "СИЛЬНО ВНИЗ",
    "LOOKING UP": "ПОГЛЯД ВГОРУ",
    "AWAY/TURNED": "ВІДВЕРНУВСЯ",
    "NO FACE": "ОБЛИЧЧЯ НЕМАЄ",
}
ATTENTION_STATE_UA = {
    "NORMAL": "НОРМА",
    "WARNING": "ПОПЕРЕДЖЕННЯ",
    "CRITICAL": "КРИТИЧНО",
}


class FocusAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KPI Фокус Асистент")
        self.geometry("950x650")
        self.minsize(800, 500)

        self.cfg = FocusConfig()

        self.enable_ai = True

        self.analyzer = FocusAnalyzer(self.cfg, gemini_api_key=self.cfg.gemini_api_key, enable_ai=self.enable_ai)
        self.csv_logger = SessionCsvLogger("session_log.csv")

        self.is_running = False
        self._is_quitting = False
        self.cap = None
        self.face_mesh = None
        self._frame_image = None
        self._frame_debug_counter = 0  # Для налагодження

        self.tray = TrayManager(
            title="KPI Фокус Асистент",
            on_show=lambda: self.after(0, self.show_from_tray),
            on_toggle_session=lambda: self.after(0, self.toggle_session),
            on_exit=lambda: self.after(0, self.exit_app),
        )

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.tray.start()

    def _build_ui(self):
        # Main layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container
        self.main_container = ctk.CTkScrollableFrame(self, corner_radius=15)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text="Фокус Асистент",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, pady=(20, 10))

        # Privacy notice
        self.privacy_label = ctk.CTkLabel(
            self.main_container,
            text="⚠️ Ця програма використовує камеру для аналізу обличчя. Переконайтеся у згоді на моніторинг.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.privacy_label.grid(row=1, column=0, pady=(0, 10))

        # Video frame
        self.video_frame = ctk.CTkFrame(self.main_container, corner_radius=15, fg_color="lightgray")
        self.video_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(
            self.video_frame,
            text="Очікування запуску...",
            corner_radius=10,
        )
        self.video_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Stats cards
        self.stats_frame = ctk.CTkFrame(self.main_container, corner_radius=15, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, pady=10, padx=20, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Stat cards
        self.stat_focus_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10)
        self.stat_focus_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.stat_focus = ctk.CTkLabel(self.stat_focus_frame, text="Час фокусу\n0 с", font=ctk.CTkFont(size=16, weight="bold"))
        self.stat_focus.pack(pady=10, padx=10)

        self.stat_distractions_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10)
        self.stat_distractions_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.stat_distractions = ctk.CTkLabel(self.stat_distractions_frame, text="Відволікання\n0", font=ctk.CTkFont(size=16, weight="bold"))
        self.stat_distractions.pack(pady=10, padx=10)

        self.stat_bpm_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10)
        self.stat_bpm_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.stat_bpm = ctk.CTkLabel(self.stat_bpm_frame, text="BPM\n0", font=ctk.CTkFont(size=16, weight="bold"))
        self.stat_bpm.pack(pady=10, padx=10)

        self.stat_score_frame = ctk.CTkFrame(self.stats_frame, corner_radius=10)
        self.stat_score_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        self.stat_score = ctk.CTkLabel(self.stat_score_frame, text="Коефіцієнт фокусу\n0.0", font=ctk.CTkFont(size=16, weight="bold"))
        self.stat_score.pack(pady=10, padx=10)

        # State
        self.stat_state = ctk.CTkLabel(
            self.main_container,
            text=f"Режим: {self.cfg.experiment_mode}\nСтан: {ATTENTION_STATE_UA['NORMAL']}",
            font=ctk.CTkFont(size=14),
        )
        self.stat_state.grid(row=3, column=0, pady=10)

        # Controls
        self.controls_frame = ctk.CTkFrame(self.main_container, corner_radius=15, fg_color="transparent")
        self.controls_frame.grid(row=4, column=0, pady=10, padx=20, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.start_btn = ctk.CTkButton(
            self.controls_frame,
            text="Почати сесію",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_session,
            corner_radius=10,
        )
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)

        self.stop_btn = ctk.CTkButton(
            self.controls_frame,
            text="Зупинити",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.stop_session,
            state="disabled",
            corner_radius=10,
        )
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)

        self.tray_btn = ctk.CTkButton(
            self.controls_frame,
            text="Згорнути в трей",
            command=self.hide_to_tray,
            corner_radius=10,
        )
        self.tray_btn.grid(row=0, column=2, padx=5, pady=5)

        # AI Toggle
        self.ai_switch = ctk.CTkSwitch(
            self.main_container,
            text="Увімкнути AI Асистент",
            command=self.toggle_ai,
            onvalue=True,
            offvalue=False,
        )
        self.ai_switch.select()  # Default on
        self.ai_switch.grid(row=5, column=0, pady=10)

    def toggle_ai(self):
        self.enable_ai = self.ai_switch.get()
        self.analyzer.set_enable_ai(self.enable_ai)

    def toggle_session(self):
        if self.is_running:
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        """
        Start the focus monitoring session.
        Initializes camera, face mesh, and begins frame processing.
        """
        if self.is_running:
            return

        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise ValueError("Camera not accessible")

            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.7,
            )
        except Exception as e:
            self.video_label.configure(text=f"Помилка ініціалізації: {str(e)}", image=None)
            if self.cap:
                self.cap.release()
                self.cap = None
            return

        self.analyzer.reset(time.time(), mode=self.cfg.experiment_mode)
        self.csv_logger.start()

        self.is_running = True
        self.tray.update_session_state(True)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.video_label.configure(text="", image=self._frame_image)
        self.update_frame()

    def stop_session(self):
        self.is_running = False
        self.tray.update_session_state(False)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        if self.cap:
            self.cap.release()
            self.cap = None

        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None

        self.csv_logger.stop()
        self.video_label.configure(image=None, text="Сесію зупинено. Дані збережено в session_log.csv")

    def hide_to_tray(self):
        if not self.tray.available:
            self.video_label.configure(text="System Tray недоступний (встановіть pystray)")
            return
        self.withdraw()
        self.tray.notify("KPI Фокус Асистент", "Програма працює у фоні (System Tray).")

    def show_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_close(self):
        if self._is_quitting:
            return
        if self.tray.available:
            self.hide_to_tray()
            return
        self.exit_app()

    def exit_app(self):
        self._is_quitting = True
        self.stop_session()
        self.tray.stop()
        self.destroy()

    def update_frame(self):
        if not self.is_running or not self.cap or not self.face_mesh:
            return

        ok, frame = self.cap.read()
        if not ok:
            self.after(30, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        current_time = time.time()
        landmarks = None
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

        metrics = self.analyzer.process(landmarks, w, h, current_time)

        zone_label = ZONE_UA.get(metrics["zone"], metrics["zone"])
        rgb_frame = draw_unicode_text(
            rgb_frame,
            f"ЗОНА: {zone_label}",
            (30, h - 60),
            metrics["color"],
            rgb_input=True,
            font_size=32,
        )

        # DEBUG: Показуємо информацію про міцність у консоль
        if metrics["intervention_level"]:
            print(f"[INTERVENTION] {metrics['intervention_level']}: {metrics['intervention_message']}")

        if metrics["intervention_level"] == "WARNING" and metrics["intervention_message"]:
            self.tray.notify("Порада асистента", metrics["intervention_message"])
            try:
                notification.notify(
                    title="Порада асистента",
                    message=metrics["intervention_message"],
                    app_name="KPI Фокус Асистент",
                    timeout=5,
                )
            except Exception as exc:
                print(f"Не вдалося показати сповіщення: {exc}")

        if metrics["should_notify"] and metrics["intervention_message"]:
            try:
                notification.notify(
                    title="Зниження концентрації",
                    message=metrics["intervention_message"],
                    app_name="KPI Фокус Асистент",
                    timeout=5,
                )
            except Exception as exc:
                print(f"Не вдалося показати сповіщення: {exc}")

        minutes, seconds = divmod(metrics["focus_duration_sec"], 60)
        self.stat_focus.configure(text=f"Час фокусу:\n{minutes} хв {seconds} с")
        self.stat_distractions.configure(text=f"Відволікання:\n{metrics['distractions']}")
        self.stat_bpm.configure(text=f"BPM:\n{metrics['bpm']}")
        self.stat_score.configure(text=f"Коефіцієнт фокусу:\n{metrics['focus_score']}")
        state_label = ATTENTION_STATE_UA.get(metrics["attention_state"], metrics["attention_state"])
        self.stat_state.configure(text=f"Режим: {metrics['mode']}\nСтан: {state_label}")

        # DEBUG: Логування для налагодження
        self._frame_debug_counter += 1
        if self._frame_debug_counter % 30 == 0:
            print(f"[DEBUG] Focus: {metrics['focus_score']:.2f} | PERCLOS: {metrics['perclos']:.1f}% | EAR: L={metrics['ear_left']:.3f} R={metrics['ear_right']:.3f} | Blinks: {metrics['blinks_total']} | Zone: {metrics['zone']} | State: {metrics['attention_state']}")

        self.csv_logger.log_once_per_second(current_time, metrics)

        img = Image.fromarray(rgb_frame)
        self._frame_image = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
        self.video_label.configure(image=self._frame_image, text="")

        self.after(10, self.update_frame)


if __name__ == "__main__":
    app = FocusAssistantApp()
    app.mainloop()
