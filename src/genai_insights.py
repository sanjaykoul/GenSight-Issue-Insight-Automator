
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Smarter per-month AI-like summary (rule-based):
- True per-month totals (not combined)
- Closed/Open + closure rate %
- Top 3 issue types with %
- Peak day & quiet day
- Busiest weekday
- Month-over-Month change %
- Actionable recommendations based on top category
"""

from typing import Dict, Optional, Tuple
import re
import pandas as pd


def _safe_counts(series: pd.Series) -> dict:
    if series is None or series.empty:
        return {}
    return series.value_counts().to_dict()


def _top_n_with_pct(counts: dict, n: int = 3) -> str:
    if not counts:
        return "N/A"
    total = sum(counts.values())
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]
    return ", ".join([f"{k} ({v} • {v * 100 / total:.0f}%)" for k, v in items])


def _label_to_year_month(label: str) -> Optional[Tuple[int, int]]:
    """Convert 'DEC2025' -> (2025, 12)."""
    m = re.match(r"^([A-Z]{3})(\d{4})$", str(label).upper().strip())
    if not m:
        return None
    mon = m.group(1)
    year = int(m.group(2))
    mon_map = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
        "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
        "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }
    if mon not in mon_map:
        return None
    return year, mon_map[mon]


def _prev_month_label(all_labels: list, current: str) -> Optional[str]:
    """
    Find the immediate previous month label from a list of labels like ['DEC2025','JAN2026',...].
    """
    # Sort labels by (year, month)
    parsed = []
    for lab in all_labels:
        ym = _label_to_year_month(lab)
        if ym:
            parsed.append((*ym, lab))  # (year, month, label)
    if not parsed:
        return None
    parsed.sort()  # by year, then month
    labels_sorted = [p[2] for p in parsed]
    if current not in labels_sorted:
        return None
    idx = labels_sorted.index(current)
    return labels_sorted[idx - 1] if idx - 1 >= 0 else None


def generate_summary_text(summary: Dict, month_label: str) -> str:
    raw = summary.get("raw")
    if raw is None or raw.empty:
        return f"No data available for {month_label}."

    # ---- Filter to the requested month
    sub = raw[raw["month_label"] == month_label].copy()
    if sub.empty:
        return f"No data available for {month_label}."

    # ---- Normalize fields
    status = sub["status"].astype(str).str.strip().str.title() if "status" in sub.columns else pd.Series(dtype=str)
    engineer = sub["engineer"].astype(str).str.strip() if "engineer" in sub.columns else pd.Series(dtype=str)
    if "issue_type" not in sub.columns:
        sub["issue_type"] = "Other"

    by_status = _safe_counts(status)
    by_issue_type = _safe_counts(sub["issue_type"])
    by_engineer = _safe_counts(engineer)

    total = int(sub.shape[0])
    closed = int(by_status.get("Closed", 0))
    open_ = int(by_status.get("Open", 0))
    closure_rate = (closed * 100 / total) if total else 0

    # ---- Peak/quiet day (by date)
    peak_str = "N/A"
    quiet_str = "N/A"
    busiest_weekday_str = "N/A"
    if "date" in sub.columns:
        daily = sub.groupby("date").size().sort_values(ascending=False)
        if not daily.empty:
            peak_day = daily.index[0]
            peak_val = int(daily.iloc[0])
            peak_str = f"{peak_day} ({peak_val})"
            # min but non-zero to avoid N/A if zeros exist
            daily_pos = daily[daily > 0].sort_values()
            if not daily_pos.empty:
                q_day, q_val = daily_pos.index[0], int(daily_pos.iloc[0])
                quiet_str = f"{q_day} ({q_val})"

        # Weekday pattern
        dd = pd.to_datetime(sub["date"])
        wcounts = dd.dt.day_name().value_counts()
        if not wcounts.empty:
            busiest_weekday_str = f"{wcounts.index[0]} ({int(wcounts.iloc[0])})"

    # ---- Top 3 issue types (with %)
    top3_issue_types = _top_n_with_pct(by_issue_type, 3)

    # ---- MoM change
    mom_change_str = "N/A"
    by_month_df = summary.get("by_month")
    if by_month_df is not None and not by_month_df.empty:
        all_labels = by_month_df["month_label"].tolist()
        prev_lab = _prev_month_label(all_labels, month_label)
        cur_count = int(by_month_df.set_index("month_label").loc[month_label, "issue_count"]) \
                    if month_label in by_month_df["month_label"].values else None
        prev_count = int(by_month_df.set_index("month_label").loc[prev_lab, "issue_count"]) \
                    if prev_lab and prev_lab in by_month_df["month_label"].values else None
        if cur_count is not None and prev_count is not None and prev_count > 0:
            delta = (cur_count - prev_count) * 100 / prev_count
            sign = "increase" if delta > 0 else "decrease" if delta < 0 else "no change"
            mom_change_str = f"{delta:+.1f}% {sign} vs {prev_lab}"
        elif cur_count is not None and prev_count == 0:
            mom_change_str = "∞% increase (previous month had 0)"
        elif cur_count is not None and prev_count is None:
            mom_change_str = "No previous month available for comparison"

    # ---- Recommendations (simple rules based on top issue type)
    recos = []
    if by_issue_type:
        dominant = max(by_issue_type.items(), key=lambda x: x[1])[0]
        if dominant.lower() == "endpoint":
            recos.append("Validate compliance agents (EDR/DLP/Tanium/PMC) and automate remediation scripts.")
        elif dominant.lower() == "citrix":
            recos.append("Coordinate with Citrix/Network team for URL reachability and client reliability checks.")
        elif dominant.lower() in ("access/password", "access", "password"):
            recos.append("Promote SSPR and password hygiene; share quick guides to reduce resets.")
        elif dominant.lower() == "mfa":
            recos.append("Push MFA enrollment/notification troubleshooting tips; preemptive user comms.")
        else:
            recos.append("Review top categories and publish targeted how-to guides for recurring issues.")
    if closure_rate < 95:
        recos.append("Improve closure rate with SOPs and triage playbooks.")
    if isinstance(peak_str, str) and peak_str != "N/A":
        recos.append("Staff peak days proactively to avoid backlog.")

    # ---- Build the narrative
    parts = [
        f"Monthly summary for {month_label}:",
        f"• Total issues: {total}  |  Closed: {closed}  |  Open: {open_}  |  Closure rate: {closure_rate:.1f}%",
        f"• Top 3 categories: {top3_issue_types}",
        f"• Peak day: {peak_str}  |  Quiet day: {quiet_str}  |  Busiest weekday: {busiest_weekday_str}",
        f"• Month-over-Month change: {mom_change_str}",
    ]
    if recos:
        parts.append("• Recommendations: " + " ".join(recos))

    parts.append("• See attached charts for daily trend, issue mix, weekday pattern, and workload.")
    return "\n".join(parts)
