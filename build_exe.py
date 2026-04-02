"""
Build script for creating standalone EXE with PyInstaller.
Handles MediaPipe and other dependencies properly.
"""
import subprocess
import sys
from pathlib import Path

def build_exe():
    project_dir = Path(__file__).parent
    spec_file = project_dir / "KPIFocusAssistant.spec"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        "KPIFocusAssistant",
        "--add-data",
        "config.py:.",
        "--add-data", 
        "focus_core.py:.",
        "--add-data",
        "csv_logger.py:.",
        "--add-data",
        "analytics.py:.",
        "--add-data",
        "tray_manager.py:.",
        "--add-data",
        "text_render.py:.",
        "--add-data",
        "gemini_client.py:.",
        "--hidden-import=mediapipe",
        "--hidden-import=customtkinter",
        "--hidden-import=cv2",
        "--hidden-import=pandas",
        "--hidden-import=matplotlib",
        "app.py"
    ]
    
    print("Компіляція програми в EXE...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        exe_path = project_dir / "dist" / "KPIFocusAssistant.exe"
        print(f"\n✅ Готово! Файл: {exe_path}")
        print(f"Розмір: ~500-800 MB (залежить від залежностей)")
        print(f"\nДля запуску:")
        print(f"  {exe_path}")
    else:
        print(f"\n❌ Помилка при компіляції (код {result.returncode})")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
