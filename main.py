#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Pipeline: Specialty → NUCC Taxonomy Mapper
------------------------------------------------
Steps:
1. Preprocess raw specialties → (processed, is_junk)
2. Map processed specialties → NUCC taxonomy codes (skip junk)
3. Merge and write final CSV
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

    # --- Step 1: Preprocessing ---
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

    # --- Step 2.5: Handle duplicate raw_specialty entries safely ---
    if df_map["raw_specialty"].duplicated().any():
        print("⚠️  Duplicates found in mapped data — aggregating results...")
        df_map = (
            df_map.groupby("raw_specialty", as_index=False)
            .agg({
                "mapped_code": lambda x: "|".join(sorted(set(x))),
                "confidence": "mean",
                "explain": lambda x: "; ".join(set(x))[:250],
            })
        )

    # --- Step 3: Merge results ---
    df_pre["__row_id__"] = range(len(df_pre))
    df_final = (
        df_pre
        .merge(df_map, on="raw_specialty", how="left", sort=False)
        .sort_values("__row_id__")
        .drop(columns="__row_id__")
        .reset_index(drop=True)
    )

    # Rename mapped_code → nucc_codes
    df_final.rename(columns={"mapped_code": "nucc_codes"}, inplace=True)

    # Fill missing mappings for junk specialties
    df_final = df_final.assign(
        nucc_codes=df_final["nucc_codes"].fillna("JUNK"),
        confidence=df_final["confidence"].fillna(0.0),
        explain=df_final["explain"].fillna("junk-flagged")
    )

    # --- Step 4: Save output ---
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(args.out, index=False)

    print(f"✅ Wrote final mapped file → {args.out}")
    print("📄 Columns: raw_specialty, processed, is_junk, nucc_codes, confidence, explain")


if __name__ == "__main__":
    main()
