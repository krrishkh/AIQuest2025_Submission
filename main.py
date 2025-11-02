#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline:
1. Preprocess raw specialties → processed + junk flag.
2. Map processed specialties → NUCC taxonomy codes (skip junk).
"""

import argparse
from pathlib import Path
import pandas as pd

from preprocessing import PreprocessSpecialty, load_synonyms
from mapping import NuccSpecialtyMapper


def main():
    ap = argparse.ArgumentParser(description="Full Specialty → NUCC mapping pipeline")
    ap.add_argument("--input", required=True, help="Input specialties CSV")
    ap.add_argument("--nucc", required=True, help="NUCC taxonomy CSV (with code/classification...)")
    ap.add_argument("--synonyms", required=True, help="Synonyms CSV (type,pattern,replacement)")
    ap.add_argument("--out", required=True, help="Output mapped CSV")
    args = ap.parse_args()

    # --- Step 1: Preprocess ---
    print("🔹 Loading synonyms...")
    syn_map = load_synonyms(args.synonyms)
    pre = PreprocessSpecialty(synonyms_map=syn_map)

    print("🔹 Reading input specialties...")
    df_in = pd.read_csv(args.input)
    df_pre = pre.process_dataframe(df_in)
    print(f"✅ Preprocessed {len(df_pre)} specialties")

    # --- Step 2: NUCC Mapping ---
    print("🔹 Loading NUCC taxonomy...")
    nucc_df = pd.read_csv(args.nucc)
    nucc_df.columns = [c.strip().lower() for c in nucc_df.columns]
    mapper = NuccSpecialtyMapper(nucc_df, synonyms=syn_map)

    print("🔹 Mapping specialties (skipping junk)...")
    df_map_input = df_pre[df_pre["is_junk"] == 0].copy()
    df_map = mapper.map_dataframe(df_map_input, col="processed")

    # --- Step 3: Merge results ---
    print("🔹 Merging results...")
    df_final = df_pre.merge(df_map, on="raw_specialty", how="left")

    # Rename mapped_code → nucc_codes to align with output spec
    df_final.rename(columns={"mapped_code": "nucc_codes"}, inplace=True)

    # Fill missing (junk) mappings
    for col in ["nucc_codes", "confidence", "explain"]:
        if col not in df_final.columns:
            df_final[col] = None

    df_final["nucc_codes"].fillna("JUNK", inplace=True)
    df_final["confidence"].fillna(0.0, inplace=True)
    df_final["explain"].fillna("junk-flagged", inplace=True)

    # --- Step 4: Save output ---
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(args.out, index=False)

    print(f"✅ Wrote final mapped file → {args.out}")
    print("Columns: raw_specialty, processed, is_junk, nucc_codes, confidence, explain")


if __name__ == "__main__":
    main()
