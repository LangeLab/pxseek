"""CLI entry point for pxscraper."""

from pathlib import Path

import click

from pxscraper import __version__


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
    from pxscraper import api, cache, parse

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
    if verbose:
        click.echo("Downloading full dataset listing from ProteomeCentral...")
    raw_tsv = api.fetch_summary()

    if verbose:
        click.echo("Parsing TSV...")
    df = parse.parse_summary_tsv(raw_tsv)

    # Save to cache
    cache.save(df, "summary", cache_dir=cdir)
    if verbose:
        click.echo(f"Cached {len(df)} datasets in {cdir}")

    # Write output
    df.to_csv(output, sep="\t", index=False)
    click.echo(f"Fetched {len(df)} datasets → {output}")


@main.command()
@click.option("-i", "--input", "input_file", default=None, help="Input TSV from fetch.")
@click.option("-o", "--output", default="filtered_datasets.tsv", help="Output file path.")
@click.option("-s", "--species", default=None, help="Filter by species (regex).")
@click.option("-r", "--repo", default=None, help="Filter by repository (e.g. PRIDE,MassIVE).")
@click.option(
    "-k", "--keywords", default=None, help="Comma-separated keywords or path to keyword file."
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output.")
def filter(input_file, output, species, repo, keywords, verbose):
    """Filter ProteomeXchange datasets by species, repo, keywords, etc."""
    click.echo("filter command not yet implemented (see plan.md for Phase 2)")


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
