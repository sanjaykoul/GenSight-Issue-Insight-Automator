
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Lightweight, rule-based insights (no external LLM call).
Generates a readable monthly summary text from the computed counts,
guaranteeing that counts come from the requested month only.
"""

from typing import Dict, Any


def _month_slice(summary: Dict[str, Any], key: str, month_label: str) -> Dict[str, int]:
    """
    Extract a per-month dictionary like {item: count} from a flexible summary structure.

    Supports:
      A) summary[key][month_label] == {item: count}
      B) summary[month_label][key] == {item: count}
      C) summary[key] == {item: count}  (already month specific / flat)
    """
    # A) summary[key][month_label]
    section = summary.get(key)
    if isinstance(section, dict):
        if month_label in section and isinstance(section[month_label], dict):
            return section[month_label]
        # C) If this is already a flat {item: count} map
        if section and all(isinstance(v, (int, float)) for v in section.values()):
            return section

    # B) summary[month_label][key]
    if month_label in summary and isinstance(summary[month_label], dict):
        inner = summary[month_label].get(key)
        if isinstance(inner, dict):
            return inner

    return {}


def generate_summary_text(summary: Dict[str, Any], month_label: str) -> str:
    """
    Build a concise monthly summary strictly from the month-specific slice.

    Expected summary keys (flexible layout supported):
      - "by_status": {month_label: {status: count}} or {status: count}
      - "by_issue_type": {month_label: {issue_type: count}} or {issue_type: count}
      - "by_engineer": {month_label: {engineer: count}} or {engineer: count}
      - "raw": pandas.DataFrame with a "month_label" column (optional, for accurate totals)
    """

    # Month-specific dictionaries (robust to different summary shapes)
    by_status_m = _month_slice(summary, "by_status", month_label)
    by_issue_type_m = _month_slice(summary, "by_issue_type", month_label)
    by_engineer_m = _month_slice(summary, "by_engineer", month_label)

    # Compute total issues for the month:
    # Prefer counting rows from summary["raw"] filtered by month_label if available.
    total = 0
    raw_df = summary.get("raw")
    if raw_df is not None:
        try:
            # raw_df is expected to be a pandas DataFrame with month_label column
            month_rows = raw_df[raw_df["month_label"] == month_label]
            total = int(len(month_rows))
        except Exception:
            # Fallback to sum of issue-type counts if structure is unexpected
            total = int(sum(by_issue_type_m.values())) if by_issue_type_m else 0
    else:
        total = int(sum(by_issue_type_m.values())) if by_issue_type_m else 0

    closed = int(by_status_m.get("Closed", 0))
    open_ = int(by_status_m.get("Open", 0))

    top_issue = None
    if by_issue_type_m:
        top_issue = max(by_issue_type_m.items(), key=lambda x: x[1])

    top_engineer = None
    if by_engineer_m:
        top_engineer = max(by_engineer_m.items(), key=lambda x: x[1])

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
