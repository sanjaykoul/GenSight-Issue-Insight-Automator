
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Lightweight, rule-based insights (no external LLM call).
Generates a readable monthly summary text from strictly month-specific counts.
"""

from typing import Dict, Any


def _month_slice(summary: Dict[str, Any], key: str, month_label: str) -> Dict[str, int]:
    section = summary.get(key)
    if isinstance(section, dict):
        if month_label in section and isinstance(section[month_label], dict):
            return section[month_label]
        if section and all(isinstance(v, (int, float)) for v in section.values()):
            return section
    if month_label in summary and isinstance(summary[month_label], dict):
        inner = summary[month_label].get(key)
        if isinstance(inner, dict):
            return inner
    return {}


def _status_counts_from_raw(summary: Dict[str, Any], month_label: str) -> Dict[str, int]:
    raw_df = summary.get("raw")
    if raw_df is None:
        return {}
    try:
        df_m = raw_df[raw_df["month_label"] == month_label].copy()
        if df_m.empty:
            return {}
        ser = df_m.get("status").astype(str).str.strip().str.lower().fillna("")
        closed = int((ser == "closed").sum())
        open_ = int((ser == "open").sum())
        return {"Closed": closed, "Open": open_}
    except Exception:
        return {}


def _engineer_counts_from_raw(summary: Dict[str, Any], month_label: str) -> Dict[str, int]:
    raw_df = summary.get("raw")
    if raw_df is None:
        return {}
    try:
        df_m = raw_df[raw_df["month_label"] == month_label].copy()
        if df_m.empty:
            return {}
        eng = df_m.get("engineer").astype(str).str.strip()
        return {k: int(v) for k, v in eng.value_counts().to_dict().items()}
    except Exception:
        return {}


def generate_summary_text(summary: Dict[str, Any], month_label: str) -> str:
    # Month-scoped slices or recomputation
    by_issue_type_m = _month_slice(summary, "by_issue_type", month_label)
    by_engineer_m = _engineer_counts_from_raw(summary, month_label)  # ✅ per-month from raw

    # Status: prefer recomputed per-month
    by_status_m = _status_counts_from_raw(summary, month_label)
    if not by_status_m:
        by_status_m = _month_slice(summary, "by_status", month_label)

    # Total issues for month
    total = 0
    raw_df = summary.get("raw")
    if raw_df is not None:
        try:
            total = int((raw_df["month_label"] == month_label).sum())
        except Exception:
            total = int(sum(by_issue_type_m.values())) if by_issue_type_m else 0
    else:
        total = int(sum(by_issue_type_m.values())) if by_issue_type_m else 0

    closed = int(by_status_m.get("Closed", 0))
    open_ = int(by_status_m.get("Open", 0))

    top_issue = max(by_issue_type_m.items(), key=lambda x: x[1]) if by_issue_type_m else None
    top_engineer = max(by_engineer_m.items(), key=lambda x: x[1]) if by_engineer_m else None

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
