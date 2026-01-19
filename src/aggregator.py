
# -*- coding: utf-8 -*-
# src/aggregator.py
"""
Aggregation & categorization for GenSight-Issue-Insight-Automator.
- Classifies issue types (labels tuned to show **Endpoint Compliance** specifically)
- Produces monthly/engineer/status/issue-type summaries
- Creates daily counts for each month
"""

from typing import Dict
import pandas as pd

# Keyword-based categories (tune anytime)
# NOTE: label here is EXACTLY how it shows in charts & AI summaries.
CATEGORIES = {
    "Citrix": ["citrix", "vdi"],
    "MFA": ["mfa", "otp", "authenticator", "notification"],
    "Endpoint Compliance": [
        "endpoint", "compliance", "dlp", "edr", "tanium", "pmc",
        "encryption", "bitlocker", "hostname", "sensor", "sense"
    ],
    "Access/Password": ["password", "access", "unlock", "reset", "sspr", "credential"],
    "Network/VPN": ["vpn", "zscaler", "network", "anyconnect", "proxy", "isp"],
}


def classify_issue(text: str) -> str:
    if not isinstance(text, str):
        return "Other"
    t = text.lower()
    for cat, keys in CATEGORIES.items():
        if any(k in t for k in keys):
            return cat
    return "Other"


def generate_monthly_summary(df: pd.DataFrame) -> Dict:
    """
    Create core summaries for the full dataframe (all months combined).
    Returns a dict with per-dimension counts and the raw df (with 'issue_type').
    """
    out: Dict = {}

    # Normalize helpful fields
    status_norm = df["status"].astype(str).str.strip().str.title() if "status" in df.columns else pd.Series([], dtype=str)
    engineer_norm = df["engineer"].astype(str).str.strip() if "engineer" in df.columns else pd.Series([], dtype=str)

    # Add issue_type with our tuned labels (incl. "Endpoint Compliance")
    local = df.copy()
    local["issue_type"] = local["issue"].apply(classify_issue)

    # By month
    by_month = local.groupby("month_label").size().reset_index(name="issue_count")

    # By status/engineer/issue_type
    out["by_status"] = status_norm.value_counts().to_dict()
    out["by_engineer"] = engineer_norm.value_counts().to_dict()
    out["by_issue_type"] = local["issue_type"].value_counts().to_dict()
    out["by_month"] = by_month

    # Daily counts per month (using 'date' as stored; per-month plots refine date selection)
    if "date" in local.columns:
        daily = local.groupby(["month_label", "date"]).size().reset_index(name="count")
    else:
        daily = pd.DataFrame(columns=["month_label", "date", "count"])
    out["daily"] = daily

    # Return raw df (with issue_type) for visualizer/reporting/AI
    out["raw"] = local
    return out


def filter_month(df: pd.DataFrame, month_label: str) -> pd.DataFrame:
    """Convenience filter to slice a single month."""
    return df[df["month_label"] == month_label].copy()
