"""Read the AlgoWiki workbook, clean the Quantum Algorithms + Problems sheets,
and emit cached JSON/CSV files into ``data/processed/``.

Inspired by ``data/converter.py`` in dtontici/parallel-algorithms: rename the
verbose spreadsheet columns to short snake_case keys, drop rows we cannot use,
type-cast year/numeric columns, and write out two analysis-ready files plus
their CSV mirrors. Plot scripts then load from these caches, never from the
raw .xlsx, so the pipeline is fast and reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from .header import (
    PROBLEMS_CSV,
    PROBLEMS_JSON,
    PROBLEMS_SHEET,
    QUANTUM_CSV,
    QUANTUM_JSON,
    QUANTUM_SHEET,
    XLSX_PATH,
)

# ---------------------------------------------------------------------------
# Column renames
# ---------------------------------------------------------------------------
QUANTUM_FIELDS = {
    "Family Name": "family",
    "Variation": "variation",
    "Algorithm Name": "algorithm",
    "Year": "year",
    "Time Complexity Class": "time_class",
    "Time Complexity / Circuit Depth (Worst Only)": "time_expr",
    "Time Encoding": "time_encoding",
    "Space Complexity Class": "space_class",
    "Space (QBit) Complexity (Auxiliary)": "space_expr",
    "Looked at?": "looked_at",
    "Approximate?": "approximate",
    "Heuristic-based?": "heuristic",
    "Randomized?": "randomized",
    "Computational Model": "model",
    "Authors": "authors",
    "Title": "title",
    "Paper/Reference Link": "paper_url",
    "DOI": "doi",
    "Algorithm Description": "description",
    "Remarks": "remarks",
}

PROBLEMS_FIELDS = {
    "Old Family #": "family_id",
    "Family Name": "family",
    "Variation": "variation",
    "Alias": "alias",
    "Parents": "parents",
    "Children": "children",
    "Problem Description": "description",
    "Parameters": "parameters",
    "Best Known Upper Bound": "upper_bound",
    "Best Known Lower Bound": "lower_bound",
    "Domain": "domain",
}

# Numeric columns we want to cast inside each table
QUANTUM_NUMERIC = ["year", "time_class", "space_class",
                   "looked_at", "approximate", "heuristic", "randomized"]
PROBLEMS_NUMERIC = ["family_id"]

# A row in `Quantum Algorithms` is treated as "excluded" if `looked_at` is in
# this set (matches the AlgoWiki convention: 0.001 = explicitly removed).
EXCLUDED_LOOKED_AT = {0.001}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _select_and_rename(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Keep only known columns and rename them to short keys."""
    keep = [c for c in mapping if c in df.columns]
    out = df[keep].copy()
    out.columns = [mapping[c] for c in keep]
    return out


def _coerce_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _strip_strings(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace({"nan": None, "": None})
    return df


def _normalize_family(s: pd.Series) -> pd.Series:
    """Standardize family names so case/spacing differences don't break joins.
    Capitalizes each word; trims internal whitespace.
    """
    return (
        s.fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.title()
        .replace({"": None})
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_quantum_algorithms(xlsx_path: Path | None = None) -> pd.DataFrame:
    """Read + clean the ``Quantum Algorithms`` sheet."""
    df = pd.read_excel(xlsx_path or XLSX_PATH, sheet_name=QUANTUM_SHEET)
    df = _select_and_rename(df, QUANTUM_FIELDS)
    df = _coerce_numeric(df, QUANTUM_NUMERIC)
    df = _strip_strings(df)

    # Drop entries flagged as removed in the source sheet
    if "looked_at" in df.columns:
        mask = ~df["looked_at"].isin(EXCLUDED_LOOKED_AT)
        df = df[mask].copy()

    # Drop rows missing a family or year - they cannot be plotted on a timeline
    df = df.dropna(subset=["family", "year"]).copy()
    df["year"] = df["year"].astype(int)

    df["family"] = _normalize_family(df["family"])

    # Treat blank Variation as the family itself (so the (family, variation) key
    # is always populated). This matches how the Problems sheet stores it for
    # families with a single canonical variant (e.g. Sorting / Sorting).
    df["variation"] = df["variation"].fillna(df["family"])

    df = df.reset_index(drop=True)
    return df


def load_problems(xlsx_path: Path | None = None) -> pd.DataFrame:
    """Read + clean the ``Problems`` sheet."""
    df = pd.read_excel(xlsx_path or XLSX_PATH, sheet_name=PROBLEMS_SHEET)
    df = _select_and_rename(df, PROBLEMS_FIELDS)
    df = _coerce_numeric(df, PROBLEMS_NUMERIC)
    df = _strip_strings(df)
    df = df.dropna(subset=["family"]).copy()
    df["family"] = _normalize_family(df["family"])
    df["variation"] = df["variation"].fillna(df["family"])
    df = df.reset_index(drop=True)
    return df


def build_processed_dataset(xlsx_path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build both cleaned tables and persist them as JSON + CSV."""
    qdf = load_quantum_algorithms(xlsx_path)
    pdf = load_problems(xlsx_path)

    qdf.to_csv(QUANTUM_CSV, index=False, encoding="utf-8")
    pdf.to_csv(PROBLEMS_CSV, index=False, encoding="utf-8")

    QUANTUM_JSON.write_text(
        json.dumps(qdf.to_dict(orient="records"), indent=2, default=str),
        encoding="utf-8",
    )
    PROBLEMS_JSON.write_text(
        json.dumps(pdf.to_dict(orient="records"), indent=2, default=str),
        encoding="utf-8",
    )

    return qdf, pdf


def get_quantum_algorithms() -> pd.DataFrame:
    """Load the cached cleaned dataset, building it on first access."""
    if not QUANTUM_JSON.exists():
        build_processed_dataset()
    return pd.read_csv(QUANTUM_CSV)


def get_problems() -> pd.DataFrame:
    if not PROBLEMS_JSON.exists():
        build_processed_dataset()
    return pd.read_csv(PROBLEMS_CSV)


if __name__ == "__main__":
    qdf, pdf = build_processed_dataset()
    print(f"Quantum Algorithms: {len(qdf)} rows  ->  {QUANTUM_JSON.name}, {QUANTUM_CSV.name}")
    print(f"Problems          : {len(pdf)} rows  ->  {PROBLEMS_JSON.name}, {PROBLEMS_CSV.name}")
