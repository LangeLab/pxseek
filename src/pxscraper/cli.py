"""CLI entry point for pxscraper."""

import re
from datetime import datetime
from pathlib import Path

import click

from pxscraper import __version__


def _fetch_summary_safe(verbose=False):
    """Fetch summary TSV from ProteomeCentral with friendly error handling."""
    import requests

    from pxscraper import api

    try:
        if verbose:
            click.echo("Downloading dataset listing from ProteomeCentral...")
        return api.fetch_summary()
    except requests.ConnectionError:
        raise click.ClickException(
            "Could not reach ProteomeCentral. Check your network connection."
        )
    except requests.Timeout:
        raise click.ClickException(
            "Request to ProteomeCentral timed out. Try again later."
        )
    except requests.HTTPError as exc:
        raise click.ClickException(f"ProteomeCentral returned an error: {exc}")


@click.group()
@click.version_option(version=__version__, prog_name="pxscraper")
def main():
    """Query, filter, and retrieve proteomics dataset metadata from ProteomeXchange."""


@main.command()
@click.option("-o", "--output", default="px_datasets.tsv", help="Output file path.")
@click.option(
    "--cache-dir",
    default=None,
    type=click.Path(),
    help="Cache directory [default: .pxscraper_cache/ in cwd].",
)
@click.option("--refresh", is_flag=True, help="Force re-download even if cached.")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def fetch(output, cache_dir, refresh, verbose):
    """Download the full ProteomeXchange dataset listing."""
    from pxscraper import cache, parse

    cache_base = Path(cache_dir) if cache_dir else None
    cdir = cache.get_cache_dir(cache_base)

    # Check cache
    if not refresh and not cache.is_stale("summary", cache_dir=cdir):
        df = cache.load("summary", cache_dir=cdir)
        info = cache.cache_info("summary", cache_dir=cdir)
        if df is not None:
            click.echo(f"Using cached data ({info['rows']} datasets, from cache in {cdir})")
            df.to_csv(output, sep="\t", index=False)
            click.echo(f"Wrote {len(df)} datasets to {output}")
            return

    # Fetch from API
    raw_tsv = _fetch_summary_safe(verbose)

    if verbose:
        click.echo("Parsing TSV...")
    result = parse.parse_summary_tsv(raw_tsv)
    df = result.df

    # Report parse diagnostics
    if result.skipped_count > 0:
        click.echo(
            f"Parsed {len(df)} datasets ({result.skipped_count} malformed row(s) skipped)"
        )
        if verbose:
            for line_num in result.skipped_lines:
                click.echo(f"  skipped line {line_num}")
    else:
        if verbose:
            click.echo(f"Parsed {len(df)} datasets (no rows skipped)")

    # Save to cache
    cache.save(df, "summary", cache_dir=cdir)
    if verbose:
        click.echo(f"Cached {len(df)} datasets in {cdir}")

    # Write output
    df.to_csv(output, sep="\t", index=False)
    click.echo(f"Fetched {len(df)} datasets -> {output}")


@main.command()
@click.option("-i", "--input", "input_file", default=None, help="Input TSV from fetch.")
@click.option("-o", "--output", default="filtered_datasets.tsv", help="Output file path.")
@click.option("-s", "--species", default=None, help="Filter by species (regex).")
@click.option("-r", "--repo", default=None, help="Filter by repository (e.g. PRIDE,MassIVE).")
@click.option(
    "-k", "--keywords", default=None, help="Comma-separated keywords or path to keyword file."
)
@click.option(
    "--after", default=None, help="Include datasets on or after DATE (YYYY-MM-DD).",
)
@click.option(
    "--before", default=None, help="Include datasets on or before DATE (YYYY-MM-DD).",
)
@click.option("--instrument", default=None, help="Filter by instrument (regex).")
@click.option(
    "--keyword-columns",
    default=None,
    help="Columns to search for keywords (comma-separated) [default: title,keywords].",
)
@click.option(
    "--cache-dir",
    default=None,
    type=click.Path(),
    help="Cache directory [default: .pxscraper_cache/ in cwd].",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def filter(input_file, output, species, repo, keywords, after, before,
           instrument, keyword_columns, cache_dir, verbose):
    """Filter ProteomeXchange datasets by species, repo, keywords, dates, etc."""
    from pxscraper import cache, parse
    from pxscraper import filter as filt

    # --- Validate user-supplied regex patterns ---
    for name, pattern in [("species", species), ("instrument", instrument)]:
        if pattern:
            try:
                re.compile(pattern)
            except re.error as e:
                raise click.ClickException(f"Invalid regex for --{name}: {e}")

    # --- Validate date format ---
    for opt_name, date_str in [("after", after), ("before", before)]:
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise click.ClickException(
                    f"Invalid date for --{opt_name}: {date_str!r} (expected YYYY-MM-DD)"
                )
    if after and before:
        if datetime.strptime(after, "%Y-%m-%d") > datetime.strptime(before, "%Y-%m-%d"):
            raise click.ClickException(
                f"--after ({after}) cannot be later than --before ({before})"
            )

    # --- Load input data ---
    if input_file:
        import pandas as pd

        if verbose:
            click.echo(f"Reading input from {input_file}")
        df = pd.read_csv(input_file, sep="\t", dtype=str)
    else:
        # Auto-fetch: use cache or download
        cache_base = Path(cache_dir) if cache_dir else None
        cdir = cache.get_cache_dir(cache_base)

        df = None
        if not cache.is_stale("summary", cache_dir=cdir):
            df = cache.load("summary", cache_dir=cdir)
            if df is not None and verbose:
                info = cache.cache_info("summary", cache_dir=cdir)
                click.echo(f"Using cached data ({info['rows']} datasets)")

        if df is None:
            raw_tsv = _fetch_summary_safe(verbose)

            result = parse.parse_summary_tsv(raw_tsv)
            df = result.df
            cache.save(df, "summary", cache_dir=cdir)
            if verbose:
                click.echo(f"Fetched and cached {len(df)} datasets")

    # --- Check we have at least one filter ---
    has_filter = any([species, repo, keywords, after, before, instrument])
    if not has_filter:
        raise click.ClickException(
            "No filters specified. Use -s, -r, -k, --after, --before, or --instrument."
        )

    # --- Warn about unknown keyword-columns ---
    if keyword_columns:
        cols = [c.strip() for c in keyword_columns.split(",") if c.strip()]
        for col in cols:
            if col not in df.columns:
                click.echo(f"Warning: column '{col}' not found in data, ignored.", err=True)

    # --- Apply filters ---
    filtered_df, summary = filt.apply_filters(
        df,
        species=species,
        repository=repo,
        keywords=keywords,
        keyword_columns=keyword_columns,
        after=after,
        before=before,
        instrument=instrument,
    )

    # --- Report ---
    filters_str = "; ".join(summary["active_filters"])
    click.echo(
        f"Filtered {summary['original_count']} -> {summary['filtered_count']} datasets "
        f"({filters_str})"
    )

    if summary["filtered_count"] == 0:
        click.echo("No datasets matched the given filters.")
        return

    # --- Write output ---
    filtered_df.to_csv(output, sep="\t", index=False)
    click.echo(f"Wrote {summary['filtered_count']} datasets to {output}")


@main.command()
@click.option("--ids", default=None, help="Comma-separated PXD IDs.")
@click.option(
    "--ids-file", default=None, type=click.Path(exists=True),
    help="File with one PXD ID per line.",
)
@click.option("-o", "--output", default=None, help="Output file path (default: stdout).")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def lookup(ids, ids_file, output, verbose):
    """Fetch detailed metadata for specific PXD identifiers."""
    click.echo("lookup command not yet implemented (see plan.md for Phase 3)")
