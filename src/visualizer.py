
# -*- coding: utf-8 -*-
# src/visualizer.py
"""
Visualization utilities for GenSight-Issue-Insight-Automator.
- Saves PNG charts in reports/<MONTH>/charts/
- All charts are computed strictly for the requested month_label
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

sns.set(style="whitegrid")


def ensure_folder(month_label: str) -> str:
    folder = f"reports/{month_label}/charts"
    os.makedirs(folder, exist_ok=True)
    return folder


def _subset_month_df(summary: dict, month_label: str) -> pd.DataFrame:
    """Return only the rows for the given month from summary['raw']."""
    df = summary.get("raw")
    if df is None or df.empty:
        return pd.DataFrame()
    return df[df["month_label"] == month_label].copy()


def plot_issue_distribution(summary: dict, month_label: str) -> str | None:
    """
    Bar chart for issue-type distribution for a single month.
    Fixes seaborn FutureWarning by using color= instead of palette= without hue.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty:
        return None

    # Ensure issue_type present (aggregator adds it; fallback if missing)
    if "issue_type" not in sub.columns:
        sub = sub.copy()
        sub["issue_type"] = "Other"

    counts = sub["issue_type"].value_counts()
    if counts.empty:
        return None

    plt.figure(figsize=(8, 5))
    counts.plot(kind="bar", color="#4C78A8")  # use a single color (no palette+hue)
    plt.title(f"Issue Type Distribution — {month_label}")
    plt.xlabel("Issue Type")
    plt.ylabel("Count")
    plt.xticks(rotation=20)
    plt.tight_layout()

    path = f"{folder}/issue_distribution.png"
    plt.savefig(path)
    plt.close()
    return path


def plot_engineer_workload(summary: dict, month_label: str, top_n: int = 10) -> str | None:
    """
    Bar chart for top-N engineers by volume for a single month.
    Uses a single color to avoid seaborn palette+hue warning.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty:
        return None

    counts = sub["engineer"].astype(str).str.strip().value_counts().head(top_n)
    if counts.empty:
        return None

    plt.figure(figsize=(9, 5))
    counts.plot(kind="bar", color="#59A14F")
    plt.title(f"Top {top_n} Engineer Workload — {month_label}")
    plt.xlabel("Engineer")
    plt.ylabel("Issues")
    plt.xticks(rotation=30)
    plt.tight_layout()

    path = f"{folder}/engineer_workload.png"
    plt.savefig(path)
    plt.close()
    return path


def plot_daily_trend(df, month_label: str) -> str | None:
    """
    Daily bar chart for a specific month (unchanged logic, per-month subset).
    """
    folder = ensure_folder(month_label)
    sub = df[df["month_label"] == month_label].copy()
    if "date" not in sub.columns or sub.empty:
        return None

    series = sub.groupby("date").size()
    plt.figure(figsize=(9, 4.5))
    series.plot(kind="bar", color="#5B8FF9")
    plt.title(f"Daily Issue Count — {month_label}")
    plt.xlabel("Date")
    plt.ylabel("Count")
    plt.tight_layout()

    path = f"{folder}/daily_trend.png"
    plt.savefig(path)
    plt.close()
    return path


def plot_status_breakdown(summary: dict, month_label: str) -> str | None:
    """
    NEW: Pie chart for Open vs Closed for a single month.
    """
    folder = ensure_folder(month_label)
    sub = _subset_month_df(summary, month_label)
    if sub.empty or "status" not in sub.columns:
        return None

    counts = sub["status"].astype(str).str.strip().str.title().value_counts()
    if counts.empty:
        return None

    plt.figure(figsize=(5.5, 5.5))
    counts.plot(kind="pie", autopct="%1.0f%%", startangle=90, colors=["#4C78A8", "#F58518", "#54A24B", "#E45756"])
    plt.title(f"Status Breakdown — {month_label}")
    plt.ylabel("")  # Hide y label for pie
    plt.tight_layout()

    path = f"{folder}/status_breakdown.png"
    plt.savefig(path)
    plt.close()
    return path
