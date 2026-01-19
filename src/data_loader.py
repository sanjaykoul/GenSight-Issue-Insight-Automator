
# -*- coding: utf-8 -*-
# src/data_loader.py
"""
Monthly-only loader for GenSight-Issue-Insight-Automator.

- Reads Excel with sheets like DEC2025, JAN2026
- Normalizes column names (tolerates spacing/case/parentheses)
- Parses dates (day-first)
- Adds month/year/month_label columns
- Returns a clean pandas DataFrame ready for aggregation/visualization
"""

import re
from typing import List, Dict, Tuple
import pandas as pd


# Month map like DEC2025 -> 12
_MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}


def _parse_month_sheet(sheet_name: str) -> Tuple[int, int, str]:
    """
    Accept names like 'DEC2025', 'JAN2026'. Return (month, year, label).
    Raises ValueError for non-monthly names.
    """
    s = sheet_name.strip().upper()
    m = re.match(r"^([A-Z]{3})(\d{4})$", s)
    if not m:
        raise ValueError(
            f"Sheet '{sheet_name}' is not in MONYYYY format (e.g., DEC2025)."
        )
    mon_abbr, year = m.group(1), int(m.group(2))
    if mon_abbr not in _MONTH_MAP:
        raise ValueError(f"Unknown month in sheet '{sheet_name}'. Use JAN..DEC.")
    return _MONTH_MAP[mon_abbr], year, f"{mon_abbr}{year}"


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to a standard set. Tolerates minor variations.
    Expected logical headers (any order):
      Project Name, Engineer Name, Associate ID, Associate Name,
      Issue Description, Start Date & Time, End Date & Time,
      Status, Request ID, Remarks
    """
    rename_map: Dict[str, str] = {}
    for c in df.columns:
        key = str(c).strip().lower()
        key = key.replace("&", "and")
        key = re.sub(r"\s+", " ", key)
        key = key.replace("(", "").replace(")", "")
        key = key.replace("/", " ")
        key = key.strip()

        if key.startswith("project"):
            rename_map[c] = "project"
        elif key.startswith("engineer"):
            rename_map[c] = "engineer"
        elif "associate" in key and "id" in key:
            rename_map[c] = "associate_id"
        elif "associate" in key and "name" in key:
            rename_map[c] = "associate_name"
        elif key.startswith("issue"):
            rename_map[c] = "issue"
        elif key.startswith("start"):
            rename_map[c] = "start"
        elif key.startswith("end"):
            rename_map[c] = "end"
        elif key.startswith("status"):
            rename_map[c] = "status"
        elif "ticket" in key or "request id" in key or key.startswith("request"):
            rename_map[c] = "request_id"
        elif key.startswith("remarks"):
            rename_map[c] = "remarks"
        else:
            # keep unknown; convert spaces to underscores
            rename_map[c] = key.replace(" ", "_")

    return df.rename(columns=rename_map)


def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce 'start' and 'end' to datetime (DD/MM/YYYY tolerated).
    Derive a 'date' column from 'start' (fallback to 'end').
    """
    for col in ["start", "end"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    if "start" in df.columns:
        df["date"] = pd.to_datetime(df["start"], errors="coerce").dt.date
    elif "end" in df.columns:
        df["date"] = pd.to_datetime(df["end"], errors="coerce").dt.date
    else:
        df["date"] = pd.NaT

    return df


def load_monthly_tracker(path: str) -> pd.DataFrame:
    """
    Read an Excel file that contains ONLY monthly sheets (e.g., DEC2025, JAN2026).
    Returns a unified DataFrame with normalized columns and added month/year fields.

    Output columns (best effort):
    ['month', 'year', 'month_label', 'project', 'engineer',
     'associate_id', 'associate_name', 'issue', 'start', 'end',
     'status', 'request_id', 'remarks', 'date']
    """
    xl = pd.ExcelFile(path, engine="openpyxl")
    frames: List[pd.DataFrame] = []

    for sheet in xl.sheet_names:
        try:
            month_num, year, month_label = _parse_month_sheet(sheet)
        except ValueError:
            # Skip non-month sheets if any (keeps tool flexible)
            continue

        df = xl.parse(sheet)
        df = df.dropna(how="all")
        if df.empty:
            continue

        df = _standardize_columns(df)
        df = _coerce_dates(df)

        # Add metadata
        df["month"] = month_num
        df["year"] = year
        df["month_label"] = month_label

        # Ensure expected columns exist
        for col in [
            "project", "engineer", "associate_id", "associate_name", "issue",
            "start", "end", "status", "request_id", "remarks", "date"
        ]:
            if col not in df.columns:
                df[col] = pd.NA

        ordered = [
            "month", "year", "month_label", "project", "engineer", "associate_id",
            "associate_name", "issue", "start", "end", "status", "request_id",
            "remarks", "date"
        ]
        df = df[ordered]

        # Basic trimming of strings
        for c in [
            "project", "engineer", "associate_id", "associate_name", "issue",
            "status", "request_id", "remarks", "month_label"
        ]:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip()

        frames.append(df)

    if not frames:
        raise ValueError(
            "No valid monthly sheets found. Use names like DEC2025, JAN2026, etc."
        )

    return pd.concat(frames, ignore_index=True)