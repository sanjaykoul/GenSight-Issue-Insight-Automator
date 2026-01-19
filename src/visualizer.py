
# -*- coding: utf-8 -*-
# src/visualizer.py
"""
Visualization utilities for GenSight-Issue-Insight-Automator.
- Saves PNG charts in reports/<MONTH>/charts/
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")


def ensure_folder(month_label: str) -> str:
    folder = f"reports/{month_label}/charts"
    os.makedirs(folder, exist_ok=True)
    return folder


def plot_issue_distribution(summary: dict, month_label: str) -> str | None:
    """
    Bar chart for issue-type distribution across the full dataset,
    saved under the given month’s charts folder.
    """
    folder = ensure_folder(month_label)
    issue_dict = summary.get("by_issue_type", {})
    if not issue_dict:
        return None

    items = sorted(issue_dict.items(), key=lambda x: x[1], reverse=True)
    labels, values = zip(*items)

    plt.figure(figsize=(8, 5))
    sns.barplot(x=list(labels), y=list(values), palette="Blues_d")
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
    Bar chart for top-N engineers by issue volume (overall),
    saved under month’s charts folder for reporting convenience.
    """
    folder = ensure_folder(month_label)
    eng_dict = summary.get("by_engineer", {})
    if not eng_dict:
        return None

    items = sorted(eng_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels, values = zip(*items)

    plt.figure(figsize=(9, 5))
    sns.barplot(x=list(labels), y=list(values), palette="Greens_d")
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
    Daily bar chart for a specific month.
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
