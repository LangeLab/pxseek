"""DataFrame filtering logic.

Pure functions that operate on the summary DataFrame returned by parse_summary_tsv().
Each filter function takes a DataFrame and returns a filtered copy.
"""

import re
from pathlib import Path

import pandas as pd


def by_species(df: pd.DataFrame, pattern: str) -> pd.DataFrame:
    """Filter rows where the species column matches a case-insensitive regex."""
    mask = df["species"].str.contains(pattern, case=False, na=False, regex=True)
    return df[mask].copy()


def by_repository(df: pd.DataFrame, repos: str) -> pd.DataFrame:
    """Filter rows where the repository matches one of the given repos (comma-separated)."""
    repo_list = [r.strip().lower() for r in repos.split(",") if r.strip()]
    mask = df["repository"].str.strip().str.lower().isin(repo_list)
    return df[mask].copy()


def by_keywords(
    df: pd.DataFrame,
    keywords: str,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    r"""Filter rows where any keyword matches in the specified columns.

    Keywords are matched using \b word boundaries, case-insensitive, OR logic.
    If *keywords* is a path to an existing file, reads one keyword per line.
    Otherwise treats *keywords* as a comma-separated string.
    """
    if columns is None:
        columns = ["title", "keywords"]

    # Resolve keyword list: file path or comma-separated
    kw_path = Path(keywords)
    if kw_path.is_file():
        kw_list = [line.strip() for line in kw_path.read_text().splitlines() if line.strip()]
    else:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

    if not kw_list:
        return df.copy()

    pattern = "|".join(rf"\b{re.escape(kw)}\b" for kw in kw_list)

    mask = pd.Series(False, index=df.index)
    for col in columns:
        if col in df.columns:
            mask = mask | df[col].str.contains(pattern, case=False, na=False, regex=True)

    return df[mask].copy()


def by_date_range(
    df: pd.DataFrame,
    after: str | None = None,
    before: str | None = None,
) -> pd.DataFrame:
    """Filter rows by announce_date range (inclusive).

    Dates are parsed with ``pd.to_datetime(errors="coerce")``.
    Rows with unparseable dates (NaT) are excluded from range matches.
    """
    dates = pd.to_datetime(df["announce_date"], format="%Y-%m-%d", errors="coerce")
    mask = dates.notna()

    if after:
        mask = mask & (dates >= pd.to_datetime(after, format="%Y-%m-%d"))
    if before:
        mask = mask & (dates <= pd.to_datetime(before, format="%Y-%m-%d"))

    return df[mask].copy()


def by_instrument(df: pd.DataFrame, pattern: str) -> pd.DataFrame:
    """Filter rows where the instrument column matches a case-insensitive regex."""
    mask = df["instrument"].str.contains(pattern, case=False, na=False, regex=True)
    return df[mask].copy()


def apply_filters(
    df: pd.DataFrame,
    *,
    species: str | None = None,
    repository: str | None = None,
    keywords: str | None = None,
    keyword_columns: str | None = None,
    after: str | None = None,
    before: str | None = None,
    instrument: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Apply all active filters sequentially and return (filtered_df, summary).

    The summary dict contains:
      - original_count: rows before filtering
      - filtered_count: rows after filtering
      - active_filters: list of human-readable filter descriptions
    """
    original_count = len(df)
    active_filters: list[str] = []

    if species:
        df = by_species(df, species)
        active_filters.append(f"species: {species}")

    if repository:
        df = by_repository(df, repository)
        active_filters.append(f"repository: {repository}")

    if keywords:
        cols = [c.strip() for c in keyword_columns.split(",")] if keyword_columns else None
        df = by_keywords(df, keywords, cols)
        active_filters.append(f"keywords: {keywords}")

    if after or before:
        df = by_date_range(df, after, before)
        parts = []
        if after:
            parts.append(f"after {after}")
        if before:
            parts.append(f"before {before}")
        active_filters.append(f"date: {', '.join(parts)}")

    if instrument:
        df = by_instrument(df, instrument)
        active_filters.append(f"instrument: {instrument}")

    summary = {
        "original_count": original_count,
        "filtered_count": len(df),
        "active_filters": active_filters,
    }

    return df, summary
