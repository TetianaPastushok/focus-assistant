from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None


@dataclass
class SessionSummary:
    duration_minutes: float
    avg_bpm: float
    avg_perclos: float
    avg_focus_score: float
    max_distractions: int
    total_blinks: int


@dataclass
class ExperimentComparison:
    baseline_sessions: int
    assistant_sessions: int
    baseline_avg_focus_score: float
    assistant_avg_focus_score: float
    focus_score_improvement: float
    baseline_avg_perclos: float
    assistant_avg_perclos: float
    perclos_improvement: float
    baseline_avg_bpm: float
    assistant_avg_bpm: float
    bpm_change: float
    baseline_total_distractions: int
    assistant_total_distractions: int
    distractions_reduction: float


def load_session(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Файл не знайдено: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8")
    required = {
        "TimestampISO",
        "Blinks",
        "BPM",
        "PERCLOS",
        "Focus_Duration_Sec",
        "Distractions",
        "Focus_Score",
        "Zone",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"У CSV відсутні колонки: {sorted(missing)}")

    df["TimestampISO"] = pd.to_datetime(df["TimestampISO"], errors="coerce")
    df = df.dropna(subset=["TimestampISO"]).sort_values("TimestampISO").reset_index(drop=True)
    return df


def summarize_session(df: pd.DataFrame) -> SessionSummary:
    if df.empty:
        return SessionSummary(0.0, 0.0, 0.0, 0.0, 0, 0)

    duration_sec = (df["TimestampISO"].iloc[-1] - df["TimestampISO"].iloc[0]).total_seconds()
    return SessionSummary(
        duration_minutes=round(duration_sec / 60.0, 2),
        avg_bpm=round(float(df["BPM"].mean()), 2),
        avg_perclos=round(float(df["PERCLOS"].mean()), 2),
        avg_focus_score=round(float(df["Focus_Score"].mean()), 3),
        max_distractions=int(df["Distractions"].max()),
        total_blinks=int(df["Blinks"].max()),
    )


def compare_experiments(baseline_csvs: list[Path], assistant_csvs: list[Path]) -> ExperimentComparison:
    """Порівнює експерименти baseline vs assistant на основі списків CSV файлів."""
    def aggregate_summaries(csv_paths: list[Path]) -> tuple[float, float, float, int]:
        summaries = [summarize_session(load_session(csv)) for csv in csv_paths]
        avg_focus = sum(s.avg_focus_score for s in summaries) / len(summaries)
        avg_perclos = sum(s.avg_perclos for s in summaries) / len(summaries)
        avg_bpm = sum(s.avg_bpm for s in summaries) / len(summaries)
        total_distractions = sum(s.max_distractions for s in summaries)
        return avg_focus, avg_perclos, avg_bpm, total_distractions

    baseline_avg_focus, baseline_avg_perclos, baseline_avg_bpm, baseline_distr = aggregate_summaries(baseline_csvs)
    assistant_avg_focus, assistant_avg_perclos, assistant_avg_bpm, assistant_distr = aggregate_summaries(assistant_csvs)

    return ExperimentComparison(
        baseline_sessions=len(baseline_csvs),
        assistant_sessions=len(assistant_csvs),
        baseline_avg_focus_score=round(baseline_avg_focus, 3),
        assistant_avg_focus_score=round(assistant_avg_focus, 3),
        focus_score_improvement=round(assistant_avg_focus - baseline_avg_focus, 3),
        baseline_avg_perclos=round(baseline_avg_perclos, 2),
        assistant_avg_perclos=round(assistant_avg_perclos, 2),
        perclos_improvement=round(baseline_avg_perclos - assistant_avg_perclos, 2),
        baseline_avg_bpm=round(baseline_avg_bpm, 2),
        assistant_avg_bpm=round(assistant_avg_bpm, 2),
        bpm_change=round(assistant_avg_bpm - baseline_avg_bpm, 2),
        baseline_total_distractions=baseline_distr,
        assistant_total_distractions=assistant_distr,
        distractions_reduction=round((baseline_distr - assistant_distr) / max(baseline_distr, 1) * 100, 1),
    )


def save_summary(summary: SessionSummary, output_txt: Path) -> None:
    lines = [
        "Звіт сесії моніторингу зосередженості",
        f"Тривалість сесії (хв): {summary.duration_minutes}",
        f"Середній BPM: {summary.avg_bpm}",
        f"Середній PERCLOS (%): {summary.avg_perclos}",
        f"Середній Focus Score: {summary.avg_focus_score}",
        f"Максимум відволікань: {summary.max_distractions}",
        f"Загальна кількість кліпань: {summary.total_blinks}",
    ]
    output_txt.write_text("\n".join(lines), encoding="utf-8")


def save_comparison(comparison: ExperimentComparison, output_txt: Path) -> None:
    lines = [
        "Звіт порівняння експериментів: Baseline vs Assistant",
        f"Кількість сесій Baseline: {comparison.baseline_sessions}",
        f"Кількість сесій Assistant: {comparison.assistant_sessions}",
        "",
        "Focus Score:",
        f"  Baseline середній: {comparison.baseline_avg_focus_score}",
        f"  Assistant середній: {comparison.assistant_avg_focus_score}",
        f"  Покращення: {comparison.focus_score_improvement} ({'+' if comparison.focus_score_improvement > 0 else ''}{comparison.focus_score_improvement})",
        "",
        "PERCLOS (%):",
        f"  Baseline середній: {comparison.baseline_avg_perclos}",
        f"  Assistant середній: {comparison.assistant_avg_perclos}",
        f"  Покращення: {comparison.perclos_improvement} ({'+' if comparison.perclos_improvement > 0 else ''}{comparison.perclos_improvement})",
        "",
        "BPM:",
        f"  Baseline середній: {comparison.baseline_avg_bpm}",
        f"  Assistant середній: {comparison.assistant_avg_bpm}",
        f"  Зміна: {comparison.bpm_change} ({'+' if comparison.bpm_change > 0 else ''}{comparison.bpm_change})",
        "",
        "Відволікання:",
        f"  Baseline загалом: {comparison.baseline_total_distractions}",
        f"  Assistant загалом: {comparison.assistant_total_distractions}",
        f"  Зменшення: {comparison.distractions_reduction}%",
    ]
    output_txt.write_text("\n".join(lines), encoding="utf-8")


def build_plots(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    if plt is None:
        raise ImportError("Для побудови графіків встановіть matplotlib: pip install matplotlib")

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    # Графік 1: BPM і PERCLOS у часі
    fig, ax1 = plt.subplots(figsize=(11, 5))
    ax1.plot(df["TimestampISO"], df["BPM"], color="#2ca02c", label="BPM")
    ax1.set_ylabel("BPM", color="#2ca02c")
    ax1.tick_params(axis="y", labelcolor="#2ca02c")

    ax2 = ax1.twinx()
    ax2.plot(df["TimestampISO"], df["PERCLOS"], color="#d62728", label="PERCLOS")
    ax2.set_ylabel("PERCLOS (%)", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")

    ax1.set_title("Динаміка BPM та PERCLOS")
    ax1.set_xlabel("Час")
    ax1.grid(alpha=0.25)

    out1 = output_dir / "bpm_perclos.png"
    fig.tight_layout()
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    saved.append(out1)

    # Графік 2: Focus Score у часі
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["TimestampISO"], df["Focus_Score"], color="#1f77b4", linewidth=2)
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Коефіцієнт фокусу у часі")
    ax.set_xlabel("Час")
    ax.set_ylabel("Focus Score")
    ax.grid(alpha=0.25)

    out2 = output_dir / "focus_score.png"
    fig.tight_layout()
    fig.savefig(out2, dpi=150)
    plt.close(fig)
    saved.append(out2)

    # Графік 3: Розподіл зон
    zone_counts = df["Zone"].value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(zone_counts.index, zone_counts.values, color="#17becf")
    ax.set_title("Розподіл станів (Zone)")
    ax.set_xlabel("Zone")
    ax.set_ylabel("Кількість секунд")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=20)

    out3 = output_dir / "zones_distribution.png"
    fig.tight_layout()
    fig.savefig(out3, dpi=150)
    plt.close(fig)
    saved.append(out3)

    return saved


def build_comparison_plots(comparison: ExperimentComparison, output_dir: Path) -> list[Path]:
    if plt is None:
        raise ImportError("Для побудови графіків встановіть matplotlib: pip install matplotlib")

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    # Графік порівняння Focus Score
    fig, ax = plt.subplots(figsize=(8, 5))
    modes = ['Baseline', 'Assistant']
    scores = [comparison.baseline_avg_focus_score, comparison.assistant_avg_focus_score]
    ax.bar(modes, scores, color=['#d62728', '#2ca02c'])
    ax.set_title("Порівняння середнього Focus Score")
    ax.set_ylabel("Focus Score")
    ax.set_ylim(0, 1.05)
    for i, v in enumerate(scores):
        ax.text(i, v + 0.01, f"{v}", ha='center', fontweight='bold')
    ax.grid(axis='y', alpha=0.25)

    out1 = output_dir / "focus_score_comparison.png"
    fig.tight_layout()
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    saved.append(out1)

    # Графік порівняння PERCLOS
    fig, ax = plt.subplots(figsize=(8, 5))
    perclos_vals = [comparison.baseline_avg_perclos, comparison.assistant_avg_perclos]
    ax.bar(modes, perclos_vals, color=['#d62728', '#2ca02c'])
    ax.set_title("Порівняння середнього PERCLOS")
    ax.set_ylabel("PERCLOS (%)")
    for i, v in enumerate(perclos_vals):
        ax.text(i, v + 0.5, f"{v}%", ha='center', fontweight='bold')
    ax.grid(axis='y', alpha=0.25)

    out2 = output_dir / "perclos_comparison.png"
    fig.tight_layout()
    fig.savefig(out2, dpi=150)
    plt.close(fig)
    saved.append(out2)

    # Графік порівняння BPM
    fig, ax = plt.subplots(figsize=(8, 5))
    bpm_vals = [comparison.baseline_avg_bpm, comparison.assistant_avg_bpm]
    ax.bar(modes, bpm_vals, color=['#d62728', '#2ca02c'])
    ax.set_title("Порівняння середнього BPM")
    ax.set_ylabel("BPM")
    for i, v in enumerate(bpm_vals):
        ax.text(i, v + 0.5, f"{v}", ha='center', fontweight='bold')
    ax.grid(axis='y', alpha=0.25)

    out3 = output_dir / "bpm_comparison.png"
    fig.tight_layout()
    fig.savefig(out3, dpi=150)
    plt.close(fig)
    saved.append(out3)

    return saved


def run_analysis(csv_file: str, output_dir: str) -> None:
    csv_path = Path(csv_file)
    out_dir = Path(output_dir)

    df = load_session(csv_path)
    summary = summarize_session(df)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "session_summary.txt"
    save_summary(summary, summary_path)

    print(f"Збережено звіт: {summary_path}")
    print(f"Тривалість: {summary.duration_minutes} хв")
    print(f"Середній Focus Score: {summary.avg_focus_score}")

    if plt is None:
        print("matplotlib не встановлено, графіки не побудовано.")
        return

    plots = build_plots(df, out_dir)
    for plot_path in plots:
        print(f"Збережено графік: {plot_path}")


def run_comparison_analysis(baseline_csvs: list[str], assistant_csvs: list[str], output_dir: str) -> None:
    baseline_paths = [Path(csv) for csv in baseline_csvs]
    assistant_paths = [Path(csv) for csv in assistant_csvs]
    out_dir = Path(output_dir)

    comparison = compare_experiments(baseline_paths, assistant_paths)

    out_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = out_dir / "experiment_comparison.txt"
    save_comparison(comparison, comparison_path)

    print(f"Збережено звіт порівняння: {comparison_path}")
    print(f"Baseline сесій: {comparison.baseline_sessions}, Assistant сесій: {comparison.assistant_sessions}")
    print(f"Focus Score покращення: {comparison.focus_score_improvement}")
    print(f"PERCLOS покращення: {comparison.perclos_improvement}%")
    print(f"Відволікання зменшення: {comparison.distractions_reduction}%")

    if plt is None:
        print("matplotlib не встановлено, графіки не побудовано.")
        return

    plots = build_comparison_plots(comparison, out_dir)
    for plot_path in plots:
        print(f"Збережено графік порівняння: {plot_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Аналітика сесії KPI Фокус Асистента")
    parser.add_argument("--csv", default="session_log.csv", help="Шлях до session_log.csv (для одиночної сесії)")
    parser.add_argument("--out", default="analysis_output", help="Директорія для звіту і графіків")
    parser.add_argument("--baseline-csvs", nargs='*', help="Список CSV файлів для baseline експерименту")
    parser.add_argument("--assistant-csvs", nargs='*', help="Список CSV файлів для assistant експерименту")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.baseline_csvs and args.assistant_csvs:
        run_comparison_analysis(
            baseline_csvs=args.baseline_csvs,
            assistant_csvs=args.assistant_csvs,
            output_dir=args.out
        )
    else:
        run_analysis(csv_file=args.csv, output_dir=args.out)
