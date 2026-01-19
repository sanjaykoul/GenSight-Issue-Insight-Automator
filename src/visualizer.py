
# -*- coding: utf-8 -*-
# src/visualizer.py

import os
from typing import Dict, Any, Optional, Sequence
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Consistent visuals
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
})


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def _month_slice(summary: Dict[str, Any], key: str, month_label: str) -> Dict[str, int]:
    if isinstance(summary.get(key), dict):
        inner = summary[key]
        if month_label in inner and isinstance(inner[month_label], dict):
            return inner[month_label]
        if all(isinstance(v, (int, float)) for v in (inner.values() or [])):
            return inner
    if month_label in summary and isinstance(summary[month_label], dict):
        maybe = summary[month_label].get(key)
        if isinstance(maybe, dict):
            return maybe
    return {}


def _barplot(
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str,
    out_path: str,
) -> Optional[str]:
    """Generic barplot that saves to file and returns the path (or None if empty)."""
    ensure_dir(os.path.dirname(out_path))
    if not labels or not values:
        return None

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x=list(labels), y=list(values), color=color)  # ✅ no FutureWarning
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")

    # Annotate bars with values
    for i, v in enumerate(values):
        try:
            ax.text(i, v, f"{int(v)}", ha="center", va="bottom", fontsize=9)
        except Exception:
            pass

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_issue_distribution(summary: Dict[str, Any], month_label: str) -> Optional[str]:
    """
    Issue type distribution for a month (bar chart).
    Returns path to saved .png, or None if no data.
    """
    counts = _month_slice(summary, "by_issue_type", month_label)
    if not counts:
        return None

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels, values = zip(*items)
    out = f"reports/{month_label}/charts/issue_distribution_{month_label}.png"
    return _barplot(
        labels, values,
        title="Issue Distribution",
        xlabel="Issue Type",
        ylabel="Count",
        color="#4C78A8",  # blue
        out_path=out,
    )


def plot_engineer_workload(summary: Dict[str, Any], month_label: str) -> Optional[str]:
    """
    Engineer workload for a month (bar chart).
    Returns path to saved .png, or None if no data.
    """
    # Prefer recomputed from raw if present
    raw_df = summary.get("raw")
    if raw_df is not None:
        df_m = raw_df[raw_df["month_label"] == month_label]
        if not df_m.empty:
            counts = df_m["engineer"].astype(str).str.strip().value_counts().to_dict()
        else:
            counts = {}
    else:
        counts = _month_slice(summary, "by_engineer", month_label)

    if not counts:
        return None

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels, values = zip(*items)
    out = f"reports/{month_label}/charts/engineer_workload_{month_label}.png"
    return _barplot(
        labels, values,
        title="Engineer Workload",
        xlabel="Engineer",
        ylabel="Issue Count",
        color="#59A14F",  # green
        out_path=out,
    )


def plot_daily_trend(df_raw: pd.DataFrame, month_label: str) -> Optional[str]:
    """
    Daily issue count trend for the given month (bar chart).
    Returns path to saved .png, or None if no data.
    """
    if df_raw is None or df_raw.empty:
        return None

    df = df_raw[df_raw["month_label"] == month_label].copy()
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    daily = df.groupby(df["date"].dt.date).size().sort_index()
    if daily.empty:
        return None

    labels = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in daily.index]
    values = list(daily.values)
    out = f"reports/{month_label}/charts/daily_trend_{month_label}.png"
    return _barplot(
        labels, values,
        title="Daily Issue Trend",
        xlabel="Date",
        ylabel="Issue Count",
        color="#F28E2B",  # orange
        out_path=out,
    )
