
# -*- coding: utf-8 -*-
# src/genai_insights.py
"""
Smarter per-month AI-like summary (rule-based):
- True per-month totals (not combined)
- Closed/Open + closure rate %
- Top 3 issue types with %
- Peak day & quiet day (using date that falls inside the month)
- Busiest weekday
- Month-over-Month change %
- Actionable recommendations based on top category (incl. "Endpoint Compliance")
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
    parsed = []
    for lab in all_labels:
        ym = _label_to_year_month(lab)
        if ym:
            parsed.append((*ym, lab))  # (year, month, label)
    if not parsed:
        return None
    parsed.sort()
    labels_sorted = [p[2] for p in parsed]
    if current not in labels_sorted:
        return None
    idx = labels_sorted.index(current)
    return labels_sorted[idx - 1] if idx - 1 >= 0 else None


def _pick_date_for_month(row: pd.Series, y: int, m: int):
    """
    Return a date from row that lies inside (y, m):
      - Prefer 'end' if in (y, m),
      - else 'start' if in (y, m),
      - else None.
    """
    start = pd.to_datetime(row.get("start"), errors="coerce")
    end = pd.to_datetime(row.get("end"), errors="coerce")
    if pd.notna(end) and end.year == y and end.month == m:
        return end.date()
    if pd.notna(start) and start.year == y and start.month == m:
        return start.date()
    return None


def generate_summary_text(summary: Dict, month_label: str) -> str:
    raw = summary.get("raw")
    if raw is None or raw.empty:
        return f"No data available for {month_label}."

    sub = raw[raw["month_label"] == month_label].copy()
    if sub.empty:
        return f"No data available for {month_label}."

    # Normalize fields
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

    # Peak/quiet day restricted to dates that lie inside the month_label
    peak_str, quiet_str, busiest_weekday_str = "N/A", "N/A", "N/A"
    ym = _label_to_year_month(month_label)
    if ym and ("start" in sub.columns or "end" in sub.columns):
        yy, mm = ym
        month_dates = sub.apply(lambda r: _pick_date_for_month(r, yy, mm), axis=1)
        md = pd.to_datetime(month_dates.dropna(), errors="coerce")
        if not md.empty:
            daily = md.value_counts().sort_index()
            if not daily.empty:
                d_desc = daily.sort_values(ascending=False)
                peak_day = d_desc.index[0].date()
                peak_val = int(d_desc.iloc[0])
                peak_str = f"{peak_day} ({peak_val})"
                d_min = daily[daily > 0].sort_values()
                if not d_min.empty:
                    q_day = d_min.index[0].date()
                    q_val = int(d_min.iloc[0])
                    quiet_str = f"{q_day} ({q_val})"
            wcounts = md.dt.day_name().value_counts()
            if not wcounts.empty:
                busiest_weekday_str = f"{wcounts.index[0]} ({int(wcounts.iloc[0])})"

    # Top 3 issue types with %
    top3_issue_types = _top_n_with_pct(by_issue_type, 3)

    # MoM change
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

    # Recommendations (note the explicit Endpoint Compliance label)
    recos = []
    if by_issue_type:
        dominant = max(by_issue_type.items(), key=lambda x: x[1])[0]
        if dominant.lower() == "endpoint compliance":
            recos.append("Validate agents (EDR/DLP/Tanium/PMC), fix hostnames, and automate remediation scripts.")
        elif dominant.lower() == "citrix":
            recos.append("Coordinate with Citrix/Network for URL reachability and client reliability checks.")
        elif dominant.lower() in ("access/password", "access", "password"):
            recos.append("Promote SSPR and password hygiene; publish quick guides to reduce resets.")
        elif dominant.lower() == "mfa":
            recos.append("Push MFA enrollment/notification troubleshooting tips; preemptive user comms.")
        else:
            recos.append("Review top categories and publish targeted how-to guides for recurring issues.")
    if closure_rate < 95:
        recos.append("Improve closure rate with SOPs and triage playbooks.")
    if peak_str != "N/A":
        recos.append("Staff peak days proactively to avoid backlog.")

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
    