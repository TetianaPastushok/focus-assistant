import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Налаштування строгого академічного стилю
sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)

# Твої файли
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

def load_and_prep(files, mode_name):
    all_data = []
    for f in files:
        df = pd.read_csv(f, encoding="utf-8")
        df["TimestampISO"] = pd.to_datetime(df["TimestampISO"], errors="coerce")
        df = df.dropna(subset=["TimestampISO"]).sort_values("TimestampISO")
        
        # Вираховуємо відносну хвилину від початку сесії (для осі Х)
        start_time = df["TimestampISO"].iloc[0]
        df["Minute"] = (df["TimestampISO"] - start_time).dt.total_seconds() / 60.0
        
        df["Режим"] = mode_name
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

print("Завантаження даних...")
df_base = load_and_prep(baselines, "Без асистента (Baseline)")
df_assist = load_and_prep(assistants, "З ШІ-асистентом")

# Об'єднуємо все в один великий датафрейм
df_all = pd.concat([df_base, df_assist], ignore_index=True)
out_dir = Path("diploma_graphs_pro")
out_dir.mkdir(exist_ok=True)

print("Малюємо графіки...")

# ==========================================
# ГРАФІК 1: Динаміка фокусу у часі (Lineplot з довірчим інтервалом)
# ==========================================
plt.figure(figsize=(10, 5))
# Seaborn автоматично усереднить дані з усіх сесій і намалює тінь (95% довірчий інтервал)
sns.lineplot(data=df_all, x="Minute", y="Focus_Score", hue="Режим", 
             palette=["#d62728", "#2ca02c"], linewidth=2)
plt.title("Динаміка зосередженості (усереднено за всіма сесіями)")
plt.xlabel("Час від початку роботи (хвилини)")
plt.ylabel("Focus Score")
plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig(out_dir / "pro_focus_trend.png", dpi=300)
plt.close()

# ==========================================
# ГРАФІК 2: Щільність розподілу PERCLOS (Violin Plot)
# ==========================================
plt.figure(figsize=(8, 5))
sns.violinplot(data=df_all, x="Режим", y="PERCLOS", palette=["#d62728", "#2ca02c"], inner="quartile")
plt.title("Розподіл показника зорової втоми (PERCLOS)")
plt.ylabel("PERCLOS (%)")
plt.tight_layout()
plt.savefig(out_dir / "pro_perclos_distribution.png", dpi=300)
plt.close()

# ==========================================
# ГРАФІК 3: Розподіл робочих зон (Складена діаграма)
# ==========================================
zone_counts = df_all.groupby(['Режим', 'Zone']).size().unstack(fill_value=0)
# Переводимо у відсотки для чесного порівняння
zone_pct = zone_counts.div(zone_counts.sum(axis=1), axis=0) * 100

zone_pct.plot(kind='bar', stacked=True, figsize=(9, 5), colormap='viridis', alpha=0.8)
plt.title("Розподіл робочих поз (відсоток часу)")
plt.xlabel("")
plt.ylabel("Відсоток від загального часу (%)")
plt.xticks(rotation=0)
plt.legend(title="Зона погляду", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(out_dir / "pro_zones_stacked.png", dpi=300)
plt.close()

print(f"Готово! Круті наукові графіки збережено у папку: {out_dir}")