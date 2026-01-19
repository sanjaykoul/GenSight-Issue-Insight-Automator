
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Lightweight, rule-based insights (no external LLM call).
Generates a readable monthly summary text from the computed counts,
guaranteeing that all counts (total, status, issue, engineer) come from the
requested month only.
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
    section = summary.get(key)
    if isinstance(section, dict):
        # A) summary[key][month_label]
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


def _status_counts_from_raw(summary: Dict[str, Any], month_label: str) -> Dict[str, int]:
    """
    Recompute monthly status counts from summary['raw'] if available.
    Case-insensitive mapping for 'Closed' and 'Open' buckets.
    """
    raw_df = summary.get("raw")
    if raw_df is None:
        return {}

    try:
        df_m = raw_df[raw_df["month_label"] == month_label].copy()
        if df_m.empty:
            return {}

        # Normalize status strings
        status_series = (
            df_m.get("status")
            .astype(str)
            .str.strip()
            .str.lower()
            .fillna("")
        )

        closed_count = int((status_series == "closed").sum())
        open_count = int((status_series == "open").sum())

        # If there are other statuses, extend mapping here as needed.
        return {"Closed": closed_count, "Open": open_count}
    except Exception:
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
    by_issue_type_m = _month_slice(summary, "by_issue_type", month_label)
    by_engineer_m = _month_slice(summary, "by_engineer", month_label)

    # 🔒 Status counts: ALWAYS prefer recomputing from 'raw' if available,
    # to guarantee per-month numbers, even if 'by_status' is a global flat dict.
    recomputed_status = _status_counts_from_raw(summary, month_label)
    if recomputed_status:
        by_status_m = recomputed_status
    else:
        by_status_m = _month_slice(summary, "by_status", month_label)

    # Compute total:
    # Prefer counting rows from summary["raw"] filtered by month_label (most accurate).
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