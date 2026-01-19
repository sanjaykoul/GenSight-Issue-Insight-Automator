
# -*- coding: utf-8 -*-
# src/visualizer.py
"""
Modern, per-month charts for GenSight-Issue-Insight-Automator.

Highlights
----------
- All charts are strictly per-month (month_label)
- Clean aesthetics; no seaborn deprecation warnings
- Value labels on bars
- Rolling average line on daily trend
- Weekday trend chart
- Pareto chart for issue types (bar + cumulative line)

Output
------
Images saved under: reports/<MONTH>/charts/
"""

import os
from typing import Dict, Optional, List
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use("seaborn-v0_8-whitegrid")  # stable seaborn style through matplotlib


# ----------------------------- #
#         PATH HELPERS          #
# ----------------------------- #

def ensure_folder(month_label: str) -> str:
    folder = f"reports/{month_label}/charts"
    os.makedirs(folder, exist_ok=True)
    return folder


# ----------------------------- #
#       STYLE / UTILITIES       #
# ----------------------------- #

def _colors_main() -> List[str]:
    """Pleasant, modern palette (color‑blind friendly leaning)."""
    return [
        "#4C78A8",  # blue
        "#F58518",  # orange
        "#54A24B",  # green
        "#E45756",  # red
        "#72B7B2",  # teal
        "#B279A2",  # purple
        "#FF9DA6",  # pink
        "#9C755F",  # brown
        "#E2CF5B",  # yellow
    ]


def _annotate_bars(ax, fmt="{:,.0f}", fontsize=10, offset=0.01):
    """Add value labels above bars (or to the right for horizontal bars)."""
    for p in ax.patches:
        if p.get_width() == 0 and p.get_height() == 0:
            continue
        if p.get_width() > p.get_height():
            # horizontal bar
            x = p.get_x() + p.get_width()
            y = p.get_y() + p.get_height() / 2
            ax.text(x + ax.get_xlim()[1] * offset, y, fmt.format(p.get_width()),
                    va="center", ha="left", fontsize=fontsize)
        else:
            # vertical bar
            x = p.get_x() + p.get_width() / 2
            y = p.get_y() + p.get_height()
            ax.text(x, y + ax.get_ylim()[1] * offset, fmt.format(p.get_height()),
                    va="bottom", ha="center", fontsize=fontsize)


def _subset_month_df(summary: Dict, month_label: str) -> pd.DataFrame:
    df = summary.get("raw")
    if df is None or df.empty:
        return pd.DataFrame()
    return df[df["month_label"] == month_label].copy()


# ----------------------------- #
#            CHARTS             #
# ----------------------------- #

def plot_issue_distribution(summary: Dict, month_label: str) -> Optional[str]:
    """
    Per‑month issue-type distribution (vertical bar).
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty:
        return None

    # Ensure 'issue_type'
    if "issue_type" not in sub.columns:
        sub = sub.copy()
        sub["issue_type"] = "Other"

    counts = sub["issue_type"].value_counts()
    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = _colors_main()
    bars = ax.bar(counts.index, counts.values, color=colors[: len(counts)])
    ax.set_title(f"Issue Type Distribution — {month_label}")
    ax.set_xlabel("Issue Type")
    ax.set_ylabel("Count")
    ax.set_ylim(0, max(counts.values) * 1.15)
    ax.set_xticklabels(counts.index, rotation=15, ha="right")

    _annotate_bars(ax)

    path = f"{folder}/issue_distribution.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_engineer_workload(summary: Dict, month_label: str, top_n: int = 10) -> Optional[str]:
    """
    Top‑N engineers by volume (horizontal bar) for a single month.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty:
        return None

    counts = sub["engineer"].astype(str).str.strip().value_counts().head(top_n)
    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = _colors_main()
    y = np.arange(len(counts.index))
    bars = ax.barh(y, counts.values, color=colors[: len(counts)])
    ax.set_yticks(y)
    ax.set_yticklabels(counts.index)
    ax.invert_yaxis()  # largest on top
    ax.set_title(f"Top {top_n} Engineer Workload — {month_label}")
    ax.set_xlabel("Issues")
    ax.set_xlim(0, max(counts.values) * 1.15)

    # annotate values to the right
    for i, v in enumerate(counts.values):
        ax.text(v + (ax.get_xlim()[1] * 0.01), i, f"{v:,}", va="center")

    path = f"{folder}/engineer_workload.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_daily_trend(df: pd.DataFrame, month_label: str) -> Optional[str]:
    """
    Daily issues (bar) + 3‑day rolling average (line) for a specific month.
    """
    folder = ensure_folder(month_label)
    sub = df[df["month_label"] == month_label].copy()
    if sub.empty or "date" not in sub.columns:
        return None

    series = sub.groupby("date").size().sort_index()
    rolling = series.rolling(window=min(3, len(series)), min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.bar(series.index.astype(str), series.values, color="#4C78A8", alpha=0.85, label="Daily count")
    ax.plot(series.index.astype(str), rolling.values, color="#E45756", linewidth=2.0, marker="o", label="3‑day avg")

    ax.set_title(f"Daily Issue Trend — {month_label}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")
    ax.set_ylim(0, max(series.values) * 1.25)
    ax.legend(loc="upper left")
    plt.xticks(rotation=45, ha="right")

    path = f"{folder}/daily_trend.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_status_breakdown(summary: Dict, month_label: str) -> Optional[str]:
    """
    Open vs Closed pie for a single month.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty or "status" not in sub.columns:
        return None

    counts = sub["status"].astype(str).str.strip().str.title().value_counts()
    if counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    colors = ["#4C78A8", "#54A24B", "#F58518", "#E45756"]
    ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%", startangle=90, colors=colors[: len(counts)])
    ax.set_title(f"Status Breakdown — {month_label}")

    path = f"{folder}/status_breakdown.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_weekday_trend(summary: Dict, month_label: str) -> Optional[str]:
    """
    Issues by weekday (Mon...Sun) — helps spot support load patterns.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty or "date" not in sub.columns:
        return None

    dd = pd.to_datetime(sub["date"])
    weekday = dd.dt.weekday  # Monday=0
    counts = weekday.value_counts().reindex(range(7), fill_value=0)

    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bars = ax.bar(labels, counts.values, color="#72B7B2")
    ax.set_title(f"Weekday Trend — {month_label}")
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Issues")
    ax.set_ylim(0, max(counts.values) * 1.25)
    _annotate_bars(ax)

    path = f"{folder}/weekday_trend.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_pareto_issue_types(summary: Dict, month_label: str) -> Optional[str]:
    """
    Pareto chart: sorted issue types (bars) + cumulative percentage (line).
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty:
        return None

    if "issue_type" not in sub.columns:
        sub = sub.copy()
        sub["issue_type"] = "Other"

    counts = sub["issue_type"].value_counts()
    if counts.empty:
        return None

    total = counts.sum()
    cum = counts.cumsum() / total * 100.0

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    color_bar = "#4C78A8"
    color_line = "#E45756"
    ax.bar(counts.index, counts.values, color=color_bar, alpha=0.9)
    ax2 = ax.twinx()
    ax2.plot(counts.index, cum.values, color=color_line, marker="o", linewidth=2)

    ax.set_title(f"Issue Types Pareto — {month_label}")
    ax.set_xlabel("Issue Type")
    ax.set_ylabel("Count")
    ax2.set_ylabel("Cumulative %")
    ax.set_xticklabels(counts.index, rotation=15, ha="right")
    ax.set_ylim(0, max(counts.values) * 1.2)
    ax2.set_ylim(0, 110)
    ax2.axhline(80, color="#9C755F", linestyle="--", linewidth=1)  # 80/20 reference

    path = f"{folder}/issue_pareto.png"
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path