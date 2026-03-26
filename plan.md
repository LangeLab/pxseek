# pxscraper — Development Plan

> Previous analysis archived in `initial-look.md`.

---

## Current State (v0.4.2)

### Modules

| Module      | Responsibility                                           | Status |
| ----------- | -------------------------------------------------------- | ------ |
| `api.py`    | HTTP client: bulk TSV + per-dataset XML endpoints        | Done   |
| `parse.py`  | TSV/XML parsing, HTML stripping, `ParseResult` DTO       | Done   |
| `cache.py`  | Local disk cache with JSON metadata, 24h TTL + XML cache | Done   |
| `filter.py` | Composable DataFrame filters (6 functions)               | Done   |
| `models.py` | Constants, column maps, `validate_pxd_id()`              | Done   |
| `cli.py`    | Click CLI: `fetch`, `filter` (incl. `--deep`), `lookup`  | Done   |

### Tests

236 passing — filter (53), parse (57), cli (40), lookup (27), api (31), cache (28)

### CI

Disabled (billing issue). Workflow file: `.github/workflows/ci.yml.disabled`.

### Validated (live)

- `pxscraper fetch` retrieves ~50,848 datasets in one HTTP request
- `pxscraper filter` with species, repository, keywords, dates, instrument all work
- Cache hit is instant; auto-fetch fallback works from `filter`
- Clean output: no HTML, snake_case columns, correct column set

---

## GitHub Issues

### Issue #1 — "More detailed search" (open)

> Include a more detailed search by accessing the inside of a particular metadata entry,
> searching for the keywords within the summary/abstract.

Requires `filter --deep` flag + batch XML infrastructure. → **Phase 3b / v0.4.2 — Done**

### ~~Issue #2 — "Scrape list of PXIDs metadata into a dataframe"~~ (closed)

> ~~Given a list of PXD identifiers, retrieve their metadata into a structured dataframe.~~

~~Addressed by the `lookup` command in Phase 3a / v0.4.0.~~

---

## Known Issues, Gaps, and Risks

Items are annotated: ~~struck out~~ = resolved; **bold** = next priority; plain = deferred.

### Performance

1. **Cache uses TSV format.** Re-parsing 50k rows on every cache load is slow. → Phase 4 (Parquet)
2. **`--deep` will be slow by design.** 1 req/s = 100s for 100 datasets. → Phase 3b (progress bar + estimate)
3. ~~`fetch_summary()` downloads ~15 MB with no streaming.~~ Low risk. No action needed.
4. ~~`strip_html()` cell-by-cell via `.apply()`.~~ Completes in <1s. No action needed.
5. **Batch XML fetching is synchronous.** For large `lookup` runs (>500 IDs), async I/O would be substantially faster. → Phase 5.

### Correctness

1. ~~**Silent row drops on parse.**~~ Resolved: `ParseResult.skipped_lines` + CLI reporting in verbose mode.
2. ~~**`announce_date` stored as string.**~~ Resolved: `by_date_range()` uses `pd.to_datetime(format="%Y-%m-%d", errors="coerce")`.
3. ~~**Multi-species semicolon handling.**~~ Verified: `str.contains()` regex matches within delimited string.
4. ~~**No PXD ID validation.**~~ Resolved: `validate_pxd_id()` in `models.py`, called from `api.fetch_dataset_xml()`.
5. ~~**Invalid regex crashes filter.**~~ Resolved: CLI validates regex patterns before passing to filter functions.
6. ~~**Corrupted cache metadata crashes.**~~ Resolved: `_read_meta()` catches `json.JSONDecodeError`.
7. ~~**Invalid `--after`/`--before` date string crashes.**~~ Resolved: CLI validates date format before calling `apply_filters()`.
8. ~~**`parse_dataset_xml()` returns inconsistent keys when contacts absent.**~~ Resolved: contact fields pre-seeded with `""` before the contacts loop.
9. ~~**`parse_dataset_xml()` silently returns empty strings for all fields when XML has a default `xmlns=` namespace.**~~ Resolved: namespace prefixes stripped with `elem.tag.rpartition("}")[2]` loop after `etree.fromstring()` (v0.4.1).
10. ~~**`lookup` confirmation prompt fires for any number of IDs, not just >50.**~~ Resolved: `LOOKUP_CONFIRM_THRESHOLD = 50` constant in `models.py`; `cli.py` guards with `len(to_fetch) > LOOKUP_CONFIRM_THRESHOLD` (v0.4.1).
11. ~~**`MOCK_XML_TEMPLATE` in `test_lookup.py` used wrong FTP element path, so `ftp_location` was always `""` in all lookup tests.**~~ Resolved: path corrected to `FullDatasetLinkList/FullDatasetLink`; `test_ftp_location_populated` added (v0.4.1).

### Usability

1. ~~**No auto-fetch in filter.**~~ Resolved: `filter` auto-fetches from cache or API when no `--input` given.
2. ~~**No filter-to-lookup pipeline.**~~ ~~`lookup` should accept `--input filtered.tsv`. → Phase 3a.~~ Resolved: `lookup --input` accepts TSV from `filter` or `fetch`.
3. **Cache directory not obvious.** Consider `pxscraper cache info/clear` subcommands. → Phase 4.
4. ~~**Raw tracebacks on network errors.**~~ Resolved: `_fetch_summary_safe()` converts to `click.ClickException`.
5. ~~**Logically invalid date range (`--after` > `--before`) produces empty results silently.**~~ Resolved: CLI validates range before data is loaded.
6. ~~**Unknown `--keyword-columns` entry silently ignored.**~~ Resolved: CLI emits `Warning:` line for each unrecognised column.
7. **No user-configurable defaults.** Species, cache dir, delay, output format must be re-specified every run. → Phase 5 (config file).
8. **No summary statistics.** No quick way to see breakdown by year, species, repository, or instrument. → Phase 5 (`stats` command).

---

## Code Quality Standards

Conventions established in v0.3.1 hardening. Follow these for all future code.

### Imports

- **Module-level**: stdlib, then third-party, then local. One blank line between groups (enforced by ruff `I001`).
- **Lazy imports in CLI**: Heavy libraries (`pandas`, `requests`, `lxml`) are imported inside command functions to keep `pxscraper --help` fast. Stdlib imports (`re`, `pathlib`) stay at module level.
- **No late imports in library code**: `api.py`, `parse.py`, `filter.py`, `cache.py` import everything at top.

### Type hints

- All library functions (api, parse, filter, cache, models) have complete type annotations.
- CLI functions (Click commands) are untyped by convention — Click's decorator pattern makes annotations impractical.
- Use `X | None` union syntax (Python 3.10+), not `Optional[X]`.

### Error handling

- **System boundary validation** (CLI layer): Validate user input (regex patterns, date formats, file paths) in `cli.py` before passing to library functions. Convert to `click.ClickException`.
- **Network errors**: Handled via `_fetch_summary_safe()` helper — single source of truth.
- **Library functions**: Raise standard Python exceptions (`ValueError`, `re.error`). Do not catch-and-swallow.
- **Cache corruption**: `_read_meta()` returns empty dict on `JSONDecodeError` (silent recovery).

### Naming

- Module names: lowercase, no underscores (`api.py`, `parse.py`, not `api_client.py`).
- Functions: `snake_case`. Filter functions follow `by_<dimension>()` pattern.
- Constants: `ALL_CAPS` in `models.py`.
- Private helpers: `_leading_underscore`.

### Module responsibilities

| Module      | What belongs here                | What does NOT belong here           |
| ----------- | -------------------------------- | ----------------------------------- |
| `api.py`    | HTTP requests, response handling | Parsing, caching, CLI output        |
| `parse.py`  | TSV/XML → Python data structures | HTTP, file I/O, user messages       |
| `cache.py`  | Disk persistence, staleness      | Parsing, network calls              |
| `filter.py` | DataFrame → DataFrame transforms | I/O, network, user messages         |
| `models.py` | Constants, validation, config    | Business logic, I/O                 |
| `cli.py`    | User interaction, orchestration  | Data processing (delegate to above) |

### DRY patterns

- **Version**: `__version__` lives in `__init__.py`; `models.py` imports it for `USER_AGENT`.
- **Network error handling**: `_fetch_summary_safe()` in `cli.py` — both `fetch` and `filter` use it.
- **Cache resolution**: Still duplicated between `fetch` and `filter` (2 lines each; too small to extract).

### Testing

- Each source module has a corresponding `tests/test_<module>.py`.
- Test classes group by function: `TestBySpecies`, `TestByKeywords`, etc.
- `TestEdgeCases` class covers boundary conditions (empty DataFrames, bad input, corruption).
- Fixtures: `sample_df()` defined per-test-file. `conftest.py` reserved for cross-module fixtures.
- Mocking: Use `@patch` for network calls; use `tmp_path` for file I/O. Never hit real APIs.

---

## Completed Phases

### Phase 1 — Fetch Command (v0.1.0 → v0.2.2)

Scaffolding, API client, TSV/XML parsing, local caching, `fetch` CLI command.
CI pipeline (later disabled). Correctness fixes (v0.2.2): HTML stripping, column mapping,
parse diagnostics, PXD validation, friendly error messages.

### Phase 2 — Filter Command (v0.3.0)

Composable filter engine (`filter.py`): `by_species()`, `by_repository()`, `by_keywords()`,
`by_date_range()`, `by_instrument()`, `apply_filters()`. CLI wiring with auto-fetch fallback,
12 Click options, error handling. 45 unit tests + 10 CLI integration tests.

### Phase 2.5 — Code Hardening (v0.3.1)

Audit-driven quality pass. Changes:

| Area          | What changed                                                                  |
| ------------- | ----------------------------------------------------------------------------- |
| `api.py`      | Moved `validate_pxd_id` import to module level (was late import)              |
| `filter.py`   | Specified `format="%Y-%m-%d"` in `pd.to_datetime()` (suppressed UserWarning)  |
| `parse.py`    | Removed dead `_xpath_text()` helper function                                  |
| `cache.py`    | Added `json.JSONDecodeError` handling in `_read_meta()`                       |
| `models.py`   | `USER_AGENT` now imports `__version__` from `__init__` (DRY)                  |
| `cli.py`      | Extracted `_fetch_summary_safe()` helper for DRY network error handling       |
| `cli.py`      | Added regex validation for `--species` and `--instrument` patterns            |
| `test_filter` | +8 tests: empty DataFrame edge cases, special chars, date format validation   |
| `test_cli`    | +4 tests: invalid regex (species/instrument), instrument filter, keyword file |
| `test_cache`  | +2 tests: corrupted JSON metadata recovery                                    |

Test count: 149 → 163.

### Phase 2.6 — Pre-Phase 3 Fixes (v0.3.2)

Two-commit quality pass targeting confirmed bugs and usability gaps found during Phase 3 planning.

| Area         | What changed                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------- |
| `cli.py`     | Validate `--after`/`--before` date format; raises `ClickException` on non-YYYY-MM-DD strings  |
| `cli.py`     | Validate that `--after` ≤ `--before`; catches logically inverted ranges before data is loaded |
| `cli.py`     | Emit `Warning:` to stderr for each column in `--keyword-columns` not present in the data      |
| `parse.py`   | Pre-seed contact fields with `""` before the contacts loop — consistent key set always        |
| `test_cli`   | +4 tests: invalid `--after`, invalid `--before`, inverted range, unknown keyword column       |
| `test_parse` | +1 test: `test_xml_no_contacts_has_consistent_keys`                                           |

Test count: 163 → 168.

---

### Phase 3a — Lookup Command (v0.4.0)

Per-dataset XML retrieval for user-specified PXD IDs. Closes usability gap #2 (filter-to-lookup pipeline).

| Area          | What changed                                                                                                                      |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `api.py`      | Added `fetch_datasets_xml()`: validates all IDs upfront, tqdm progress, per-ID error isolation, KeyboardInterrupt returns partial |
| `cache.py`    | Added `save_xml()`, `load_xml()`, `is_xml_cached()` for immutable per-dataset XML files                                           |
| `cli.py`      | Full `lookup` command: `--ids`, `--ids-file`, `--input`, `--delay`, `--yes`, `--cache-dir`, `-v`                                  |
| `test_api`    | +11 tests: `TestFetchDatasetsXml`                                                                                                 |
| `test_cache`  | +11 tests: `TestXmlCache`                                                                                                         |
| `test_lookup` | New file — 24 integration tests covering happy paths, cache, errors, delay, verbose, help                                         |
| `test_cli`    | Stub test updated; version assertion bumped to 0.4.0                                                                              |
| `README.md`   | `lookup` marked Available; full usage section with 7 examples and 19-column output schema                                         |

Test count: 168 → 213.

---

### Phase 3a.1 — Bug Fixes (v0.4.1)

Three confirmed bugs in v0.4.0 caught by systematic review and new regression tests.

| Area          | What changed                                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `parse.py`    | Strip XML namespace prefixes after `etree.fromstring()` so `find()` / XPath works when `xmlns=` is set                         |
| `models.py`   | Added `LOOKUP_CONFIRM_THRESHOLD = 50` constant                                                                                 |
| `cli.py`      | `lookup` prompt now fires only when `len(to_fetch) > LOOKUP_CONFIRM_THRESHOLD` (was: any non-zero count)                       |
| `test_parse`  | +12 tests: `TestParseDatasetXmlNamespace` — one per field, all using XML with a default namespace                              |
| `test_lookup` | +3 tests: `test_ftp_location_populated`, `test_small_batch_needs_no_yes_flag`, `test_large_batch_triggers_confirmation_prompt` |
| `test_lookup` | Corrected `MOCK_XML_TEMPLATE` FTP element path (`DatasetFileList` → `FullDatasetLinkList`)                                     |

Test count: 213 → 228.

---

## Phase 3b — Deep Search (v0.4.2) ✓

**Goal**: Keyword search within full dataset description/abstract fields, reusing the XML infrastructure from v0.4.0. Closes **Issue #1**.

### 3b.1 `filter --deep` flag

1. Run summary-level filters first (narrow candidate set)
2. Check XML cache; prompt if uncached count > 50 (unless `--yes`)
3. Fetch XML for uncached candidates via `fetch_datasets_xml()` (with progress bar, using cache)
4. Merge `description` column; apply `by_keywords()` on `[title, keywords, description]`
5. Write enriched output with `description` column; report results

### 3b.2 Checklist

- [x] Add `--deep`, `--yes`, and `--delay` flags to `filter` command
- [x] Reuse `fetch_datasets_xml()` from v0.4.0 (no new HTTP code)
- [x] Apply `by_keywords()` on `description` column via extended columns list
- [x] Write 8 tests for `filter --deep` in `test_cli.py` (mocked XML fetch)
- [x] Update README with `--deep` usage examples
- [x] Bump version to 0.4.2

Test count: 228 → 236 (8 new in `TestFilterDeep`).

---

## Phase 4 — Output & Cache (v0.5.0)

**Goal**: Improve output flexibility and cache performance for users working with large datasets.

- [ ] `--format tsv|csv|json` option for `fetch`, `filter`, `lookup`
- [ ] Switch cache from TSV to Parquet format (addresses gap #1); include migration path for existing caches
- [ ] `pxscraper cache info` — print cache dir path, file sizes, age, row counts (addresses gap #13)
- [ ] `pxscraper cache clear` — remove cache files with confirmation prompt
- [ ] `--quiet` flag for all commands (suppress all output except errors)
- [ ] Bump version to 0.5.0

---

## Phase 5 — Interactivity & Statistics (v0.6.0)

**Goal**: Exploratory analysis features and quality-of-life improvements for power users.

- [ ] `pxscraper stats` command: summary table — dataset counts by year, species, repository, instrument
- [ ] Config file: `~/.pxscraper.toml` for user defaults (species, cache dir, delay, output format)
- [ ] `rich` integration for interactive terminal tables (optional dep; already in `pyproject.toml`)
- [ ] Async batch fetching: replace sync `time.sleep` loop in `fetch_datasets_xml()` with `asyncio` + `aiohttp` + rate limiter (addresses gap #19); retain sync path as fallback
- [ ] Bump version to 0.6.0

---

## Phase 6 — Release (v1.0.0)

**Goal**: Stable public release suitable for the broader proteomics community.

- [ ] Re-enable GitHub Actions CI (addresses gap #23; blocked on billing)
- [ ] Python 3.13 test matrix in CI
- [ ] PyPI publication — add `[project.urls]`, finalise classifiers, test `uv build && uv publish`
- [ ] `CHANGELOG.md` covering all versions from v0.1.0
- [ ] Define public Python API: `__all__` in `__init__.py`, library usage guide in README
- [ ] v1.0.0 semantic-version release

---

## Mappings

### Issues → Phases

| Issue  | Description                  | Phase  | Status     |
| ------ | ---------------------------- | ------ | ---------- |
| #1     | Deep search in abstracts     | 3b     | Pending    |
| ~~#2~~ | ~~PXD ID list to dataframe~~ | ~~3a~~ | ~~Closed~~ |

### Gaps → Resolution

| #   | Description                        | Phase | Status                                                         |
| --- | ---------------------------------- | ----- | -------------------------------------------------------------- |
| 1   | Cache format (TSV → Parquet)       | 4     | Pending                                                        |
| 2   | `--deep` slowness                  | 3b    | Pending (progress bar + estimate + confirmation)               |
| 3   | No streaming for 15 MB fetch       | —     | ~~Low risk, no action needed~~                                 |
| 4   | `strip_html()` perf                | —     | ~~<1s, no action needed~~                                      |
| 5   | Silent row drops on parse          | 2     | ~~Resolved: `ParseResult` diagnostics~~                        |
| 6   | Date column as string              | 2     | ~~Resolved: `format="%Y-%m-%d"` with coerce~~                  |
| 7   | Multi-species semicolons           | 2     | ~~Verified working~~                                           |
| 8   | No PXD ID validation               | 2     | ~~Resolved: `validate_pxd_id()` in models.py~~                 |
| 9   | Invalid regex crashes              | 2.5   | ~~Resolved: CLI validates before calling filters~~             |
| 10  | Corrupted cache metadata           | 2.5   | ~~Resolved: `JSONDecodeError` caught in `_read_meta`~~         |
| 11  | No auto-fetch in filter            | 2     | ~~Resolved: auto-fetch with cache fallback~~                   |
| 12  | No filter-to-lookup pipeline       | 3a    | Pending                                                        |
| 13  | Hidden cache dir                   | 4     | Pending                                                        |
| 14  | Raw tracebacks on network errors   | 2     | ~~Resolved: `_fetch_summary_safe()` helper~~                   |
| 15  | Invalid date string crashes        | 2.6   | ~~Resolved: CLI validates YYYY-MM-DD format~~                  |
| 16  | Inverted date range silent fail    | 2.6   | ~~Resolved: CLI checks `--after` ≤ `--before`~~                |
| 17  | Unknown keyword-column ignored     | 2.6   | ~~Resolved: CLI emits Warning for unknown columns~~            |
| 18  | Inconsistent XML contact keys      | 2.6   | ~~Resolved: contact fields pre-seeded in `parse_dataset_xml`~~ |
| 19  | Synchronous batch fetch bottleneck | 5     | Pending (async I/O with rate limiter)                          |
| 20  | No user-configurable defaults      | 5     | Pending (config file support)                                  |
| 21  | No summary statistics command      | 5     | Pending (`stats` command)                                      |
| 22  | No public Python API surface       | 6     | Pending (`__all__`, usage guide)                               |
| 23  | CI disabled                        | 6     | Pending (billing issue)                                        |
