#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NUCC Specialty Mapper (Clean Version)
------------------------------------
Maps raw specialty text to NUCC taxonomy codes using:
  1) Synonym expansion
  2) Exact / Token overlap
  3) Fuzzy match
Returns multiple codes if ambiguous; marks as JUNK if below threshold.
"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from collections import Counter

try:
    from rapidfuzz import process, fuzz
    USE_RAPIDFUZZ = True
except ImportError:
    from difflib import SequenceMatcher, get_close_matches
    USE_RAPIDFUZZ = False


def normalize(text: str) -> str:
    """Clean and lowercase input text."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s/&+,-]", " ", text)
    text = re.sub(r"\b(dept|department|clinic|division|program|service|center|centre|unit|office)\b", " ", text)
    text = re.sub(r"\b(of|for|and|the)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_specialties(text: str) -> List[str]:
    """Split multi-specialty string into individual specialties."""
    parts = re.split(r"\s*[|,/;&+]\s*| and ", text)
    return [p.strip() for p in parts if p.strip()]


def token_overlap(a: str, b: str) -> float:
    """Compute token-level overlap between two phrases."""
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


class NuccSpecialtyMapper:
    def __init__(self, nucc_df: pd.DataFrame, synonyms: Dict[str, str], threshold: float = 0.65):
        """
        nucc_df columns: code, classification, specialization, display_name
        synonyms: mapping of abbreviations/synonyms to canonical forms
        """
        self.df = nucc_df.copy()
        self.synonyms = {k.lower(): v.lower() for k, v in synonyms.items()}
        self.threshold = threshold

        # Canonical phrase for each NUCC entry
        self.df["canonical"] = self.df.apply(
            lambda r: (r.get("display_name") or f"{r.get('classification','')} {r.get('specialization','')}").strip().lower(),
            axis=1
        )
        self.df["canonical"] = self.df["canonical"].map(normalize)
        self.canonicals = self.df["canonical"].tolist()

    def expand_synonyms(self, text: str) -> str:
        words = text.split()
        expanded = [self.synonyms.get(w, w) for w in words]
        return " ".join(expanded)

    def exact_match(self, query: str) -> List[Tuple[str, float, str]]:
        hits = self.df[self.df["canonical"] == query]
        return [(r.code, 1.0, "exact") for _, r in hits.iterrows()]

    def token_match(self, query: str) -> List[Tuple[str, float, str]]:
        res = []
        for _, r in self.df.iterrows():
            score = token_overlap(query, r["canonical"])
            if score >= 0.7:
                res.append((r.code, score, f"token_overlap:{score:.2f}"))
        return res

    def fuzzy_match(self, query: str) -> List[Tuple[str, float, str]]:
        res = []
        if USE_RAPIDFUZZ:
            matches = process.extract(query, self.canonicals, scorer=fuzz.token_sort_ratio, limit=10)
            for phrase, score, _ in matches:
                score_n = score / 100.0
                if score_n >= 0.75 and token_overlap(query, phrase) > 0:
                    code = self.df.loc[self.df["canonical"] == phrase, "code"].iloc[0]
                    res.append((code, score_n, f"fuzzy:{score_n:.2f}"))

        else:
            for _, r in self.df.iterrows():
                score = SequenceMatcher(None, query, r["canonical"]).ratio()
                if score >= 0.8:
                    res.append((r.code, score, f"fuzzy:{score:.2f}"))
        return res

    def map_one(self, text: str) -> Tuple[List[str], float, str]:
        q = normalize(self.expand_synonyms(text))
        if not q:
            return ([], 0.0, "empty")

        candidates = []
        candidates += self.exact_match(q)
        candidates += self.token_match(q)
        candidates += self.fuzzy_match(q)

        if not candidates:
            return ([], 0.0, "no match")

        # Aggregate by best score per code
        best = {}
        for code, score, why in candidates:
            if code not in best or score > best[code][0]:
                best[code] = (score, why)
        merged = sorted(best.items(), key=lambda x: x[1][0], reverse=True)

        top_code, top_score, reason = merged[0][0], merged[0][1][0], merged[0][1][1]
        if top_score < self.threshold:
            return ([], top_score, "junk-low-confidence")
        return ([top_code], top_score, reason)

    def map_text(self, text: str) -> Tuple[List[str], float, str]:
        parts = split_specialties(normalize(text))
        all_codes = Counter()
        confs, reasons = [], []
        for p in parts:
            codes, conf, why = self.map_one(p)
            for c in codes:
                all_codes[c] += 1
            confs.append(conf)
            reasons.append(f"[{p}]→{','.join(codes) or 'none'}({conf:.2f})")
        if not all_codes:
            return ([], 0.0, "; ".join(reasons))
        avg_conf = sum(confs) / len(confs)
        top_codes = [c for c, _ in all_codes.most_common(3)]
        return (top_codes, avg_conf, "; ".join(reasons))

    def map_dataframe(self, df: pd.DataFrame, col: str = "raw_specialty") -> pd.DataFrame:
        """
        df: a DataFrame that must include a 'raw_specialty' column (original)
            and a column named by 'col' which is the processed text to map.
        col: column in df that contains processed text to map (default 'raw_specialty').

        Returns DataFrame with columns: raw_specialty, mapped_code, confidence, explain
        where raw_specialty is the original input (so it can be merged back easily).
        """
        rows = []
        # Expect df to have 'raw_specialty' (original) and 'col' (processed)
        if "raw_specialty" in df.columns and col in df.columns and col != "raw_specialty":
            iter_rows = zip(df["raw_specialty"].astype(str), df[col].astype(str))
        else:
            # Fallback: treat the passed column as both original and processed
            iter_rows = zip(df[col].astype(str), df[col].astype(str))

        for raw_orig, proc_val in iter_rows:
            codes, conf, reason = self.map_text(str(proc_val))
            mapped = "|".join(codes) if codes else "JUNK"
            rows.append((raw_orig, mapped, round(conf, 3), reason[:250]))
        return pd.DataFrame(rows, columns=["raw_specialty", "mapped_code", "confidence", "explain"])

