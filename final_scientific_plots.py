import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# 1. НАЛАШТУВАННЯ ТА ШЛЯХИ
sns.set_theme(style="white", font_scale=1.1)
MATTE_BLACK = "#1c1c1c"
LIGHT_GRAY = "#D3D3D3"
CHOCOLATE_BROWN = "#5C4033"
palette = [LIGHT_GRAY, CHOCOLATE_BROWN]

# Твої файли (всі 7 для загальної статистики)
baselines = [
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_1(2026-05-06_21.36.45).csv",
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_2(2026-05-07_19.21.06).csv",
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_3(2026-05-08_15.34.47).csv",
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_4(2026-05-08_23.05.03).csv"
]
assistants = [
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_1(2026-05-07_23.09.59).csv",
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_2(2026-05-08_18.33.11).csv",
    r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_3(2026-05-08_22.21.20).csv"
]

def load_all(files, mode):
    data = []
    for f in files:
        df = pd.read_csv(f)
        df['Mode'] = mode
        data.append(df)
    return pd.concat(data)

print("Завантаження даних...")
df_all = pd.concat([load_all(baselines, "Baseline"), load_all(assistants, "Assistant")])

# --- ГРАФІК 1: ТВОЯ ПОРІВНЯЛЬНА ТАЙМЛІНІЯ (Baseline vs Assistant) ---
print("Малюю таймлайни...")
df_b_spec = pd.read_csv(baselines[0])
df_a_spec = pd.read_csv(assistants[0])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
ax1.plot(df_b_spec.index, df_b_spec["Focus_Score"], color=LIGHT_GRAY, linewidth=1.5)
ax1.set_title("Сесія без асистента: затяжні падіння концентрації", loc='left', fontweight='bold')
ax1.set_ylabel("Focus Score")

ax2.plot(df_a_spec.index, df_a_spec["Focus_Score"], color=CHOCOLATE_BROWN, linewidth=2)
interventions = df_a_spec[df_a_spec["Intervention_Message"].notna()]
ax2.scatter(interventions.index, interventions["Focus_Score"], color="red", s=50, zorder=5, label="Тригер ШІ")
ax2.set_title("Сесія з асистентом: корекція стану в реальному часі", loc='left', fontweight='bold')
ax2.set_ylabel("Focus Score")
ax2.set_xlabel("Час (секунди)")
plt.tight_layout()
plt.savefig("plot_1_timelines.png", dpi=300)

# --- ГРАФІК 2: ЩІЛЬНІСТЬ РОЗПОДІЛУ (Доказ стабільності) ---
print("Малюю щільність розподілу...")
plt.figure(figsize=(10, 5))
sns.kdeplot(data=df_all, x="Focus_Score", hue="Mode", fill=True, palette=palette, alpha=0.6)
plt.title("Розподіл рівнів фокусу: стабільність проти коливань", fontweight='bold')
plt.xlabel("Коефіцієнт зосередженості (0.0 - 1.0)")
plt.ylabel("Щільність")
sns.despine()
plt.savefig("plot_2_density.png", dpi=300)

# --- ГРАФІК 3: ЕФЕКТ ВТРУЧАННЯ (Causality Plot) ---
print("Аналізую ефект сповіщень...")
window = 15 # 15 секунд до і 15 після
segments = []
for idx in interventions.index:
    if idx > window and idx < len(df_a_spec) - window:
        segments.append(df_a_spec.iloc[idx-window:idx+window]["Focus_Score"].values)

if segments:
    mean_seg = np.mean(segments, axis=0)
    plt.figure(figsize=(8, 5))
    plt.plot(range(-window, window), mean_seg, color=CHOCOLATE_BROWN, linewidth=3)
    plt.axvline(x=0, color='red', linestyle='--', label='Момент сповіщення')
    plt.fill_between(range(-window, window), mean_seg-0.03, mean_seg+0.03, color=CHOCOLATE_BROWN, alpha=0.1)
    plt.title("Середня зміна фокусу після втручання ШІ", fontweight='bold')
    plt.xlabel("Секунди відносно тригера")
    plt.ylabel("Focus Score")
    plt.legend()
    sns.despine()
    plt.savefig("plot_3_ai_impact.png", dpi=300)

# --- ГРАФІК 4: HEATMAP (Timeline strip) ---
print("Генерую теплову карту...")
plt.figure(figsize=(12, 2))
# Беремо кожні 5-ту секунду для чіткості
strip = df_b_spec["Focus_Score"].values[::5]
sns.heatmap([strip], cmap="RdYlGn", cbar=False, xticklabels=False, yticklabels=False)
plt.title("Хронологія концентрації (Baseline): червоні зони — втрата уваги", fontweight='bold')
plt.savefig("plot_4_heatmap.png", dpi=300)

print("Всі графіки збережено!")