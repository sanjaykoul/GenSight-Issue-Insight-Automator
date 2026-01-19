
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

