import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# 1. ТЕХНІЧНІ НАЛАШТУВАННЯ
sns.set_theme(style="whitegrid", font_scale=1.1)
COLOR_BASE = "#D3D3D3"  # Світло-сірий (Baseline)
COLOR_ASSIST = "#5C4033" # Шоколадний (Assistant)
palette = {"Baseline": COLOR_BASE, "Assistant": COLOR_ASSIST}

baselines = [r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_1(2026-05-06_21.36.45).csv",
             r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_2(2026-05-07_19.21.06).csv",
             r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_3(2026-05-08_15.34.47).csv",
             r"C:\Users\Tetiana\Desktop\diplom_project\logs\baseline_4(2026-05-08_23.05.03).csv"]

assistants = [r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_1(2026-05-07_23.09.59).csv",
               r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_2(2026-05-08_18.33.11).csv",
               r"C:\Users\Tetiana\Desktop\diplom_project\logs\assistant_3(2026-05-08_22.21.20).csv"]

def load_and_clean(files, mode):
    list_df = []
    for f in files:
        df = pd.read_csv(f)
        df['Mode'] = mode
        list_df.append(df)
    return pd.concat(list_df, ignore_index=True)

df = pd.concat([load_and_clean(baselines, "Baseline"), load_and_clean(assistants, "Assistant")])

# Створюємо фігуру на 4 графіки
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# --- ГРАФІК 1: Box Plot (A/B Порівняння Focus_Score) ---
sns.boxplot(ax=axes[0, 0], data=df, x="Mode", y="Focus_Score", palette=palette, width=0.5)
axes[0, 0].set_title("1. Статистичний розподіл Focus Score", fontweight='bold')
axes[0, 0].set_ylabel("Коефіцієнт фокусу")

# --- ГРАФІК 2: Stacked Bar (Розподіл станів Attention_State) ---
state_dist = df.groupby(['Mode', 'Attention_State']).size().unstack(fill_value=0)
state_pct = state_dist.div(state_dist.sum(axis=1), axis=0) * 100
state_pct.plot(kind='bar', stacked=True, ax=axes[0, 1], color=['#e74c3c', '#f1c40f', '#2ecc71'])
axes[0, 1].set_title("2. Розподіл станів уваги (%)", fontweight='bold')
axes[0, 1].set_ylabel("Відсоток часу")
axes[0, 1].legend(title="Стан", loc='upper left', bbox_to_anchor=(1, 1))

# --- ГРАФІК 3: Scatter Plot + Regression (Втома vs Фокус) ---
# Беремо вибірку для швидкості
df_sample = df.sample(n=min(2000, len(df)))
sns.regplot(ax=axes[1, 0], data=df_sample[df_sample['Mode']=="Baseline"], x="PERCLOS", y="Focus_Score", 
            scatter_kws={'alpha':0.3, 'color':COLOR_BASE}, line_kws={'color':'red'}, label="Baseline")
sns.regplot(ax=axes[1, 0], data=df_sample[df_sample['Mode']=="Assistant"], x="PERCLOS", y="Focus_Score", 
            scatter_kws={'alpha':0.3, 'color':COLOR_ASSIST}, line_kws={'color':'green'}, label="Assistant")
axes[1, 0].set_title("3. Кореляція: Втома (PERCLOS) vs Фокус", fontweight='bold')
axes[1, 0].set_xlabel("PERCLOS (%)")
axes[1, 0].legend()

# --- ГРАФІК 4: Accumulated Inattention (Стрес-індикатор) ---
# Для наочності беремо середнє за секундами сесії
df['Sec'] = df.groupby('Mode').cumcount() % 2500 # приблизне вирівнювання
sns.lineplot(ax=axes[1, 1], data=df, x="Sec", y="Accumulated_Inattention_Sec", hue="Mode", palette=palette, linewidth=2)
axes[1, 1].set_title("4. Накопичена неуважність (динаміка)", fontweight='bold')
axes[1, 1].set_xlabel("Час сесії (сек)")
axes[1, 1].set_ylabel("Секунди відволікання")

plt.tight_layout()
plt.savefig("master_analytics_panel.png", dpi=300)
plt.show()