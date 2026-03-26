# pxscraper Test Matrix

> **228 tests** across 6 modules | v0.4.1 | Python 3.12+

---

## test_parse.py (57 tests)

### TestStripHtml (8)

Validates the `strip_html()` utility that removes HTML tags (especially `<a>` anchors) from raw ProteomeCentral TSV cells.

| #   | Test                          | What it verifies                                       | Expect | Why                                                           |
| --- | ----------------------------- | ------------------------------------------------------ | ------ | ------------------------------------------------------------- |
| 1   | `test_simple_anchor`          | Single `<a>` tag stripped, inner text kept             | pass   | Core use case — every dataset ID arrives wrapped in an anchor |
| 2   | `test_nested_tags`            | `<b><a>` nesting stripped correctly                    | pass   | Publication cells sometimes have bold+anchor combos           |
| 3   | `test_multiple_anchors`       | Two anchors in one cell both stripped                  | pass   | Publication field often has DOI + PubMed links                |
| 4   | `test_plain_text_unchanged`   | Text without HTML passes through unchanged             | pass   | Most species/instrument cells have no HTML                    |
| 5   | `test_empty_string`           | Empty string returns empty string                      | pass   | Guard against edge cases in sparse rows                       |
| 6   | `test_non_string_passthrough` | `None` and `int` values returned as-is                 | pass   | pandas cells can be NaN/numeric — must not crash              |
| 7   | `test_self_closing_tag`       | `<br/>` removed, surrounding text joined               | pass   | Occasional `<br/>` appears in free-text fields                |
| 8   | `test_whitespace_stripping`   | Leading/trailing whitespace stripped after tag removal | pass   | Prevents invisible whitespace in cleaned data                 |

### TestParseSummaryTsv (9)

Core parser: reads raw TSV from the ProteomeCentral API, cleans it into a tidy DataFrame.

| #   | Test                                  | What it verifies                                    | Expect | Why                                                      |
| --- | ------------------------------------- | --------------------------------------------------- | ------ | -------------------------------------------------------- |
| 1   | `test_basic_shape`                    | Returns `ParseResult`; 2 rows, 9 clean column names | pass   | Contract: shape and column renaming                      |
| 2   | `test_html_stripped_from_dataset_id`  | Dataset IDs are plain `PXD*` strings                | pass   | IDs must be usable as keys without HTML noise            |
| 3   | `test_html_stripped_from_publication` | No `<a` tags remain in publication column           | pass   | DOI/PubMed links cleaned to plain text                   |
| 4   | `test_announcement_xml_dropped`       | `announcementXML` column removed                    | pass   | Column is empty filler in the raw TSV                    |
| 5   | `test_trailing_whitespace_stripped`   | Trailing spaces on cell values trimmed              | pass   | Raw data has trailing spaces (e.g. "Rattus norvegicus ") |
| 6   | `test_no_empty_rows`                  | Blank trailing rows filtered out                    | pass   | TSV often has empty trailing lines                       |
| 7   | `test_single_row`                     | Parses correctly with only 1 data row               | pass   | Minimum viable input                                     |
| 8   | `test_total_raw_lines_counted`        | `ParseResult.total_raw_lines` equals row count      | pass   | Diagnostics: user needs to know total before filtering   |
| 9   | `test_no_skipped_lines_on_clean_data` | `skipped_count == 0`, `skipped_lines == []`         | pass   | Clean data should produce zero warnings                  |

### TestParseSummaryTsvFixture (2)

Runs the parser against a real TSV fixture captured from ProteomeCentral.

| #   | Test                               | What it verifies                                 | Expect | Why                                           |
| --- | ---------------------------------- | ------------------------------------------------ | ------ | --------------------------------------------- |
| 1   | `test_fixture_parses`              | Fixture loads, 3+ rows, all IDs start with `PXD` | pass   | Regression test against real-world data shape |
| 2   | `test_fixture_no_html_in_any_cell` | No `<a` substring in any cell after parsing      | pass   | Confirms HTML stripping works on real data    |

### TestParseDatasetXml (15)

Parses per-dataset XML (ProteomeXchange schema) into a flat dict. Each test isolates one field.

| #   | Test                     | What it verifies                           | Expect | Why                         |
| --- | ------------------------ | ------------------------------------------ | ------ | --------------------------- |
| 1   | `test_dataset_id`        | `id` attribute extracted from root element | pass   | Primary key for the dataset |
| 2   | `test_title`             | `title` from `DatasetSummary`              | pass   | Human-readable dataset name |
| 3   | `test_description`       | `Description` text content                 | pass   | Abstract / free text        |
| 4   | `test_species`           | Scientific name from `SpeciesList` cvParam | pass   | Critical filter dimension   |
| 5   | `test_instruments`       | Instrument name extracted                  | pass   | Instrument filter support   |
| 6   | `test_modifications`     | Modification names extracted               | pass   | PTM information for users   |
| 7   | `test_submitter_contact` | Submitter name, email, affiliation         | pass   | Contact metadata            |
| 8   | `test_lab_head_contact`  | Lab head name and email                    | pass   | Contact metadata            |
| 9   | `test_pubmed`            | PubMed ID(s) extracted                     | pass   | Literature linking          |
| 10  | `test_doi`               | DOI string(s) extracted                    | pass   | Literature linking          |
| 11  | `test_ftp_location`      | FTP URL contains dataset ID                | pass   | Data download path          |
| 12  | `test_review_level`      | `Peer-reviewed dataset` string             | pass   | Quality indicator           |
| 13  | `test_announce_date`     | Date from `DatasetSummary` attribute       | pass   | Date filtering support      |
| 14  | `test_repository`        | `hostingRepository` attribute (e.g. PRIDE) | pass   | Repository filtering        |
| 15  | `test_keywords`          | Submitter keywords extracted               | pass   | Keyword search support      |

### TestParseDatasetXmlFixture (4)

Runs the XML parser against a real fixture file (`PXD063194`).

| #   | Test                           | What it verifies                        | Expect | Why                                              |
| --- | ------------------------------ | --------------------------------------- | ------ | ------------------------------------------------ |
| 1   | `test_fixture_parses`          | Correct dataset ID, PRIDE repository    | pass   | Real-world XML regression                        |
| 2   | `test_fixture_has_description` | Description > 50 chars                  | pass   | Ensures description extraction works on real XML |
| 3   | `test_fixture_has_species`     | Contains "Rattus"                       | pass   | Species extraction on real data                  |
| 4   | `test_fixture_has_contacts`    | Submitter name non-empty, email has `@` | pass   | Contact parsing on real data                     |

### TestParseEdgeCases (7)

Boundary conditions: minimal XML, multi-species, empty inputs, invalid inputs, missing contacts.

| #   | Test                                       | What it verifies                                             | Expect | Why                                                 |
| --- | ------------------------------------------ | ------------------------------------------------------------ | ------ | --------------------------------------------------- |
| 1   | `test_xml_missing_description`             | Minimal XML with no optional elements returns empty strings  | pass   | Not all datasets have descriptions/species/keywords |
| 2   | `test_xml_multiple_species`                | Two species joined with `;` separator                        | pass   | Many datasets are multi-organism                    |
| 3   | `test_tsv_with_only_header`                | Header-only TSV returns 0-row DataFrame with correct columns | pass   | Edge case: empty ProteomeCentral response           |
| 4   | `test_tsv_empty_string_raises`             | Empty string raises an exception                             | pass   | Caller must handle empty input                      |
| 5   | `test_xml_invalid_raises`                  | Non-XML string raises an exception                           | pass   | Malformed data must not silently succeed            |
| 6   | `test_xml_empty_string_raises`             | Empty string raises an exception                             | pass   | Null input must not silently succeed                |
| 7   | `test_xml_no_contacts_has_consistent_keys` | Empty ContactList → all 6 contact keys present as `""`       | pass   | Consistent key set for DataFrame construction       |

---

## test_cli.py (32 tests)

### TestCliBasics (3)

CLI entry point: `--version`, `--help`, subcommand discovery.

| #   | Test              | What it verifies                                            | Expect | Why                          |
| --- | ----------------- | ----------------------------------------------------------- | ------ | ---------------------------- |
| 1   | `test_version`    | `--version` prints `0.4.1`                                  | pass   | Version pinned to release    |
| 2   | `test_help`       | `--help` lists `fetch`, `filter`, `lookup`                  | pass   | All subcommands discoverable |
| 3   | `test_fetch_help` | `fetch --help` shows `--output`, `--refresh`, `--cache-dir` | pass   | CLI options documented       |

### TestFetchCommand (6)

End-to-end CLI fetch (mocked API, real file I/O via `tmp_path`).

| #   | Test                                  | What it verifies                                            | Expect | Why                                  |
| --- | ------------------------------------- | ----------------------------------------------------------- | ------ | ------------------------------------ |
| 1   | `test_fetch_writes_output`            | TSV file created, 2 rows, correct dataset IDs               | pass   | Core happy path                      |
| 2   | `test_fetch_verbose`                  | `-v` flag triggers "Downloading" message                    | pass   | Verbose output works                 |
| 3   | `test_fetch_uses_cache`               | Second fetch hits cache (0 API calls), output says "cached" | pass   | Cache saves redundant downloads      |
| 4   | `test_fetch_refresh_bypasses_cache`   | `--refresh` forces re-download despite cache                | pass   | Users can force fresh data           |
| 5   | `test_fetch_output_has_clean_columns` | Output has `dataset_id`, no `announcementXML` or raw names  | pass   | Column renaming and dropping applied |
| 6   | `test_fetch_no_html_in_output`        | Output file contains no `<a` or `</a>`                      | pass   | HTML fully stripped before write     |

### TestStubs (1)

Residual integration stub: confirms `lookup` with no arguments exits with an error.

| #   | Test                                   | What it verifies                    | Expect | Why                                              |
| --- | -------------------------------------- | ----------------------------------- | ------ | ------------------------------------------------ |
| 1   | `test_lookup_no_args_exits_with_error` | `lookup` with no IDs exits non-zero | pass   | Regression guard — full tests are in test_lookup |

### TestFilterCommand (18)

End-to-end filter command (mocked API, real file I/O via `tmp_path`).

| #   | Test                                       | What it verifies                                          | Expect | Why                                      |
| --- | ------------------------------------------ | --------------------------------------------------------- | ------ | ---------------------------------------- |
| 1   | `test_filter_help`                         | `filter --help` shows all filter flags                    | pass   | All options discoverable                 |
| 2   | `test_filter_requires_at_least_one_filter` | No filters raises ClickException                          | pass   | User must specify at least one filter    |
| 3   | `test_filter_with_input_file`              | `-i data.tsv -s Homo` reads file rather than auto-fetch   | pass   | Explicit input path works                |
| 4   | `test_filter_auto_fetch`                   | Auto-downloads from API when no `--input`                 | pass   | Zero-friction first use                  |
| 5   | `test_filter_uses_cache`                   | Uses existing cache (0 API calls)                         | pass   | Cache avoids re-download                 |
| 6   | `test_filter_by_species`                   | `-s "Mus musculus"` returns correct subset                | pass   | Species filter works end-to-end          |
| 7   | `test_filter_by_repo`                      | `-r MassIVE` returns correct subset                       | pass   | Repo filter works end-to-end             |
| 8   | `test_filter_no_matches`                   | Nonexistent species shows "No datasets matched"           | pass   | Graceful empty result                    |
| 9   | `test_filter_by_date`                      | `--after 2025-02-01` returns correct subset               | pass   | Date range filter works end-to-end       |
| 10  | `test_filter_connection_error`             | ConnectionError shows friendly message                    | pass   | Network errors handled in filter too     |
| 11  | `test_filter_invalid_species_regex`        | Bad regex for `--species` shows friendly error            | pass   | User-supplied regex validated early      |
| 12  | `test_filter_invalid_instrument_regex`     | Bad regex for `--instrument` shows friendly error         | pass   | User-supplied regex validated early      |
| 13  | `test_filter_by_instrument`                | `--instrument "Q Exactive"` returns correct subset        | pass   | Instrument filter works end-to-end       |
| 14  | `test_filter_keyword_file`                 | `-k keywords.txt` reads keyword file correctly            | pass   | Keyword file path works via CLI          |
| 15  | `test_filter_invalid_after_date`           | Bad `--after` date shows friendly error with option name  | pass   | Date format validated before data load   |
| 16  | `test_filter_invalid_before_date`          | Bad `--before` date shows friendly error with option name | pass   | Date format validated before data load   |
| 17  | `test_filter_after_later_than_before`      | `--after` > `--before` shows friendly error               | pass   | Logically invalid range caught early     |
| 18  | `test_filter_unknown_keyword_column_warns` | Unknown column in `--keyword-columns` emits Warning line  | pass   | User notified of typo, filter still runs |

### TestFilterDeep (8)

End-to-end deep search (`filter --deep`), XML description matching via mocked API.

| #   | Test                                          | What it verifies                                                | Expect | Why                                                |
| --- | --------------------------------------------- | --------------------------------------------------------------- | ------ | -------------------------------------------------- |
| 1   | `test_deep_finds_description_only_match`      | Keyword absent from title/keywords but in XML description found | pass   | Core deep-search use case                          |
| 2   | `test_deep_no_match_excluded`                 | Keyword absent from all fields → no output rows                 | pass   | True negative: deep search doesn't inflate results |
| 3   | `test_deep_requires_keywords`                 | `--deep` without `-k` exits with error                          | pass   | Guard against nonsensical invocation               |
| 4   | `test_deep_output_has_description_column`     | Output TSV contains `description` column                        | pass   | Output enriched with XML data                      |
| 5   | `test_deep_uses_xml_cache`                    | Pre-cached XML reused; `fetch_datasets_xml` not called          | pass   | Cache avoids redundant network requests            |
| 6   | `test_deep_yes_skips_prompt`                  | `--yes` skips large-batch confirmation prompt                   | pass   | Non-interactive / scripting mode                   |
| 7   | `test_deep_large_set_without_yes_prompts`     | Large candidate set triggers prompt; `n` aborts                 | pass   | User protected from accidental 5h fetch            |
| 8   | `test_deep_connection_error_exits_friendly`   | `ConnectionError` during XML fetch → friendly message, no file  | pass   | Network errors handled cleanly                     |

### TestFetchErrors (3)

Verifies friendly error messages for network failures.

| #   | Test                          | What it verifies                                                        | Expect | Why                            |
| --- | ----------------------------- | ----------------------------------------------------------------------- | ------ | ------------------------------ |
| 1   | `test_fetch_connection_error` | ConnectionError shows "Could not reach ProteomeCentral", no output file | pass   | User-friendly network error    |
| 2   | `test_fetch_timeout_error`    | Timeout shows "timed out" message                                       | pass   | Explicit timeout feedback      |
| 3   | `test_fetch_http_error`       | HTTPError shows "error" in output                                       | pass   | Server errors surfaced cleanly |

### TestFetchDiagnostics (1)

Parse diagnostics surfaced in CLI output.

| #   | Test                                         | What it verifies                                        | Expect | Why                           |
| --- | -------------------------------------------- | ------------------------------------------------------- | ------ | ----------------------------- |
| 1   | `test_fetch_reports_no_skipped_rows_verbose` | Verbose output includes "no rows skipped" on clean data | pass   | User sees parse health status |

---

## test_filter.py (53 tests)

### TestBySpecies (7)

Species column regex filter.

| #   | Test                             | What it verifies                          | Expect | Why                                 |
| --- | -------------------------------- | ----------------------------------------- | ------ | ----------------------------------- |
| 1   | `test_exact_species`             | Exact name matches correct rows           | pass   | Core species filter                 |
| 2   | `test_case_insensitive`          | Lowercase pattern still matches           | pass   | Users shouldn't need to match case  |
| 3   | `test_partial_match`             | Short pattern matches within longer names | pass   | Regex partial match                 |
| 4   | `test_semicolon_delimited_match` | Multi-species rows match either species   | pass   | Many datasets have multiple species |
| 5   | `test_no_match`                  | Returns empty DataFrame with columns kept | pass   | Graceful empty result               |
| 6   | `test_regex_pattern`             | `Homo\|Mus` matches both species          | pass   | Regex alternation                   |
| 7   | `test_nan_handling`              | NaN species excluded, no crash            | pass   | Some rows lack species info         |

### TestByRepository (6)

Repository exact-match filter (comma-separated, case-insensitive).

| #   | Test                       | What it verifies                            | Expect | Why                          |
| --- | -------------------------- | ------------------------------------------- | ------ | ---------------------------- |
| 1   | `test_single_repo`         | Single repo name matches correct rows       | pass   | Basic PRIDE filter           |
| 2   | `test_multiple_repos`      | `PRIDE,MassIVE` matches both                | pass   | Multi-repo selection         |
| 3   | `test_case_insensitive`    | Lowercase repo name works                   | pass   | Case normalization           |
| 4   | `test_spaces_around_repos` | Spaces around comma-separated repos trimmed | pass   | Forgiving input parsing      |
| 5   | `test_no_match`            | Nonexistent repo returns empty              | pass   | Graceful empty result        |
| 6   | `test_single_unique_repo`  | jPOST matches its single dataset            | pass   | Less common repositorys work |

### TestByKeywords (11)

Word-boundary keyword search across configurable columns.

| #   | Test                                  | What it verifies                         | Expect | Why                                    |
| --- | ------------------------------------- | ---------------------------------------- | ------ | -------------------------------------- |
| 1   | `test_single_keyword_in_title`        | Keyword found in title column            | pass   | Primary search path                    |
| 2   | `test_single_keyword_in_keywords_col` | Keyword found in keywords column         | pass   | Secondary search path                  |
| 3   | `test_multiple_keywords_or_logic`     | `cancer,yeast` matches either            | pass   | OR logic across keywords               |
| 4   | `test_case_insensitive`               | Uppercase keyword matches lowercase      | pass   | Case normalization                     |
| 5   | `test_word_boundary_matching`         | `plasma` matches, `plas` does not        | pass   | Prevents false positives on substrings |
| 6   | `test_custom_columns`                 | Search restricted to specified columns   | pass   | `--keyword-columns` support            |
| 7   | `test_keyword_from_file`              | Keywords loaded from file (one per line) | pass   | File input for large keyword lists     |
| 8   | `test_keyword_file_with_blank_lines`  | Blank lines in keyword file ignored      | pass   | Robust file parsing                    |
| 9   | `test_no_match`                       | Nonexistent keyword returns empty        | pass   | Graceful empty result                  |
| 10  | `test_empty_keywords_returns_all`     | `,,,` (empty tokens) returns all rows    | pass   | No crash on degenerate input           |
| 11  | `test_nan_handling`                   | NaN in searched columns excluded         | pass   | Some cells may be empty                |

### TestByDateRange (7)

Date range filter with `pd.to_datetime(errors="coerce")`.

| #   | Test                              | What it verifies                  | Expect | Why                             |
| --- | --------------------------------- | --------------------------------- | ------ | ------------------------------- |
| 1   | `test_after_only`                 | Only `--after` filters correctly  | pass   | Common: "datasets since 2024"   |
| 2   | `test_before_only`                | Only `--before` filters correctly | pass   | Common: "datasets before 2023"  |
| 3   | `test_both_after_and_before`      | Range filter with both bounds     | pass   | Full window: 2024-01 to 2024-12 |
| 4   | `test_inclusive_boundaries`       | Exact boundary dates included     | pass   | Boundaries are inclusive        |
| 5   | `test_no_match`                   | Future date returns empty         | pass   | Graceful empty result           |
| 6   | `test_unparseable_dates_excluded` | `"not-a-date"` excluded (NaT)     | pass   | Malformed dates don't crash     |
| 7   | `test_nan_dates_excluded`         | None dates excluded               | pass   | Missing dates handled safely    |

### TestByInstrument (6)

Instrument column regex filter.

| #   | Test                    | What it verifies                     | Expect | Why                            |
| --- | ----------------------- | ------------------------------------ | ------ | ------------------------------ |
| 1   | `test_exact_instrument` | Full instrument name matches         | pass   | Exact match                    |
| 2   | `test_partial_match`    | `Orbitrap` matches multiple variants | pass   | Regex partial match            |
| 3   | `test_case_insensitive` | Lowercase works                      | pass   | Case normalization             |
| 4   | `test_regex_pattern`    | `Q Exactive\|timsTOF` alternation    | pass   | Multi-instrument selection     |
| 5   | `test_no_match`         | Nonexistent instrument returns empty | pass   | Graceful empty result          |
| 6   | `test_nan_handling`     | NaN instruments excluded             | pass   | Some rows lack instrument info |

### TestApplyFilters (8)

Orchestrator that chains all active filters.

| #   | Test                               | What it verifies                                | Expect | Why                          |
| --- | ---------------------------------- | ----------------------------------------------- | ------ | ---------------------------- |
| 1   | `test_single_filter`               | Summary dict has correct counts and filter list | pass   | Basic orchestration          |
| 2   | `test_multiple_filters`            | Species + repo chained correctly                | pass   | Composable filter chain      |
| 3   | `test_combo_species_and_keywords`  | Species then keywords narrows correctly         | pass   | Sequential narrowing         |
| 4   | `test_no_filters_returns_all`      | No filters returns full DataFrame               | pass   | Identity operation           |
| 5   | `test_date_filter_in_summary`      | Date filter shows in active_filters list        | pass   | Summary reporting            |
| 6   | `test_all_filters_combined`        | All 5 filter types active at once               | pass   | Full combination             |
| 7   | `test_keyword_columns_passthrough` | Custom keyword_columns respected                | pass   | Column restriction works     |
| 8   | `test_returns_copy`                | Filtered df is not the same object as input     | pass   | No mutation of original data |

### TestFilterEdgeCases (8)

Boundary conditions: empty DataFrames, special characters, strict date format.

| #   | Test                                    | What it verifies                               | Expect | Why                                       |
| --- | --------------------------------------- | ---------------------------------------------- | ------ | ----------------------------------------- |
| 1   | `test_empty_df_by_species`              | 0-row df returns 0-row df with correct columns | pass   | Empty input must not crash                |
| 2   | `test_empty_df_by_repository`           | 0-row df returns 0-row df                      | pass   | Empty input must not crash                |
| 3   | `test_empty_df_by_keywords`             | 0-row df returns 0-row df                      | pass   | Empty input must not crash                |
| 4   | `test_empty_df_by_date_range`           | 0-row df returns 0-row df                      | pass   | Empty input must not crash                |
| 5   | `test_empty_df_by_instrument`           | 0-row df returns 0-row df                      | pass   | Empty input must not crash                |
| 6   | `test_empty_df_apply_filters`           | Summary shows 0 original and 0 filtered        | pass   | Orchestrator handles empty input          |
| 7   | `test_special_chars_in_keyword_escaped` | Regex special chars in keyword don't crash     | pass   | `re.escape()` safety in by_keywords       |
| 8   | `test_date_format_validation`           | Non-YYYY-MM-DD dates in column coerced to NaT  | pass   | Strict format prevents silent mis-parsing |

---

## test_api.py (31 tests)

### TestSession (2)

HTTP session construction and headers.

| #   | Test                            | What it verifies                          | Expect | Why                                  |
| --- | ------------------------------- | ----------------------------------------- | ------ | ------------------------------------ |
| 1   | `test_user_agent_set`           | `User-Agent` header is set on the session | pass   | Polite scraping — identify ourselves |
| 2   | `test_returns_session_instance` | Returns a `requests.Session` object       | pass   | API contract for callers             |

### TestFetchSummary (3)

Bulk TSV download from ProteomeCentral.

| #   | Test                               | What it verifies                         | Expect | Why                              |
| --- | ---------------------------------- | ---------------------------------------- | ------ | -------------------------------- |
| 1   | `test_returns_text`                | Returns raw TSV string on success        | pass   | Core contract                    |
| 2   | `test_raises_on_http_error`        | HTTP 4xx/5xx raises `requests.HTTPError` | pass   | Caller can handle network errors |
| 3   | `test_creates_own_session_if_none` | Works without a pre-built session        | pass   | Convenience: no session required |

### TestFetchDatasetXml (7)

Per-dataset XML download from the ProteomeCentral API.

| #   | Test                              | What it verifies                               | Expect | Why                                 |
| --- | --------------------------------- | ---------------------------------------------- | ------ | ----------------------------------- |
| 1   | `test_returns_xml`                | Returns XML string for valid PXD ID            | pass   | Core contract                       |
| 2   | `test_applies_delay`              | Sleeps for `delay` seconds between calls       | pass   | Polite rate-limiting                |
| 3   | `test_no_delay_when_zero`         | No sleep when `delay=0`                        | pass   | Tests and scripts can disable delay |
| 4   | `test_raises_on_http_error`       | HTTP error raises `requests.HTTPError`         | pass   | Caller can isolate per-ID failures  |
| 5   | `test_rejects_invalid_dataset_id` | Raises `ValueError` for non-PXD strings        | pass   | Validation before any network call  |
| 6   | `test_rejects_empty_dataset_id`   | Raises `ValueError` for empty string           | pass   | Guard against accidental blank IDs  |
| 7   | `test_rejects_partial_pxd_id`     | Raises `ValueError` for `"PXD"` with no digits | pass   | Pattern must have 6+ digits         |

### TestFetchDatasetsXml (10)

Batch XML downloader — validates all IDs upfront, isolates per-ID errors.

| #   | Test                                        | What it verifies                                     | Expect | Why                                              |
| --- | ------------------------------------------- | ---------------------------------------------------- | ------ | ------------------------------------------------ |
| 1   | `test_returns_dict_of_xml`                  | Single ID returns `{id: xml_string}` dict            | pass   | Core contract for lookup command                 |
| 2   | `test_multiple_ids`                         | Multiple IDs all returned in one dict                | pass   | Batch fetching works                             |
| 3   | `test_empty_list_returns_empty_dict`        | Empty input → empty dict, no requests made           | pass   | No-op for empty input                            |
| 4   | `test_invalid_id_raises_before_any_request` | `ValueError` raised before any HTTP call on bad ID   | pass   | Fail-fast validation                             |
| 5   | `test_per_id_http_error_stores_none`        | HTTP error for one ID → `{id: None}`, others succeed | pass   | Per-ID error isolation                           |
| 6   | `test_per_id_connection_error_stores_none`  | Connection error for one ID → `{id: None}`           | pass   | Network failures don't abort the whole batch     |
| 7   | `test_all_fail_returns_all_none`            | All IDs fail → dict with all values `None`           | pass   | Full-failure case handled gracefully             |
| 8   | `test_keyboard_interrupt_returns_partial`   | Ctrl-C mid-batch returns partial results so far      | pass   | User can interrupt long runs without losing data |
| 9   | `test_delay_is_passed_through`              | `delay` kwarg forwarded to `fetch_dataset_xml()`     | pass   | Polite rate-limiting respected in batch          |
| 10  | `test_creates_own_session_if_none`          | Works without a pre-built session                    | pass   | Convenience: no session plumbing required        |

### TestValidatePxdId (9)

PXD ID validation used across all modules.

| #   | Test                          | What it verifies                             | Expect | Why                                          |
| --- | ----------------------------- | -------------------------------------------- | ------ | -------------------------------------------- |
| 1   | `test_valid_six_digit`        | `PXD000001` accepted                         | pass   | Standard format                              |
| 2   | `test_valid_long_id`          | IDs with >6 digits accepted                  | pass   | New high-numbered datasets have longer IDs   |
| 3   | `test_strips_whitespace`      | Leading/trailing spaces removed before check | pass   | Forgiving input from files and CLI           |
| 4   | `test_rejects_lowercase`      | `pxd000001` rejected                         | pass   | IDs are case-sensitive uppercase             |
| 5   | `test_rejects_no_digits`      | `"PXD"` rejected                             | pass   | Prefix alone is invalid                      |
| 6   | `test_rejects_too_few_digits` | `"PXD1234"` (5 digits) rejected              | pass   | Must have 6+ digits                          |
| 7   | `test_rejects_non_pxd_prefix` | `"MSV000001"` rejected                       | pass   | Only PXD namespace accepted                  |
| 8   | `test_rejects_empty`          | Empty string raises `ValueError`             | pass   | Guard against blank input                    |
| 9   | `test_rejects_path_traversal` | `"../etc/passwd"` raises `ValueError`        | pass   | Security: no path traversal in ID validation |

---

## test_cache.py (28 tests)

### TestGetCacheDir (3)

Cache directory creation and resolution.

| #   | Test                       | What it verifies                          | Expect | Why                                  |
| --- | -------------------------- | ----------------------------------------- | ------ | ------------------------------------ |
| 1   | `test_creates_dir`         | Directory created with correct name       | pass   | Cache bootstrapping                  |
| 2   | `test_idempotent`          | Calling twice returns same path, no error | pass   | Safe to call repeatedly              |
| 3   | `test_default_base_is_cwd` | Default base directory is CWD             | pass   | Sensible default for interactive use |

### TestSaveLoad (6)

DataFrame serialization to TSV + JSON metadata sidecar.

| #   | Test                                 | What it verifies                             | Expect | Why                                   |
| --- | ------------------------------------ | -------------------------------------------- | ------ | ------------------------------------- |
| 1   | `test_roundtrip`                     | Save then load returns identical data        | pass   | Core contract: lossless roundtrip     |
| 2   | `test_save_creates_tsv_file`         | `.tsv` file created on disk                  | pass   | Physical file existence               |
| 3   | `test_save_creates_metadata`         | JSON sidecar has key, row count, timestamp   | pass   | Metadata used for staleness checks    |
| 4   | `test_load_nonexistent_returns_none` | Missing key returns `None` (not crash)       | pass   | Graceful cache miss                   |
| 5   | `test_multiple_datasets`             | Two different keys coexist in same cache dir | pass   | Cache supports multiple named entries |
| 6   | `test_overwrite`                     | Second save to same key replaces data        | pass   | Re-download overwrites stale data     |

### TestIsStale (4)

Cache freshness checking.

| #   | Test                      | What it verifies                              | Expect | Why                                |
| --- | ------------------------- | --------------------------------------------- | ------ | ---------------------------------- |
| 1   | `test_missing_is_stale`   | Non-existent entry is always stale            | pass   | Triggers a fresh download          |
| 2   | `test_fresh_is_not_stale` | Just-saved entry is fresh                     | pass   | Recent cache should be used        |
| 3   | `test_old_is_stale`       | Entry backdated 48h is stale at 24h threshold | pass   | Expired cache triggers re-download |
| 4   | `test_custom_max_age`     | High `max_age_hours` keeps data fresh         | pass   | Configurable staleness window      |

### TestCacheInfo (2)

Cache metadata inspection.

| #   | Test               | What it verifies                         | Expect | Why                           |
| --- | ------------------ | ---------------------------------------- | ------ | ----------------------------- |
| 1   | `test_existing`    | Returns dict with `rows` and `timestamp` | pass   | Users can inspect cache state |
| 2   | `test_nonexistent` | Returns `None` for unknown key           | pass   | Graceful handling             |

### TestCorruptedMetadata (2)

Recovery from corrupted JSON metadata files.

| #   | Test                                  | What it verifies                                          | Expect | Why                             |
| --- | ------------------------------------- | --------------------------------------------------------- | ------ | ------------------------------- |
| 1   | `test_corrupted_json_returns_empty`   | Corrupted JSON → load returns None, is_stale returns True | pass   | Silent recovery from corruption |
| 2   | `test_save_overwrites_corrupted_json` | Saving after corruption overwrites with valid JSON        | pass   | Self-healing on next write      |

### TestXmlCache (11)

Per-dataset XML file cache (added v0.4.0). Immutable once written; never expires.

| #   | Test                                    | What it verifies                                         | Expect | Why                                            |
| --- | --------------------------------------- | -------------------------------------------------------- | ------ | ---------------------------------------------- |
| 1   | `test_save_creates_xml_file`            | `PXD000001.xml` file created in cache dir                | pass   | Core write contract                            |
| 2   | `test_load_returns_saved_content`       | Loaded XML matches saved string exactly                  | pass   | Lossless round-trip                            |
| 3   | `test_load_nonexistent_returns_none`    | Missing ID returns `None`, no exception                  | pass   | Graceful cache miss                            |
| 4   | `test_is_xml_cached_true_after_save`    | `True` immediately after save                            | pass   | Freshness check used by lookup command         |
| 5   | `test_is_xml_cached_false_when_missing` | `False` for IDs not yet fetched                          | pass   | Drives which IDs to fetch from API             |
| 6   | `test_save_overwrites_existing`         | Second save replaces content                             | pass   | Allows manual re-fetch by deleting cache file  |
| 7   | `test_multiple_ids_are_independent`     | Two IDs stored in separate files, no cross-contamination | pass   | Each PXD gets its own file                     |
| 8   | `test_invalid_id_raises_on_save`        | `ValueError` on `save_xml("BADID", ...)`                 | pass   | Consistent ID validation across all operations |
| 9   | `test_invalid_id_raises_on_load`        | `ValueError` on `load_xml("BADID")`                      | pass   | Same                                           |
| 10  | `test_invalid_id_raises_on_is_cached`   | `ValueError` on `is_xml_cached("BADID")`                 | pass   | Same                                           |
| 11  | `test_xml_and_tsv_coexist`              | XML cache files coexist with TSV summary cache           | pass   | Both cache types share one directory           |

---

## test_lookup.py (27 tests)

Integration tests for the `pxscraper lookup` CLI command. All HTTP calls are mocked; no network required.

### TestLookupHappyPath (8)

End-to-end success scenarios.

| #   | Test                               | What it verifies                                    | Expect | Why                                                           |
| --- | ---------------------------------- | --------------------------------------------------- | ------ | ------------------------------------------------------------- |
| 1   | `test_single_id_via_flag`          | `--ids PXD000001 --yes` writes 1-row TSV            | pass   | Core use case                                                 |
| 2   | `test_multiple_ids_via_flag`       | `--ids PXD000001,PXD000002` writes 2-row TSV        | pass   | Comma-separated IDs work                                      |
| 3   | `test_ids_file`                    | `--ids-file ids.txt` reads IDs from file            | pass   | File input mode                                               |
| 4   | `test_input_tsv_pipeline`          | `--input filtered.tsv` reads IDs from filter output | pass   | Filter → lookup pipeline                                      |
| 5   | `test_ids_combined_with_ids_file`  | `--ids` + `--ids-file` merged and deduplicated      | pass   | Sources are unioned; duplicates removed                       |
| 6   | `test_output_has_expected_columns` | Output TSV has all 19 expected columns              | pass   | Schema contract for downstream tools                          |
| 7   | `test_default_output_filename`     | Without `-o`, writes `lookup_results.tsv` to CWD    | pass   | Sensible default output name                                  |
| 8   | `test_ftp_location_populated`      | `ftp_location` in output contains the dataset ID    | pass   | FTP path correctly extracted from XML (regression for Bug B3) |

### TestLookupConfirmation (4)

Confirmation prompt fires only for large batches (>50 IDs by default).

| #   | Test                                            | What it verifies                                                    | Expect | Why                                                        |
| --- | ----------------------------------------------- | ------------------------------------------------------------------- | ------ | ---------------------------------------------------------- |
| 1   | `test_yes_flag_skips_prompt`                    | `--yes` completes without any prompt                                | pass   | Script-friendly flag                                       |
| 2   | `test_small_batch_needs_no_yes_flag`            | ≤50 IDs succeeds without `--yes`                                    | pass   | Single lookup should not require confirmation (Bug B2 fix) |
| 3   | `test_large_batch_triggers_confirmation_prompt` | >threshold IDs prompts; answering 'n' aborts without writing output | pass   | Protects against accidental large fetches                  |
| 4   | `test_prompt_abort_exits_cleanly`               | Aborting prompt leaves no output file and makes no API call         | pass   | Clean abort behaviour                                      |

### TestLookupCache (3)

Cache integration with the lookup command.

| #   | Test                                      | What it verifies                                       | Expect | Why                            |
| --- | ----------------------------------------- | ------------------------------------------------------ | ------ | ------------------------------ |
| 1   | `test_cache_hit_skips_fetch`              | Pre-cached ID is not fetched from API                  | pass   | Avoids redundant network calls |
| 2   | `test_partial_cache_fetches_only_missing` | Cached IDs served from disk; only uncached IDs fetched | pass   | Efficient partial-hit handling |
| 3   | `test_fetched_xml_is_cached`              | After successful lookup, XML is written to cache dir   | pass   | Subsequent runs are faster     |

### TestLookupErrors (9)

Error conditions and partial-failure handling.

| #   | Test                                          | What it verifies                                                   | Expect | Why                                      |
| --- | --------------------------------------------- | ------------------------------------------------------------------ | ------ | ---------------------------------------- |
| 1   | `test_no_ids_given_exits_with_error`          | No source of IDs → non-zero exit with "No PXD IDs" message         | pass   | User sees a clear error, not a traceback |
| 2   | `test_invalid_id_exits_with_error`            | Invalid ID (e.g. `NOTANID`) → non-zero exit with "Invalid" message | pass   | ID validation fires before any API call  |
| 3   | `test_mixed_valid_invalid_ids_exits`          | Mix of valid and invalid → exits, bad ID named in output           | pass   | User knows which ID was rejected         |
| 4   | `test_input_tsv_missing_dataset_id_column`    | TSV without `dataset_id` column → non-zero exit with column name   | pass   | Friendly error for wrong input file      |
| 5   | `test_all_fetches_fail_exits_with_error`      | All IDs return `None` → non-zero exit with summary message         | pass   | Total failure surfaced explicitly        |
| 6   | `test_partial_failure_writes_successful_rows` | Some IDs fail → successful rows written, warning printed           | pass   | Partial success is still useful          |
| 7   | `test_connection_error_exits_friendly`        | `requests.ConnectionError` → friendly message, non-zero exit       | pass   | No raw tracebacks for network problems   |
| 8   | `test_timeout_error_exits_friendly`           | `requests.Timeout` → "timed out" in output                         | pass   | Explicit timeout feedback                |
| 9   | `test_duplicate_ids_deduplication`            | Same ID in `--ids` twice → API called with it only once            | pass   | Deduplication before fetch               |

### TestLookupDelay (1)

| #   | Test                         | What it verifies                                  | Expect | Why                            |
| --- | ---------------------------- | ------------------------------------------------- | ------ | ------------------------------ |
| 1   | `test_delay_passed_to_fetch` | `--delay 0.5` forwarded to `fetch_datasets_xml()` | pass   | Rate-limit configuration works |

### TestLookupVerbose (1)

| #   | Test                              | What it verifies                             | Expect | Why                                    |
| --- | --------------------------------- | -------------------------------------------- | ------ | -------------------------------------- |
| 1   | `test_verbose_reports_cache_hits` | `-v` output mentions "cached" when cache hit | pass   | User can see which IDs came from cache |

### TestLookupHelp (1)

| #   | Test                                 | What it verifies                                      | Expect | Why                            |
| --- | ------------------------------------ | ----------------------------------------------------- | ------ | ------------------------------ |
| 1   | `test_lookup_help_shows_all_options` | `--help` lists all flags: `--ids`, `--ids-file`, etc. | pass   | Documentation via CLI contract |

---

## test_parse.py — TestParseDatasetXmlNamespace (12, added v0.4.1)

Regression tests confirming `parse_dataset_xml()` correctly extracts every field when the XML document declares a default namespace (`xmlns="http://proteomexchange.org/schema"`). Each test parses `SAMPLE_XML_WITH_NS` and checks one output key. These tests caught Bug B1 (namespace-unaware XPath in lxml).

| #   | Test                               | What it verifies                                                   | Expect | Why                                                |
| --- | ---------------------------------- | ------------------------------------------------------------------ | ------ | -------------------------------------------------- |
| 1   | `test_title_populated`             | `title` non-empty when XML has `xmlns=`                            | pass   | DatasetSummary/@title not reachable without fix    |
| 2   | `test_description_populated`       | `description` non-empty                                            | pass   | Description text content silently blank before fix |
| 3   | `test_announce_date_populated`     | `announce_date` non-empty                                          | pass   | DatasetSummary/@announceDate                       |
| 4   | `test_repository_populated`        | `repository` non-empty                                             | pass   | DatasetSummary/@hostingRepository                  |
| 5   | `test_species_populated`           | `species` non-empty                                                | pass   | SpeciesList xpath fails without namespace strip    |
| 6   | `test_instruments_populated`       | `instruments` non-empty                                            | pass   | InstrumentList xpath idem                          |
| 7   | `test_review_level_populated`      | `review_level` non-empty                                           | pass   | ReviewLevel xpath idem                             |
| 8   | `test_keywords_populated`          | `keywords` non-empty                                               | pass   | KeywordList xpath idem                             |
| 9   | `test_submitter_contact_populated` | `submitter_name` non-empty                                         | pass   | ContactList xpath idem                             |
| 10  | `test_pubmed_populated`            | `pubmed_ids` non-empty                                             | pass   | PublicationList xpath idem                         |
| 11  | `test_ftp_location_populated`      | `ftp_location` non-empty                                           | pass   | FullDatasetLinkList xpath idem                     |
| 12  | `test_dataset_id_always_works`     | `dataset_id` populated even without namespace fix (root attribute) | pass   | Baseline: root `id` attribute unaffected by xmlns  |

---

## Summary

| Module         |   Tests | All pass | Skipped | Expected failures |
| -------------- | ------: | :------: | :-----: | :---------------: |
| test_parse.py  |      57 |   yes    |    0    |         0         |
| test_filter.py |      53 |   yes    |    0    |         0         |
| test_api.py    |      31 |   yes    |    0    |         0         |
| test_cli.py    |      40 |   yes    |    0    |         0         |
| test_cache.py  |      28 |   yes    |    0    |         0         |
| test_lookup.py |      27 |   yes    |    0    |         0         |
| **Total**      | **236** | **yes**  |  **0**  |       **0**       |

All tests are deterministic, offline (mocked HTTP), and use `tmp_path` for I/O — no network calls, no side effects.
