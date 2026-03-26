# pxscraper

Query, filter, and retrieve proteomics dataset metadata from [ProteomeXchange](http://www.proteomexchange.org/).

## Overview

`pxscraper` replaces the original Selenium-based web scraper with a clean, API-driven approach using the ProteomeCentral bulk TSV and per-dataset XML endpoints. No browser or ChromeDriver required.

## Commands

| Command            | Status        | Description                                                   |
| ------------------ | ------------- | ------------------------------------------------------------- |
| `pxscraper fetch`  | **Available** | Download the full dataset listing from ProteomeCentral        |
| `pxscraper filter` | **Available** | Filter datasets by species, repository, keywords, dates, etc. |
| `pxscraper lookup` | **Available** | Fetch detailed metadata for specific PXD identifiers          |

## Installation

Requires **Python 3.12+** and [uv](https://pypi.org/project/uv/) for package management.

```bash
git clone https://github.com/LangeLab/pxscraper.git
cd pxscraper
uv sync
```

## Usage

### Fetch all datasets

```bash
# Download full ProteomeXchange listing (~50k datasets)
uv run pxscraper fetch

# Custom output path
uv run pxscraper fetch -o my_datasets.tsv

# Force re-download (bypass cache)
uv run pxscraper fetch --refresh

# Verbose output
uv run pxscraper fetch -v
```

The output TSV has the following columns:

| Column          | Description                                             |
| --------------- | ------------------------------------------------------- |
| `dataset_id`    | ProteomeXchange identifier (e.g. PXD063194)             |
| `title`         | Dataset title                                           |
| `repository`    | Hosting repository (PRIDE, MassIVE, jPOST, iProX, etc.) |
| `species`       | Species name(s)                                         |
| `instrument`    | Instrument type(s)                                      |
| `publication`   | Associated publication(s)                               |
| `lab_head`      | Lab head / PI                                           |
| `announce_date` | Date the dataset was announced                          |
| `keywords`      | Dataset keywords                                        |

### Caching

Fetched data is cached locally in `.pxscraper_cache/` (in the current directory) for 24 hours. Subsequent runs use the cache for instant results. Use `--refresh` to force a fresh download, or `--cache-dir` to specify an alternative cache location.

### Filter datasets

```bash
# Filter by species (regex)
uv run pxscraper filter -s "Homo sapiens"

# Filter by repository
uv run pxscraper filter -r "PRIDE,MassIVE"

# Filter by keywords (searched in title and keywords columns)
uv run pxscraper filter -k "cancer,proteomics"

# Filter by date range
uv run pxscraper filter --after 2024-01-01 --before 2024-12-31

# Filter by instrument (regex)
uv run pxscraper filter --instrument "Orbitrap|timsTOF"

# Combine multiple filters
uv run pxscraper filter -s "Homo sapiens" -r PRIDE -k "cancer" --after 2024-01-01

# Use a keyword file (one keyword per line)
uv run pxscraper filter -k keywords.txt

# Filter from a previously fetched file
uv run pxscraper filter -i px_datasets.tsv -s "Mus musculus" -o mouse_datasets.tsv

# Search specific columns for keywords
uv run pxscraper filter -k "brain" --keyword-columns "title"

# Deep search — also search within dataset descriptions/abstracts (fetches XML)
uv run pxscraper filter -k "phosphoproteomics" --deep

# Deep search with species pre-filter to minimise XML requests
uv run pxscraper filter -s "Homo sapiens" -k "ubiquitylation" --deep

# Deep search with confirmation prompt skipped
uv run pxscraper filter -k "glycoproteomics" --deep --yes
```

When no `--input` is given, `filter` automatically uses cached data or downloads fresh data from ProteomeCentral.

### `pxscraper lookup` — fetch detailed XML metadata for specific datasets

```bash
# Look up one or more IDs by flag
uv run pxscraper lookup --ids PXD000001

# Multiple IDs (comma-separated)
uv run pxscraper lookup --ids PXD000001,PXD000002,PXD000003

# Read IDs from a file (one per line)
uv run pxscraper lookup --ids-file my_ids.txt

# Pipeline: feed filter output directly into lookup
uv run pxscraper filter -s "Homo sapiens" -o filtered.tsv
uv run pxscraper lookup --input filtered.tsv -o detailed.tsv

# Skip confirmation prompt (useful in scripts)
uv run pxscraper lookup --ids PXD000001 --yes

# Custom request delay (default: 1.0 s)
uv run pxscraper lookup --ids PXD000001 --delay 2.0

# Custom cache directory
uv run pxscraper lookup --ids PXD000001 --cache-dir /data/cache
```

`lookup` outputs a TSV with one row per dataset containing 19 fields: `dataset_id`, `title`, `description`, `species`, `instruments`, `modifications`, `keywords`, `review_level`, `announce_date`, `repository`, `submitter_name`, `submitter_email`, `submitter_affiliation`, `lab_head_name`, `lab_head_email`, `lab_head_affiliation`, `pubmed_ids`, `dois`, and `ftp_location`.

XML files are cached on disk so repeated lookups do not re-download data. Remove `.pxscraper_cache/PXD*.xml` to force a fresh fetch.

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests (228 tests)
uv run pytest

# Run tests with coverage
uv run pytest --cov=pxscraper --cov-report=term-missing

# Lint
uv run ruff check src/ tests/

# Format check
uv run ruff format --check src/ tests/
```

## Project structure

```bash
src/pxscraper/
├── __init__.py      # Package version
├── cli.py           # Click CLI entry point
├── api.py           # ProteomeCentral API client (polite User-Agent, rate-limited)
├── parse.py         # TSV + XML parsing (HTML stripping, column mapping)
├── cache.py         # Local caching with staleness check
├── models.py        # Column names, constants, configuration
└── filter.py        # DataFrame filtering logic (Phase 2)
```

## Legacy

The original single-file Selenium scraper is preserved in `legacy/proteomeXchange_scraper.py` for reference.

## License

MIT License. See [LICENSE](LICENSE) for details.
