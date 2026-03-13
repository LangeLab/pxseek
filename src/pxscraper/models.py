"""Column names, constants, and data models."""

import re

# Raw TSV header → clean column name mapping
RAW_TO_CLEAN_COLUMNS = {
    "Dataset Identifier": "dataset_id",
    "Title": "title",
    "Repos": "repository",
    "Species": "species",
    "Instrument": "instrument",
    "Publication": "publication",
    "LabHead": "lab_head",
    "Announce Date": "announce_date",
    "Keywords": "keywords",
}

# Columns to drop from the raw TSV
DROP_COLUMNS = ["announcementXML"]

SUMMARY_COLUMNS = list(RAW_TO_CLEAN_COLUMNS.values())

# Default cache directory name (created in the current working directory)
CACHE_DIR_NAME = ".pxscraper_cache"

# Cache metadata filename
CACHE_META_FILE = "_metadata.json"

# Default cache max age in hours
DEFAULT_CACHE_MAX_AGE_HOURS = 24

# Polite delay between individual XML requests (seconds)
XML_REQUEST_DELAY = 1.0

# User-Agent string for API requests
USER_AGENT = "pxscraper/0.3.0 (https://github.com/LangeLab/pxscraper; academic research tool)"

# HTTP timeout in seconds
HTTP_TIMEOUT = 60

# PXD dataset ID pattern (e.g. PXD000001, PXD063194)
PXD_ID_RE = re.compile(r"^PXD\d{6,}$")


def validate_pxd_id(dataset_id: str) -> str:
    """Validate and return a PXD dataset ID, or raise ValueError."""
    dataset_id = dataset_id.strip()
    if not PXD_ID_RE.match(dataset_id):
        raise ValueError(
            f"Invalid dataset ID: {dataset_id!r} (expected format: PXD followed by 6+ digits)"
        )
    return dataset_id
