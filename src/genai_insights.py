
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Per-month AI-like summary (rule-based, no external LLM).
This version filters to the requested month_label BEFORE counting,
so the numbers reflect that month only.
"""

from typing import Dict
import pandas as pd


def _safe_counts(series: pd.Series) -> dict:
    if series is None or series.empty:
        return {}
    return series.value_counts().to_dict()


def _top_item(counts: dict):
    if not counts:
        return None
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0]


def generate_summary_text(summary: Dict, month_label: str) -> str:
    """
    Build a natural language summary for ONE month (month_label).
    Uses summary['raw'] (the full DataFrame) and filters down to month_label.
    """
    raw = summary.get("raw")
    if raw is None or raw.empty:
        return f"No data available for {month_label}."

    # ---- Filter to the requested month
    sub = raw[raw["month_label"] == month_label].copy()
    if sub.empty:
        return f"No data available for {month_label}."

    # ---- Normalize common fields
    status = sub["status"].astype(str).str.strip().str.title() if "status" in sub.columns else pd.Series(dtype=str)
    engineer = sub["engineer"].astype(str).str.strip() if "engineer" in sub.columns else pd.Series(dtype=str)
    # 'issue_type' should already exist from aggregator; if not, default to 'Other'
    if "issue_type" not in sub.columns:
        sub["issue_type"] = "Other"

    # ---- Per-month counts
    by_status = _safe_counts(status)
    by_engineer = _safe_counts(engineer)
    by_issue_type = _safe_counts(sub["issue_type"])

    total = int(sub.shape[0])
    closed = int(by_status.get("Closed", 0))
    open_ = int(by_status.get("Open", 0))

    top_issue = _top_item(by_issue_type)
    top_engineer = _top_item(by_engineer)

    parts = [
        f"Monthly summary for {month_label}:",
        f"• Total issues recorded: {total}",
        f"• Status — Closed: {closed}, Open: {open_}",
    ]

    if top_issue:
        parts.append(f"• Most frequent issue type: {top_issue[0]} ({top_issue[1]})")
    if top_engineer:
        parts.append(f"• Top engineer by volume: {top_engineer[0]} ({top_engineer[1]} issues)")

    parts.append("• See charts for daily trend, issue mix, and workload distribution.")
    return "\n".join(parts)