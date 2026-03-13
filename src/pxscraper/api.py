"""ProteomeCentral API client."""

import time

import requests

from pxscraper.models import HTTP_TIMEOUT, USER_AGENT, XML_REQUEST_DELAY, validate_pxd_id

SUMMARY_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset"
    "?action=summary&outputMode=tsv"
)

DATASET_XML_URL = (
    "https://proteomecentral.proteomexchange.org/cgi/GetDataset"
    "?outputMode=XML&ID={dataset_id}"
)


def _session() -> requests.Session:
    """Create a requests Session with a polite User-Agent."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_summary(session: requests.Session | None = None) -> str:
    """Download the full ProteomeXchange dataset summary TSV.

    Returns the raw TSV text (~50k rows).
    """
    s = session or _session()
    resp = s.get(SUMMARY_URL, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def fetch_dataset_xml(
    dataset_id: str,
    session: requests.Session | None = None,
    delay: float = XML_REQUEST_DELAY,
) -> str:
    """Download the XML metadata for a single PXD dataset.

    Validates the dataset ID format before making the request.
    Includes a polite delay before the request to avoid overloading
    the ProteomeCentral server.
    """
    dataset_id = validate_pxd_id(dataset_id)
    if delay > 0:
        time.sleep(delay)
    s = session or _session()
    url = DATASET_XML_URL.format(dataset_id=dataset_id)
    resp = s.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.text
