from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

STATE_LABELS = {
    "NORMAL": "НОРМА",
    "WARNING": "ПОПЕРЕДЖЕННЯ",
    "CRITICAL": "КРИТИЧНО",
}

BASELINE_FILES = [
    "logs/baseline_1(2026-05-06_21.36.45).csv",
    "logs/baseline_2(2026-05-07_19.21.06).csv",
    "logs/baseline_3(2026-05-08_15.34.47).csv",
    "logs/baseline_4(2026-05-08_23.05.03).csv",
]
ASSISTANT_FILES = [
    "logs/assistant_1(2026-05-07_23.09.59).csv",
    "logs/assistant_2(2026-05-08_18.33.11).csv",
    "logs/assistant_3(2026-05-08_22.21.20).csv",
]


def load_session(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    df["TimestampISO"] = pd.to_datetime(df["TimestampISO"], errors="coerce")
    df = df.sort_values("TimestampISO").reset_index(drop=True)
    for col in [
        "Blinks",
        "Distractions",
        "PERCLOS",
        "Focus_Score",
        "BPM",
        "Accumulated_Inattention_Sec",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def summarize_session(df: pd.DataFrame) -> dict[str, float | dict[str, float]]:
    if df.empty:
        return {}

    duration = len(df)
    blinks = int(df["Blinks"].iloc[-1] - df["Blinks"].iloc[0]) if "Blinks" in df.columns else 0
    distractions = int(df["Distractions"].iloc[-1] - df["Distractions"].iloc[0]) if "Distractions" in df.columns else 0
    avg_focus = float(df["Focus_Score"].mean()) if "Focus_Score" in df.columns else 0.0
    avg_perclos = float(df["PERCLOS"].mean()) if "PERCLOS" in df.columns else 0.0
    avg_bpm = float(df["BPM"].mean()) if "BPM" in df.columns else 0.0
    blink_rate = blinks / duration * 60 if duration > 0 else 0.0
    attention_pct = (df["Attention_State"].value_counts(normalize=True) * 100).round(1).to_dict() if "Attention_State" in df.columns else {}
    zone_pct = (df["Zone"].value_counts(normalize=True) * 100).round(1).to_dict() if "Zone" in df.columns else {}

    return {
        "duration_s": duration,
        "total_blinks": blinks,
        "blink_rate_per_min": blink_rate,
        "total_distractions": distractions,
        "avg_focus_score": avg_focus,
        "avg_perclos": avg_perclos,
        "avg_bpm": avg_bpm,
        "attention_pct": attention_pct,
        "zone_pct": zone_pct,
    }


def aggregate_group(paths: list[Path]) -> dict[str, float | dict[str, float]]:
    summaries = [summarize_session(load_session(path)) for path in paths]
    if not summaries:
        return {}

    return {
        "avg_focus_score": float(pd.Series([s["avg_focus_score"] for s in summaries]).mean()),
        "avg_perclos": float(pd.Series([s["avg_perclos"] for s in summaries]).mean()),
        "avg_bpm": float(pd.Series([s["avg_bpm"] for s in summaries]).mean()),
        "avg_blink_rate_per_min": float(pd.Series([s["blink_rate_per_min"] for s in summaries]).mean()),
        "avg_distractions": float(pd.Series([s["total_distractions"] for s in summaries]).mean()),
        "avg_duration_s": float(pd.Series([s["duration_s"] for s in summaries]).mean()),
        "normal_pct": float(pd.Series([s["attention_pct"].get("NORMAL", 0.0) for s in summaries]).mean()),
        "warning_pct": float(pd.Series([s["attention_pct"].get("WARNING", 0.0) for s in summaries]).mean()),
        "critical_pct": float(pd.Series([s["attention_pct"].get("CRITICAL", 0.0) for s in summaries]).mean()),
    }


def remove_outliers(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    clean = values.copy()
    median = np.nanmedian(clean)
    mad = np.nanmedian(np.abs(clean - median))
    if mad == 0:
        mad = np.nanstd(clean)
    threshold = median + 3.0 * mad
    if np.isnan(threshold) or threshold <= 0:
        return clean
    outliers = clean > threshold
    if not np.any(outliers):
        return clean
    clean[outliers] = np.nan
    idx = np.arange(len(clean))
    valid = ~np.isnan(clean)
    if not np.any(valid):
        return np.full_like(clean, median)
    clean[np.isnan(clean)] = np.interp(idx[np.isnan(clean)], idx[valid], clean[valid])
    return clean


def normalize_series(df: pd.DataFrame, column: str, bins: int = 120) -> np.ndarray:
    values = df[column].ffill().fillna(0).to_numpy()
    if values.size == 0:
        return np.full(bins, np.nan)
    if column == "PERCLOS":
        values = remove_outliers(values)
    x_old = np.linspace(0.0, 1.0, len(values))
    x_new = np.linspace(0.0, 1.0, bins)
    return np.interp(x_new, x_old, values)


def group_average_curve(paths: list[Path], column: str, bins: int = 120) -> np.ndarray:
    curves = []
    for path in paths:
        df = load_session(path)
        if column in df.columns:
            curves.append(normalize_series(df, column, bins))
    if not curves:
        return np.full(bins, np.nan)
    return np.nanmean(np.vstack(curves), axis=0)


def build_group_comparison_plots(baseline: dict[str, float], assistant: dict[str, float], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = ["Baseline", "Assistant"]

    def save_bar_plot(values: list[float], title: str, ylabel: str, filename: str, fmt: str = "{:.2f}"):
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, values, color=["#d62728", "#2ca02c"])
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        ax.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(values), fmt.format(value), ha="center", va="bottom", fontweight="bold", fontsize=12)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=150)
        plt.close(fig)

    save_bar_plot(
        [baseline["avg_focus_score"], assistant["avg_focus_score"]],
        "Середній Focus Score",
        "Focus Score",
        "comparison_focus_score.png",
        "{:.3f}",
    )
    save_bar_plot(
        [baseline["avg_perclos"], assistant["avg_perclos"]],
        "Середній PERCLOS",
        "PERCLOS — відсоток закриття повік (%)",
        "comparison_perclos.png",
    )
    save_bar_plot(
        [baseline["avg_blink_rate_per_min"], assistant["avg_blink_rate_per_min"]],
        "Середній Blink Rate",
        "Моргання / хв",
        "comparison_blink_rate.png",
    )
    save_bar_plot(
        [baseline["normal_pct"], assistant["normal_pct"]],
        "Час у нормальному стані уваги",
        "% часу",
        "comparison_normal_pct.png",
    )
    save_bar_plot(
        [baseline["critical_pct"], assistant["critical_pct"]],
        "Час у критичному стані уваги",
        "% часу",
        "comparison_critical_pct.png",
    )

    states = ["normal_pct", "warning_pct", "critical_pct"]
    baseline_values = [baseline[state] for state in states]
    assistant_values = [assistant[state] for state in states]
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(states))
    width = 0.35
    ax.bar(x - width / 2, baseline_values, width, label="Baseline", color="#d62728")
    ax.bar(x + width / 2, assistant_values, width, label="Assistant", color="#2ca02c")
    ax.set_xticks(x)
    ax.set_xticklabels(
    [
        STATE_LABELS["NORMAL"],
        STATE_LABELS["WARNING"],
        STATE_LABELS["CRITICAL"],
    ],
    fontsize=12,
)
    ax.set_ylabel("Частка часу у стані уваги (% від тривалості сесії)", fontsize=14)
    ax.set_title("Порівняння частки часу у станах уваги", fontsize=16, fontweight="bold")
    ax.legend(fontsize=12)
    ax.tick_params(axis="both", labelsize=12)
    ax.grid(axis="y", alpha=0.25)
    for i, (b, a) in enumerate(zip(baseline_values, assistant_values)):
        ax.text(i - width / 2, b + 0.5, f"{b:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)
        ax.text(i + width / 2, a + 0.5, f"{a:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)
    fig.text(
        0.5,
        0.02,
        "Відсоток часу сесії, проведений у відповідному стані уваги: NORMAL = нормальна увага, WARNING = попередження, CRITICAL = критичне зниження.",
        ha="center",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(output_dir / "comparison_attention_states.png", dpi=150)
    plt.close(fig)


def build_time_series_comparison_plots(baseline_paths: list[Path], assistant_paths: list[Path], output_dir: Path, avg_duration_min: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = [
        ("PERCLOS", "PERCLOS (%)", "comparison_time_perclos.png", 0, None),
        ("Focus_Score", "Focus Score", "comparison_time_focus_score.png", 0, 1),
        ("BPM", "Blinks per Minute (BPM)", "comparison_time_bpm.png", 0, None),
        ("Accumulated_Inattention_Sec", "Accumulated Inattention (s)", "comparison_time_inattention.png", 0, None),
    ]
    x = np.linspace(0, avg_duration_min, 120)
    for column, ylabel, filename, ymin, ymax in metrics:
        baseline_curve = group_average_curve(baseline_paths, column)
        assistant_curve = group_average_curve(assistant_paths, column)
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(x, baseline_curve, label="Baseline", color="#d62728", linewidth=3)
        ax.plot(x, assistant_curve, label="Assistant", color="#2ca02c", linewidth=3)
        ax.set_title(f"{ylabel} по часу сесії", fontsize=18, fontweight="bold")
        ax.set_xlabel("Час (хв)", fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        if ymin is not None and ymax is not None:
            ax.set_ylim(ymin, ymax)
        ax.legend(fontsize=12)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=150)
        plt.close(fig)


def shade_attention_states(ax: plt.Axes, df: pd.DataFrame) -> None:
    if "Attention_State" not in df.columns or df.empty:
        return

    state_colors = {
        "WARNING": "#ffcc00",
        "CRITICAL": "#ff6666",
    }
    current_state = None
    start_time = None
    for idx, row in df.iterrows():
        state = row["Attention_State"]
        if state not in state_colors:
            if current_state in state_colors:
                ax.axvspan(start_time, df.loc[idx - 1, "TimestampISO"], color=state_colors[current_state], alpha=0.2)
                current_state = None
                start_time = None
            continue

        if state != current_state:
            if current_state in state_colors and start_time is not None:
                ax.axvspan(start_time, df.loc[idx - 1, "TimestampISO"], color=state_colors[current_state], alpha=0.2)
            current_state = state
            start_time = row["TimestampISO"]

    if current_state in state_colors and start_time is not None:
        ax.axvspan(start_time, df["TimestampISO"].iloc[-1], color=state_colors[current_state], alpha=0.2)


def build_attention_state_histogram(baseline_paths: list[Path], assistant_paths: list[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def group_attention_percent(paths: list[Path]) -> dict[str, float]:
        values = []
        for path in paths:
            df = load_session(path)
            if "Attention_State" in df.columns:
                values.append(df["Attention_State"].value_counts(normalize=True).mul(100).to_dict())
        if not values:
            return {"NORMAL": 0.0, "WARNING": 0.0, "CRITICAL": 0.0}
        return {
            state: float(pd.Series([v.get(state, 0.0) for v in values]).mean())
            for state in ["NORMAL", "WARNING", "CRITICAL"]
        }

    baseline_pct = group_attention_percent(baseline_paths)
    assistant_pct = group_attention_percent(assistant_paths)
    states = ["NORMAL", "WARNING", "CRITICAL"]
    for state in states:
        baseline_val = baseline_pct[state]
        assistant_val = assistant_pct[state]
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(['Baseline', 'Assistant'], [baseline_val, assistant_val], color=['#d62728', '#2ca02c'])
        ax.set_title(
        f"Частка часу у стані {STATE_LABELS[state]}",
        fontsize=16,
        fontweight='bold'
)
        ax.set_ylabel("Частка часу у стані (%)", fontsize=14)
        ax.tick_params(axis='both', labelsize=12)
        
        # Динамічний масштаб для кращої видимості
        max_val = max(baseline_val, assistant_val)
        if state == "NORMAL":
            ax.set_ylim(0, 105)
        elif state == "WARNING":
            ax.set_ylim(0, max(3, max_val * 1.5))
        elif state == "CRITICAL":
            ax.set_ylim(0, max(10, max_val * 1.5))
        
        ax.grid(axis="y", alpha=0.25)
        for i, v in enumerate([baseline_val, assistant_val]):
            if state == "NORMAL" and v > 80:
                ax.text(i, v - 1, f"{v:.1f}%", ha="center", va="top", fontweight="bold", color="white", fontsize=12)
            else:
                ax.text(i, v + (max_val * 0.05), f"{v:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)
        fig.tight_layout()
        fig.savefig(output_dir / f"attention_state_{state.lower()}.png", dpi=150)
        plt.close(fig)


def build_accumulated_inattention_plots(baseline_paths: list[Path], assistant_paths: list[Path], output_dir: Path, avg_duration_min: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def session_accumulation(path: Path) -> tuple[str, pd.Series, pd.Series]:
        df = load_session(path)
        if "Accumulated_Inattention_Sec" not in df.columns:
            return path.stem, pd.Series(dtype=float), pd.Series(dtype=float)
        series = df["Accumulated_Inattention_Sec"].ffill().fillna(0)
        time_axis = (df["TimestampISO"] - df["TimestampISO"].iloc[0]).dt.total_seconds() / 60  # minutes
        return path.stem, series, time_axis

    baseline_data = [session_accumulation(path) for path in baseline_paths]
    assistant_data = [session_accumulation(path) for path in assistant_paths]

    fig, ax = plt.subplots(figsize=(12, 6))
    for name, series, time_ax in baseline_data:
        if not series.empty:
            ax.plot(time_ax, series, color="#d62728", linewidth=3, label="Baseline" if name == baseline_data[0][0] else "")
    for name, series, time_ax in assistant_data:
        if not series.empty:
            ax.plot(time_ax, series, color="#2ca02c", linewidth=3, label="Assistant" if name == assistant_data[0][0] else "")
    ax.set_title("Accumulated Inattention — наростаючий (Baseline vs Assistant)", fontsize=16, fontweight="bold")
    ax.set_xlabel(f"Час (хв) [середня тривалість сесії: {avg_duration_min:.1f} хв]", fontsize=14)
    ax.set_ylabel("Accumulated Inattention (с)", fontsize=14)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(fontsize=12)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "accumulated_inattention_time_series.png", dpi=150)
    plt.close(fig)

    final_values = []
    for name, series, _ in baseline_data:
        if not series.empty:
            final_values.append((f"B-{name}", series.iloc[-1]))
    for name, series, _ in assistant_data:
        if not series.empty:
            final_values.append((f"A-{name}", series.iloc[-1]))

    names = [item[0] for item in final_values]
    values = [item[1] for item in final_values]
    colors = ["#d62728"] * len(baseline_data) + ["#2ca02c"] * len(assistant_data)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(names, values, color=colors)
    ax.set_title("Порівняння кінцевого значення Accumulated Inattention")
    ax.set_ylabel("Accumulated Inattention (с)")
    ax.set_xticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.25)
    mean_baseline = np.mean([v for v in values[: len(baseline_data)]]) if baseline_data else 0.0
    mean_assistant = np.mean([v for v in values[len(baseline_data):]]) if assistant_data else 0.0
    ax.axhline(mean_baseline, color="#aa0000", linestyle="--", linewidth=1, label=f"Baseline mean {mean_baseline:.1f}s")
    ax.axhline(mean_assistant, color="#008800", linestyle="--", linewidth=1, label=f"Assistant mean {mean_assistant:.1f}s")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "accumulated_inattention_summary.png", dpi=150)
    plt.close(fig)


def build_perclos_distribution_plots(baseline_paths: list[Path], assistant_paths: list[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_values = pd.concat([load_session(path)["PERCLOS"] for path in baseline_paths], ignore_index=True).dropna()
    assistant_values = pd.concat([load_session(path)["PERCLOS"] for path in assistant_paths], ignore_index=True).dropna()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(baseline_values, bins=20, alpha=0.7, label='Baseline', color='#d62728')
    ax.hist(assistant_values, bins=20, alpha=0.7, label='Assistant', color='#2ca02c')
    ax.legend(fontsize=12)
    ax.set_title("Розподіл значень PERCLOS", fontsize=16, fontweight='bold')
    ax.set_xlabel("PERCLOS — відсоток закриття повік (%)", fontsize=14)
    ax.set_ylabel("Кількість спостережень", fontsize=14)
    ax.tick_params(axis='both', labelsize=12)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "perclos_distribution.png", dpi=150)
    plt.close(fig)


def build_session_line_plots(paths: list[Path], label: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for session_path in paths:
        df = load_session(session_path)
        session_name = session_path.stem.replace("(", "_").replace(")", "")
        fig, ax = plt.subplots(figsize=(12, 5))
        if "Attention_State" in df.columns:
            shade_attention_states(ax, df)
        ax.plot(df["TimestampISO"], df["Focus_Score"], label="Focus Score", color="#1f77b4", linewidth=3)
        if "PERCLOS" in df.columns:
            ax2 = ax.twinx()
            ax2.plot(df["TimestampISO"], df["PERCLOS"], label="PERCLOS", color="#d62728", linewidth=3)
            ax2.set_ylabel("PERCLOS — відсоток закриття повік (%)", color="#d62728", fontsize=14)
            ax2.tick_params(axis="y", labelcolor="#d62728", labelsize=12)
        ax.set_title(f"Focus Score — {label} — {session_name}", fontsize=16, fontweight="bold")
        ax.set_ylabel("Focus Score", fontsize=14)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Час", fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        ax.grid(alpha=0.25)
        handles, labels = ax.get_legend_handles_labels()
        if "PERCLOS" in df.columns:
            handles2, labels2 = ax2.get_legend_handles_labels()
            handles += handles2
            labels += labels2
        if handles:
            ax.legend(handles, labels, loc="upper right")
        fig.tight_layout()
        fig.savefig(output_dir / f"{session_name}_focus_score.png", dpi=150)
        plt.close(fig)


def main() -> None:
    output_dir = Path("effectiveness_graphs")
    baseline_paths = [Path(p) for p in BASELINE_FILES]
    assistant_paths = [Path(p) for p in ASSISTANT_FILES]

    baseline_group = aggregate_group(baseline_paths)
    assistant_group = aggregate_group(assistant_paths)
    avg_duration_min = assistant_group["avg_duration_s"] / 60

    build_group_comparison_plots(baseline_group, assistant_group, output_dir)
    build_time_series_comparison_plots(baseline_paths, assistant_paths, output_dir, avg_duration_min)
    build_accumulated_inattention_plots(baseline_paths, assistant_paths, output_dir, avg_duration_min)
    build_attention_state_histogram(baseline_paths, assistant_paths, output_dir)
    build_perclos_distribution_plots(baseline_paths, assistant_paths, output_dir)
    build_session_line_plots(baseline_paths, "Baseline", output_dir)
    build_session_line_plots(assistant_paths, "Assistant", output_dir)

    print("Графіки побудовано у папці:", output_dir.resolve())


if __name__ == "__main__":
    main()
