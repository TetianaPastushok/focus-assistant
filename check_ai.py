import google.generativeai as genai
from config import FocusConfig

# Load the API key from the configuration
cfg = FocusConfig()
genai.configure(api_key=cfg.gemini_api_key)

print("The following text-generation models are available for your key:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f" - {m.name}")