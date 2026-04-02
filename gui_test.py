import customtkinter as ctk

# Налаштування теми
ctk.set_appearance_mode("dark")  # Темна тема
ctk.set_default_color_theme("blue") # Сині акценти для кнопок

class FocusAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування головного вікна
        self.title("KPI Focus Assistant")
        self.geometry("900x600")
        self.minsize(800, 500)

        # --- СТВОРЕННЯ СІТКИ (Layout) ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # 📁 ЛІВА ПАНЕЛЬ (Меню)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Фокус Асистент", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.start_btn = ctk.CTkButton(self.sidebar_frame, text="▶ Почати сесію", fg_color="#28a745", hover_color="#218838")
        self.start_btn.grid(row=1, column=0, padx=20, pady=10)

        self.stop_btn = ctk.CTkButton(self.sidebar_frame, text="⏹ Зупинити", fg_color="#dc3545", hover_color="#c82333")
        self.stop_btn.grid(row=2, column=0, padx=20, pady=10)

        # ==========================================
        # 🖥️ ЦЕНТРАЛЬНА ПАНЕЛЬ (Камера та Статистика)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1) 
        self.main_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Заглушка для відео з камери
        self.video_label = ctk.CTkLabel(self.main_frame, text="Тут буде відео з веб-камери\n(Очікування запуску...)", 
                                        fg_color="gray15", corner_radius=10, font=ctk.CTkFont(size=18))
        self.video_label.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=20, pady=20)

        # --- ПАНЕЛЬ МЕТРИК (Внизу) ---
        self.stat_focus = ctk.CTkLabel(self.main_frame, text="Час фокусу:\n0 хв", font=ctk.CTkFont(size=18, weight="bold"))
        self.stat_focus.grid(row=1, column=0, padx=10, pady=20)

        self.stat_distractions = ctk.CTkLabel(self.main_frame, text="Відволікання:\n0", font=ctk.CTkFont(size=18, weight="bold"))
        self.stat_distractions.grid(row=1, column=1, padx=10, pady=20)

        self.stat_bpm = ctk.CTkLabel(self.main_frame, text="BPM:\n0", font=ctk.CTkFont(size=18, weight="bold"))
        self.stat_bpm.grid(row=1, column=2, padx=10, pady=20)

        self.stat_score = ctk.CTkLabel(self.main_frame, text="Коефіцієнт (Kc):\n0.0", font=ctk.CTkFont(size=18, weight="bold"))
        self.stat_score.grid(row=1, column=3, padx=10, pady=20)

if __name__ == "__main__":
    app = FocusAssistantApp()
    app.mainloop()