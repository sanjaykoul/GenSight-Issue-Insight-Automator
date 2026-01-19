
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Lightweight, rule-based insights (no external LLM call).
Generates a readable monthly summary text from the computed counts.
"""

from typing import Dict


def generate_summary_text(summary: Dict, month_label: str) -> str:
    by_status = summary.get("by_status", {})
    by_issue_type = summary.get("by_issue_type", {})
    by_engineer = summary.get("by_engineer", {})

    total = sum(by_issue_type.values()) if by_issue_type else 0
    closed = by_status.get("Closed", 0)
    open_ = by_status.get("Open", 0)

    top_issue = None
    if by_issue_type:
        top_issue = sorted(by_issue_type.items(), key=lambda x: x[1], reverse=True)[0]

    top_engineer = None
    if by_engineer:
        top_engineer = sorted(by_engineer.items(), key=lambda x: x[1], reverse=True)[0]

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