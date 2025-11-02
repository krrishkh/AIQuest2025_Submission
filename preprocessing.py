#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Preprocess provider specialties into mapping-ready text and flag JUNK.

NO HARDCODED SYNONYMS — all expansions are read from your synonyms file.

Output columns: raw_specialty, processed, is_junk (1/0)
"""

import re
import csv
import argparse
from html import unescape
from typing import Tuple, Dict, List, Optional
from pathlib import Path

import pandas as pd


def load_synonyms(path: str) -> Dict[str, str]:
    """
    Load a synonyms CSV with columns: type,pattern,replacement.
    Uses ONLY rows where type ∈ {abbreviation, synonym}.
    Returns a dict mapping normalized pattern -> normalized replacement.
    """
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Synonyms file not found: {path}")
    out: Dict[str, str] = {}
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            typ = (r.get("type") or "").strip().lower()
            pat = (r.get("pattern") or "").strip().lower()
            rep = (r.get("replacement") or "").strip().lower()
            if typ in {"abbreviation", "synonym"} and pat and rep and pat != rep:
                out[_norm(pat)] = _norm(rep)
    return out


def _fix_mojibake(s: str) -> str:
    replacements = {
        "Ã¢â‚¬â€œ": "",
        "ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“": "",
        "Ã¢â‚¬": "",
        "Â": "",
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)
    return unescape(s)


def _norm(s: str) -> str:
    s = (s or "").strip()
    s = _fix_mojibake(s)
    s = s.replace("\u00A0", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def _to_lower_tokens(s: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t]


class PreprocessSpecialty:
    """
    Cleans raw specialty strings and applies ONLY file-driven synonyms.
    - numbers→letters inside words
    - whitespace/case/punctuation normalization
    - multi-specialty connectors normalized to " / "
    - noise stripping (dept/clinic/geo/honorifics)
    - parentheses flattened
    - HTML entities + common mojibake fix
    - NUCC code passthrough (e.g., 207RC0000X)
    - junk detection (placeholders, clearly non-medical)
    """

    PLACEHOLDERS = {
        "tbd", "temporary", "unknown", "n/a", "na", "none", "no data", "random data",
        "unk", "-", "", "####", "n a", "n.a.", "nil", "null"
    }
    NON_MEDICAL = {
        "taxi", "ambulance", "driver", "contractor", "agency", "public", "sector",
        "admin", "accounts", "billing"
    }
    ORG_NOISE = {
        "dept", "department", "division", "program", "service", "center", "centre",
        "unit", "office", "hospital", "clinic", "outpatient", "inpatient", "opd",
        "ed", "er"
    }
    GEO_NOISE = {"usa", "us", "united", "states", "india", "canada", "uk", "united kingdom"}
    HONORIFICS = {"dr", "mr", "mrs", "ms", "prof", "md."}
    DIGIT_LETTER = str.maketrans({"0": "o", "1": "i", "3": "e", "5": "s", "7": "t", "8": "b"})
    NUCC_CODE_RE = re.compile(r"\b[0-9A-Z]{9}X\b", re.I)
    PARENS_RE = re.compile(r"\(([^)]+)\)")

    def __init__(self, synonyms_map: Dict[str, str]):
        """
        synonyms_map: normalized pattern -> normalized replacement (from your CSV)
        """
        self.syn_map = dict(synonyms_map)
        # Precompile phrase patterns (multiword first) for boundary-safe replacement
        pats = sorted(self.syn_map.keys(), key=len, reverse=True)
        self._regexes: List[Tuple[re.Pattern, str]] = []
        for pat in pats:
            escaped = re.escape(pat)
            rx = re.compile(rf"(?<!\w){escaped}(?!\w)")
            self._regexes.append((rx, self.syn_map[pat]))

    def _digits_to_letters(self, s: str) -> str:
        def repl(m):
            word = m.group(0)
            if re.search(r"[0-9]", word):
                return word.translate(self.DIGIT_LETTER)
            return word
        return re.sub(r"[A-Za-z0-9]+", repl, s)

    def _strip_noise_tokens(self, s: str) -> str:
        toks = _to_lower_tokens(s)
        kept = []
        for t in toks:
            if t in self.HONORIFICS:  continue
            if t in self.ORG_NOISE:   continue
            if t in self.GEO_NOISE:   continue
            kept.append(t)
        return " ".join(kept)

    def _standardize_separators(self, s: str) -> str:
        s = re.sub(r"\s*&\s*", " / ", s)
        s = re.sub(r"\s*\+\s*", " / ", s)
        s = re.sub(r"\s*(,|;)\s*", " / ", s)
        s = re.sub(r"\s*/\s*", " / ", s)
        s = re.sub(r"\band\b", " / ", s, flags=re.I)
        s = re.sub(r"( / )+", " / ", s)
        return s

    def _clean_parentheses(self, s: str) -> str:
        s = self.PARENS_RE.sub(lambda m: " " + m.group(1), s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _normalize_punct_case(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[-–—]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _apply_synonyms(self, s: str) -> str:
        if not self._regexes:
            return s
        out = s
        for rx, repl in self._regexes:
            out = rx.sub(repl, out)
        out = re.sub(r"\s+", " ", out).strip()
        return out

    def _select_primary_text(self, s: str) -> str:
        m = self.NUCC_CODE_RE.search(s.upper())
        if m:
            return m.group(0).upper()
        return s

    def _is_placeholder_or_empty(self, s: str) -> bool:
        return s.lower() in self.PLACEHOLDERS or s.strip() == ""

    def _is_non_medical(self, s: str) -> bool:
        toks = _to_lower_tokens(s)
        if not toks:
            return True
        nm = sum(t in self.NON_MEDICAL for t in toks)
        med_hint = any(t in {
            "medicine","surgery","cardiology","neurology","dermatology","radiology","oncology",
            "pediatrics","psychiatry","pathology","anesthesiology","urology","nephrology",
            "endocrinology","gastroenterology","hematology","ophthalmology","otolaryngology",
            "rehabilitation","genetics","rheumatology","pulmonology"
        } for t in toks)
        return bool(nm and not med_hint)

    def process_one(self, raw: str) -> Tuple[str, int]:
        orig = "" if pd.isna(raw) else str(raw)
        s = _norm(orig)
        if self._is_placeholder_or_empty(s):
            return ("junk", 1)
        s = self._clean_parentheses(s)
        s = self._digits_to_letters(s)
        s = self._strip_noise_tokens(s)
        if not s:
            return ("junk", 1)
        s = self._standardize_separators(s)
        s = self._normalize_punct_case(s)
        s = self._apply_synonyms(s)  # ONLY file-driven synonyms here
        s = re.sub(r"\s+", " ", s).strip()
        s = self._select_primary_text(s)
        if self._is_non_medical(s) or len(re.sub(r"[^a-zA-Z]+", "", s)) < 3:
            return (s if s else "junk", 1)
        return (s, 0)

    def process_dataframe(self, df: pd.DataFrame, col_guess: Optional[str] = None) -> pd.DataFrame:
        if col_guess is None:
            candidates = [c for c in df.columns
                          if re.search(r"(special|dept|discipline|service|category|name)", c, re.I)]
            col_guess = candidates[0] if candidates else df.columns[0]
        rows = []
        for raw in df[col_guess].astype(str).tolist():
            processed, junk = self.process_one(raw)
            rows.append((raw, processed, junk))
        return pd.DataFrame(rows, columns=["raw_specialty", "processed", "is_junk"])


def detect_input_column(df: pd.DataFrame) -> str:
    cands = [c for c in df.columns
             if re.search(r"(special|dept|discipline|service|category|name)", c, re.I)]
    return cands[0] if cands else df.columns[0]


def main():
    ap = argparse.ArgumentParser(description="Preprocess provider specialties (synonyms only from file).")
    ap.add_argument("--input", required=True, help="Path to input_specialties.csv")
    ap.add_argument("--out", required=True, help="Path to write preprocessed_specialties.csv")
    ap.add_argument("--synonyms", required=True, help="Path to synonyms CSV (type,pattern,replacement)")
    args = ap.parse_args()

    syn = load_synonyms(args.synonyms)
    pre = PreprocessSpecialty(synonyms_map=syn)

    df_in = pd.read_csv(args.input)
    col = detect_input_column(df_in)
    df_out = pre.process_dataframe(df_in, col_guess=col)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.out, index=False)
    print(f"Wrote {len(df_out)} rows to {args.out}")
    print("Columns: raw_specialty, processed, is_junk")


if __name__ == "__main__":
    main()
