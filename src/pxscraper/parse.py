"""TSV and XML parsing utilities."""

import io
import re
import warnings
from dataclasses import dataclass, field

import pandas as pd
from lxml import etree

from pxscraper.models import DROP_COLUMNS, RAW_TO_CLEAN_COLUMNS

# Regex to strip HTML tags but keep inner text
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class ParseResult:
    """Result of parsing summary TSV, including diagnostics."""

    df: pd.DataFrame
    total_raw_lines: int = 0
    skipped_lines: list[int] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_lines)


def strip_html(text: str) -> str:
    """Remove HTML tags from a string, keeping the inner text."""
    if not isinstance(text, str):
        return text
    return _HTML_TAG_RE.sub("", text).strip()


def parse_summary_tsv(raw_tsv: str) -> ParseResult:
    """Parse the raw ProteomeCentral summary TSV into a clean DataFrame.

    Returns a ParseResult containing:
    - df: the cleaned DataFrame
    - total_raw_lines: number of data lines in the raw TSV
    - skipped_lines: line numbers of rows that could not be parsed
    """
    # Count raw data lines (total lines minus header, minus trailing blank)
    raw_lines = raw_tsv.strip().split("\n")
    total_raw_lines = max(0, len(raw_lines) - 1)  # subtract header

    # Capture warnings from on_bad_lines="warn" to track skipped rows
    skipped_lines: list[int] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = pd.read_csv(
            io.StringIO(raw_tsv), sep="\t", dtype=str, on_bad_lines="warn"
        )
    for w in caught:
        msg = str(w.message)
        if "Expected" in msg and "fields" in msg:
            # Extract line number from warning like "Skipping line 36502: ..."
            match = re.search(r"line (\d+)", msg)
            if match:
                skipped_lines.append(int(match.group(1)))

    # Strip trailing whitespace from column names (API has trailing tab)
    df.columns = df.columns.str.strip()

    # Drop unwanted columns
    for col in DROP_COLUMNS:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Strip HTML from all cells
    for col in df.columns:
        df[col] = df[col].apply(strip_html)

    # Rename columns
    df = df.rename(columns=RAW_TO_CLEAN_COLUMNS)

    # Drop any unnamed/empty columns (trailing tabs in TSV create these)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.loc[:, df.columns.str.strip() != ""]

    # Strip trailing whitespace from string values
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.strip()

    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    return ParseResult(df=df, total_raw_lines=total_raw_lines, skipped_lines=skipped_lines)


def parse_dataset_xml(raw_xml: str) -> dict:
    """Parse a single ProteomeXchange dataset XML into a flat dict.

    Extracts: dataset_id, title, description, species, instruments,
    modifications, contacts, FTP links, PubMed IDs, keywords, review level.
    """
    root = etree.fromstring(raw_xml.encode("utf-8"))

    result = {}

    # Dataset ID
    result["dataset_id"] = root.get("id", "")

    # Title and description from DatasetSummary
    ds = root.find("DatasetSummary")
    result["title"] = ds.get("title", "") if ds is not None else ""
    result["announce_date"] = ds.get("announceDate", "") if ds is not None else ""
    result["repository"] = ds.get("hostingRepository", "") if ds is not None else ""

    desc = ds.find("Description") if ds is not None else None
    result["description"] = desc.text.strip() if desc is not None and desc.text else ""

    # Review level
    review_el = root.xpath(".//ReviewLevel/cvParam/@name")
    result["review_level"] = review_el[0] if review_el else ""

    # Species (may be multiple)
    species = root.xpath('.//SpeciesList/Species/cvParam[@name="taxonomy: scientific name"]/@value')
    result["species"] = "; ".join(species)

    # Instruments (may be multiple)
    instruments = root.xpath(".//InstrumentList/Instrument/cvParam/@name")
    result["instruments"] = "; ".join(instruments)

    # Modifications
    mods = root.xpath(".//ModificationList/cvParam/@name")
    result["modifications"] = "; ".join(mods)

    # Keywords
    kw = root.xpath('.//KeywordList/cvParam[@name="submitter keyword"]/@value')
    result["keywords"] = "; ".join(kw)

    # Contacts
    for contact in root.xpath(".//ContactList/Contact"):
        contact_id = contact.get("id", "")
        name = contact.xpath('cvParam[@name="contact name"]/@value')
        email = contact.xpath('cvParam[@name="contact email"]/@value')
        affil = contact.xpath('cvParam[@name="contact affiliation"]/@value')

        prefix = "submitter" if contact_id == "project_submitter" else "lab_head"
        result[f"{prefix}_name"] = name[0] if name else ""
        result[f"{prefix}_email"] = email[0] if email else ""
        result[f"{prefix}_affiliation"] = affil[0] if affil else ""

    # Publications
    pmids = root.xpath('.//PublicationList/Publication/cvParam[@name="PubMed identifier"]/@value')
    result["pubmed_ids"] = "; ".join(pmids)

    dois = root.xpath(
        './/PublicationList/Publication/cvParam[@name="Digital Object Identifier (DOI)"]/@value'
    )
    result["dois"] = "; ".join(dois)

    # FTP location
    ftp = root.xpath(
        './/FullDatasetLinkList/FullDatasetLink/cvParam[@name="Dataset FTP location"]/@value'
    )
    result["ftp_location"] = ftp[0] if ftp else ""

    return result
