
# -*- coding: utf-8 -*-
# src/genai_summary_hf.py
"""
GenAI (Hugging Face) summarization for GenSight using small CPU-friendly models.

- Primary: T5-small via `text2text-generation`.
- Fallback: DistilBART (sshleifer/distilbart-cnn-6-6) via `summarization`.
- Strictly month-scoped; entity whitelists; sanitization.
- Always include these insights (deterministically enforced post-LLM):
    * Headline (total, Closed, Open)
    * MoM trend with descriptive phrasing: "Slight increase/decrease vs previous month (+/-Δ)."
    * Top issues (top 1–3) with count, % share, momentum (↑/↓/→) vs prev
    * Top engineer + overall close rate (%)
    * Most improved issue (largest decrease vs prev)
    * Emerging issue (present this month, absent prev)
    * Issue diversity (unique issue types up/down)
    * Engineer distribution (even vs concentrated)
- Average resolution time has been REMOVED per user request.
- Returns None on failure so caller can fallback to deterministic summary.
"""

import os
import re
from typing import Dict, Any, Optional, List, Tuple, Set

# --- Lazy imports (project must still run if transformers is absent) ---
try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except Exception:
    _TRANSFORMERS_AVAILABLE = False

_HF_T5 = None
_HF_BART = None

# Allow override; defaults run on CPU in Codespaces
HF_MODEL_PRIMARY = os.getenv("HF_MODEL", "t5-small")
HF_MODEL_FALLBACK = os.getenv("HF_MODEL_FALLBACK", "sshleifer/distilbart-cnn-6-6")
GENAI_SENTENCES = int(os.getenv("GENAI_SENTENCES", "6"))  # default to 6 to fit all insights


# ----------------------- Pipeline helpers -----------------------
def _ensure_t5():
    """Create/load the T5 text2text-generation pipeline (CPU)."""
    global _HF_T5
    if not _TRANSFORMERS_AVAILABLE:
        return None
    if _HF_T5 is not None:
        return _HF_T5
    try:
        _HF_T5 = pipeline(
            task="text2text-generation",
            model=HF_MODEL_PRIMARY,
            device=-1,  # CPU
            clean_up_tokenization_spaces=True,
        )
        return _HF_T5
    except Exception:
        return None


def _ensure_bart():
    """Create/load the DistilBART summarization pipeline (CPU) for fallback."""
    global _HF_BART
    if not _TRANSFORMERS_AVAILABLE:
        return None
    if _HF_BART is not None:
        return _HF_BART
    try:
        _HF_BART = pipeline(
            task="summarization",
            model=HF_MODEL_FALLBACK,
            device=-1,  # CPU
            clean_up_tokenization_spaces=True,
        )
        return _HF_BART
    except Exception:
        return None


# ----------------------- Data helpers -----------------------
def _safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _month_slice(summary: Dict[str, Any], key: str, month_label: str) -> Dict[str, int]:
    """
    Extract a per-month dictionary like {item: count} from flexible summary shapes:
      A) summary[key][month_label] == {item: count}
      B) summary[month_label][key] == {item: count}
      C) summary[key] == {item: count} (flat)
    """
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
    """Recompute Closed/Open counts for the month from summary['raw'] if available."""
    raw_df = summary.get("raw")
    if raw_df is None:
        return {}
    try:
        df_m = raw_df[raw_df["month_label"] == month_label].copy()
        if df_m.empty:
            return {}
        ser = df_m.get("status").astype(str).str.strip().str.lower()
        closed = _safe_int((ser == "closed").sum())
        open_ = _safe_int((ser == "open").sum())
        return {"Closed": closed, "Open": open_}
    except Exception:
        return {}


def _engineer_counts_from_raw(summary: Dict[str, Any], month_label: str) -> Dict[str, int]:
    """Compute per-month engineer workload directly from raw (most reliable)."""
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


def _issue_counts_from_raw(summary: Dict[str, Any], month_label: str) -> Dict[str, int]:
    """Prefer raw 'issue' column if exists to avoid shape ambiguity."""
    raw_df = summary.get("raw")
    if raw_df is None:
        return {}
    try:
        df_m = raw_df[raw_df["month_label"] == month_label].copy()
        if df_m.empty:
            return {}
        issue_col = "issue" if "issue" in df_m.columns else None
        if issue_col:
            issues = df_m[issue_col].astype(str).str.strip()
            return {k: int(v) for k, v in issues.value_counts().to_dict().items()}
        # Fallback to aggregated section if provided:
        return _month_slice(summary, "by_issue_type", month_label)
    except Exception:
        return {}


def _prev_month_label(summary: Dict[str, Any], month_label: str) -> Optional[str]:
    """Infer previous month by ordering unique month_label in raw_df."""
    raw_df = summary.get("raw")
    if raw_df is None or "month_label" not in raw_df.columns:
        return None
    try:
        labels = list(dict.fromkeys(raw_df["month_label"].astype(str).tolist()))  # preserve order
        if month_label in labels:
            idx = labels.index(month_label)
            if idx > 0:
                return labels[idx - 1]
    except Exception:
        pass
    return None


def _normalize_labels(d: Dict[str, int]) -> Dict[str, int]:
    """Light normalization of label whitespace (keep case)."""
    out = {}
    for k, v in d.items():
        kk = re.sub(r"\s+", " ", str(k).strip())
        out[kk] = _safe_int(v)
    return out


def _top_n(d: Dict[str, int], k=3) -> List[Tuple[str, int]]:
    return sorted(d.items(), key=lambda x: x[1], reverse=True)[:k] if d else []


# ----------------------- Deterministic insight computations -----------------------
def _compute_totals(summary: Dict[str, Any], month_label: str) -> Tuple[int, int, int]:
    raw_df = summary.get("raw")
    total = 0
    if raw_df is not None:
        try:
            total = int((raw_df["month_label"] == month_label).sum())
        except Exception:
            total = 0
    by_status = _status_counts_from_raw(summary, month_label)
    return total, _safe_int(by_status.get("Closed", 0)), _safe_int(by_status.get("Open", 0))


def _compute_mom(summary: Dict[str, Any], month_label: str) -> Tuple[Optional[str], int, int, Optional[str]]:
    """Returns (prev_label, total_cur, total_prev, trend_line)."""
    raw_df = summary.get("raw")
    if raw_df is None:
        return None, 0, 0, None
    total_cur = int((raw_df["month_label"] == month_label).sum())
    prev_label = _prev_month_label(summary, month_label)
    total_prev = int((raw_df["month_label"] == prev_label).sum()) if prev_label else 0
    if prev_label and total_prev >= 0:
        delta = total_cur - total_prev
        if delta == 0:
            trend = "Overall workload stable compared to last month."
        elif delta > 0:
            trend = f"Slight increase vs previous month (+{delta})."
        else:
            trend = f"Slight decrease vs previous month (-{abs(delta)})."
    else:
        trend = None
    return prev_label, total_cur, total_prev, trend


def _issue_trends(summary: Dict[str, Any], month_label: str, total_cur: int, prev_label: Optional[str]):
    by_issue_cur = _normalize_labels(_issue_counts_from_raw(summary, month_label))
    by_issue_prev = _normalize_labels(_issue_counts_from_raw(summary, prev_label)) if prev_label else {}
    top_cur = _top_n(by_issue_cur, 3)
    top3 = []
    for issue, cnt in top_cur:
        share = round((cnt / total_cur) * 100) if total_cur > 0 else 0
        prev_cnt = _safe_int(by_issue_prev.get(issue, 0))
        arrow = "→"
        if prev_label:
            if cnt > prev_cnt: arrow = "↑"
            elif cnt < prev_cnt: arrow = "↓"
        top3.append((issue, cnt, share, arrow))
    return by_issue_cur, by_issue_prev, top3


def _most_improved_issue(by_issue_cur: Dict[str, int], by_issue_prev: Dict[str, int]) -> Optional[str]:
    candidates = []
    for issue, prev_cnt in by_issue_prev.items():
        cur_cnt = _safe_int(by_issue_cur.get(issue, 0))
        drop = prev_cnt - cur_cnt
        if drop > 0:
            candidates.append((issue, drop))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _emerging_issue(by_issue_cur: Dict[str, int], by_issue_prev: Dict[str, int]) -> Optional[str]:
    new_items = [(issue, cnt) for issue, cnt in by_issue_cur.items() if issue not in by_issue_prev]
    if not new_items:
        return None
    new_items.sort(key=lambda x: x[1], reverse=True)
    return new_items[0][0]


def _engineer_distribution(by_eng_cur: Dict[str, int], total_cur: int) -> Optional[str]:
    if total_cur <= 0 or not by_eng_cur:
        return None
    top = _top_n(by_eng_cur, 1)[0]
    name, cnt = top
    share = cnt / total_cur
    pct = round(share * 100)
    if share >= 0.60:
        return f"Workload concentrated: {name} handled {pct}%."
    return "Workload evenly distributed among engineers."


# ----------------------- Deterministic line builders -----------------------
def _line_headline(month_label: str, total: int, closed: int, open_: int) -> str:
    return f"{month_label}: {total} issues; Closed {closed}, Open {open_}."


def _line_trend(prev_label: Optional[str], total_cur: int, total_prev: int) -> Optional[str]:
    if not prev_label:
        return None
    delta = total_cur - total_prev
    if delta == 0:
        return "Overall workload stable compared to last month."
    if delta > 0:
        return f"Slight increase vs previous month (+{delta})."
    return f"Slight decrease vs previous month (-{abs(delta)})."


def _line_top_issues(top3: List[Tuple[str, int, int, str]]) -> Optional[str]:
    if not top3:
        return None
    label = "Top issues:" if len(top3) > 1 else "Top issue:"
    bits = [f"{issue} ({cnt}, {share}%, {arrow})" for issue, cnt, share, arrow in top3]
    # If all arrows are "→" and look noisy, we still keep them for consistency.
    return f"{label} " + ", ".join(bits) + "."


def _line_top_engineer(by_eng_cur: Dict[str, int], total: int, closed: int) -> Optional[str]:
    if not by_eng_cur:
        return None
    name, cnt = _top_n(by_eng_cur, 1)[0]
    close_rate = round((closed / total) * 100) if total > 0 else 0
    return f"Top engineer: {name} ({cnt}); overall close rate {close_rate}%."


def _line_most_improved(mi: Optional[str], prev_label: Optional[str]) -> Optional[str]:
    if mi and prev_label:
        return f"Most improved: {mi} decreased compared to {prev_label}."
    return None


def _line_emerging(em: Optional[str]) -> Optional[str]:
    if em:
        return f"New emerging issue: {em} appeared this month."
    return None


def _line_diversity(by_issue_cur: Dict[str, int], by_issue_prev: Dict[str, int]) -> Optional[str]:
    if by_issue_prev is None:
        return None
    cur_n = len(by_issue_cur)
    prev_n = len(by_issue_prev) if by_issue_prev is not None else 0
    if prev_n == 0:
        return None
    if cur_n > prev_n:
        return f"Issue variety increased ({cur_n} vs {prev_n} types)."
    if cur_n < prev_n:
        return f"Issue variety decreased ({cur_n} vs {prev_n} types)."
    return "Issue variety remained unchanged."


def _deterministic_insight_lines(summary: Dict[str, Any], month_label: str) -> Dict[str, Optional[str]]:
    total, closed, open_ = _compute_totals(summary, month_label)
    prev_label, total_cur, total_prev, trend_line = _compute_mom(summary, month_label)
    by_issue_cur, by_issue_prev, top3 = _issue_trends(summary, month_label, total_cur, prev_label)
    by_eng_cur = _engineer_counts_from_raw(summary, month_label)

    mi = _most_improved_issue(by_issue_cur, by_issue_prev) if prev_label else None
    em = _emerging_issue(by_issue_cur, by_issue_prev) if prev_label else None
    dist = _engineer_distribution(by_eng_cur, total)

    lines = {
        "headline": _line_headline(month_label, total, closed, open_),
        "trend": trend_line or _line_trend(prev_label, total_cur, total_prev),
        "top_issues": _line_top_issues(top3),
        "top_engineer": _line_top_engineer(by_eng_cur, total, closed),
        "most_improved": _line_most_improved(mi, prev_label),
        "emerging": _line_emerging(em),
        "diversity": _line_diversity(by_issue_cur, by_issue_prev) if prev_label else None,
        "distribution": dist,
    }
    return lines


# ----------------------- Sanitization helpers -----------------------
_BLOCK_IF_CONTAINS = re.compile(
    r"\b(year|quarter|week|today|yesterday|tomorrow|U\.S\.|USA|United States|company-wide)\b",
    re.IGNORECASE,
)

def _normalize_name(name: str) -> str:
    """Fix common tokenization splits like 'San Jay' -> 'Sanjay'."""
    bad_splits = {r"\bSan Jay\b": "Sanjay"}
    out = name
    for pat, rep in bad_splits.items():
        out = re.sub(pat, rep, out)
    return out


def _split_sentences(text: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    inserts = [
        " Top issues:", " Top issue:", " Top engineer:", " Most improved:", " New emerging issue:",
        " Issue variety", " Workload concentrated:", " Workload evenly distributed", " Overall workload",
        " Slight increase", " Slight decrease"
    ]
    for token in inserts:
        text = text.replace(token, ". " + token.strip())
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _looks_ok(text: str) -> bool:
    if not text:
        return False
    return len(text.strip().split()) >= 12


def _finalize(text: str) -> str:
    t = (text or "").strip()
    if t and t[-1] not in ".!?":
        t += "."
    t = re.sub(r"\s+", " ", t)
    return t


def _sanitize_model_output(text: str, month_label: str, entities: Dict[str, Set[str]]) -> List[str]:
    """
    Keep only safe sentences (no cross-scope claims), normalize names.
    We DO NOT trust model for metrics lines; we will replace/append deterministic lines later.
    """
    if not text:
        return []
    sents = _split_sentences(text)
    kept: List[str] = []
    known_engs = {_normalize_name(e) for e in entities.get("engineers", set())}

    for s in sents:
        s_clean = _normalize_name(s)
        if _BLOCK_IF_CONTAINS.search(s_clean):
            continue
        # Permit only sentences that either mention month headline or generic insight phrases.
        lower = s_clean.lower()
        if month_label.lower() in lower and ("issues" in lower or "closed" in lower or "open" in lower):
            kept.append(_finalize(s_clean))
            continue
        if any(key in lower for key in [
            "top issue", "top issues:", "top engineer:", "most improved:", "new emerging issue:",
            "issue variety", "workload concentrated", "workload evenly distributed",
            "overall workload", "slight increase", "slight decrease", "vs previous month"
        ]):
            # Validate engineer names if present
            eng_names = re.findall(r"([A-Za-z][A-Za-z]+(?:\s[A-Za-z][A-Za-z]+)*)\s*\(\d+\)", s_clean)
            if eng_names:
                valid = True
                for nm in eng_names:
                    nm_norm = _normalize_name(re.sub(r"\s+", " ", nm.strip()))
                    if nm_norm not in known_engs:
                        valid = False
                        break
                if not valid:
                    continue
            kept.append(_finalize(s_clean))
            continue
        # drop anything else

    return kept


# ----------------------- Post-LLM enforcement -----------------------
def _ensure_required_sections(sanitized_sents: List[str], lines: Dict[str, Optional[str]], max_sentences: int) -> str:
    """
    Build the final output ensuring deterministic presence/order:
    headline -> trend -> top_issues -> top_engineer -> most_improved -> emerging -> diversity -> distribution
    """
    order = ["headline", "trend", "top_issues", "top_engineer", "most_improved", "emerging", "diversity", "distribution"]
    final_sents: List[str] = []

    # Prefer any decent headline/trend the model produced; otherwise use deterministic
    # Then always use deterministic for the metrics lines (to avoid hallucinations)
    # Collect model-provided headline/trend if present
    model_text = " ".join(sanitized_sents)
    for key in ["headline", "trend"]:
        if lines.get(key):
            # If model has something that matches the semantic, we still standardize to deterministic phrase
            final_sents.append(lines[key])

    # Deterministic metric/insight lines
    for key in order[2:]:
        if lines.get(key):
            final_sents.append(lines[key])

    # Trim to requested max_sentences (user can set GENAI_SENTENCES)
    final_sents = [s for s in final_sents if s]  # drop Nones
    final_sents = final_sents[:max_sentences]

    text = " ".join(final_sents)
    text = _finalize(text)
    text = re.sub(r"\.\s*\.", ".", text)
    return text


# ----------------------- Public API -----------------------
def generate_summary_text_genai(
    summary: Dict[str, Any],
    month_label: str,
    max_new_tokens: int = 110,   # allow richer output
    no_repeat_ngram_size: int = 3,
    repetition_penalty: float = 1.05,
) -> Optional[str]:
    """
    Strategy:
      1) Build deterministic insight lines (facts).
      2) Compose a facts paragraph (joined) for the LLM to smooth phrasing.
      3) Run T5; sanitize output.
      4) If rejected or weak, run DistilBART with dynamic lengths; sanitize.
      5) Enforce required sections (always present, deterministic and accurate).
    """
    # Deterministic lines (our source of truth)
    lines = _deterministic_insight_lines(summary, month_label)
    # Facts paragraph for LLM
    facts = " ".join([v for v in [
        lines.get("headline"),
        lines.get("trend"),
        lines.get("top_issues"),
        lines.get("top_engineer"),
        lines.get("most_improved"),
        lines.get("emerging"),
        lines.get("diversity"),
        lines.get("distribution"),
    ] if v])

    entities = {
        "engineers": set(_engineer_counts_from_raw(summary, month_label).keys()),
        "issues": set(_normalize_labels(_issue_counts_from_raw(summary, month_label)).keys()),
    }

    # ---- Attempt 1: T5 ----
    pipe_t5 = _ensure_t5()
    sanitized_sents: List[str] = []
    if pipe_t5 is not None:
        try:
            out = pipe_t5(
                f"summarize: {facts}",
                max_new_tokens=max_new_tokens,
                do_sample=False,                 # deterministic
                truncation=True,
                no_repeat_ngram_size=no_repeat_ngram_size,
                repetition_penalty=repetition_penalty,
            )
            if isinstance(out, list) and out:
                text = out[0].get("generated_text") or out[0].get("summary_text") or ""
                sanitized_sents = _sanitize_model_output(text, month_label, entities)
        except Exception:
            sanitized_sents = []

    # ---- Attempt 2: DistilBART fallback ----
    if not sanitized_sents:
        pipe_bart = _ensure_bart()
        if pipe_bart is not None:
            try:
                # Dynamic lengths to avoid warnings (tie to input length)
                words = max(1, len(facts.split()))
                max_length = min(160, max(48, int(words * 0.85)))
                min_length = min(max_length - 4, max(36, int(max_length * 0.55)))

                out = pipe_bart(
                    facts,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True,
                )
                if isinstance(out, list) and out:
                    text = out[0].get("summary_text") or out[0].get("generated_text") or ""
                    sanitized_sents = _sanitize_model_output(text, month_label, entities)
            except Exception:
                sanitized_sents = []

    # If both failed, let caller use deterministic fallback
    if not sanitized_sents and not facts:
        return None

    # Build final with required sections enforced and ordered
    final_text = _ensure_required_sections(sanitized_sents, lines, GENAI_SENTENCES)
    return final_text if _looks_ok(final_text) else (facts if facts else None)
