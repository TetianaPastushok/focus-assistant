import google.generativeai as genai
from config import FocusConfig

# Беремо твій ключ з конфігу
cfg = FocusConfig()
genai.configure(api_key=cfg.gemini_api_key)

print("Твоєму ключу доступні такі моделі для генерації тексту:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f" - {m.name}")