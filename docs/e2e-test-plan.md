# E2E Test Plan

## Scope

End-to-end tests exercise the full CLI from a user's perspective: they run `oncall-rag` as a subprocess against a temporary corpus and verify output, exit codes, and side effects.

## Scenarios

### Happy Path

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 1 | Index a corpus | `oncall-rag index <tmp_corpus>` | Prints "Indexed N files, M chunks"; chroma db created |
| 2 | Query after index | `oncall-rag query "restart"` | Returns answer with source citations |
| 3 | Eval after index | `oncall-rag eval` | Prints MRR and Recall@5 values |
| 4 | Rebuild index | `oncall-rag index <tmp_corpus> --rebuild` | Re-indexes without error |
| 5 | Help | `oncall-rag --help` | Prints available commands |
| 6 | Chunking experiment | `oncall-rag chunking-experiment <tmp_corpus> --eval <tmp_eval>` | Prints comparison table; writes report |

### Edge Cases

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 7 | Empty corpus | `oncall-rag index <empty_dir>` | Warns no files found |
| 8 | Query with no index | `oncall-rag query "test"` (no prior index) | Error: "No documents indexed" |
| 9 | Index missing path | `oncall-rag index /nonexistent` | Non-zero exit; file not found error |
| 10 | Query with empty question | `oncall-rag query ""` | Returns non-error or handles gracefully |
| 11 | Large file in corpus | Corpus contains a >1MB file | File skipped with warning |
| 12 | Non-markdown files | Corpus contains `.txt`, `.py` files | Only `.md` files indexed |
| 13 | Eval with missing eval file | `oncall-rag eval` with missing eval.json | Handles gracefully |

### M2 — Discord Bot & Dashboard

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 16 | Discord command available | `oncall-rag discord --help` | Prints usage |
| 17 | Dashboard command available | `oncall-rag dashboard --help` | Prints usage |
| 18 | Help shows M2 commands | `oncall-rag --help` | Output includes `discord` and `dashboard` |

### Unit Tests (M2)

| # | Module | Tests |
|---|---|---|
| U1 | `bot._parse_sources` | Full answer, sources-only, no-runbook, no-sources |
| U2 | `bot._answer_to_embed` | No-runbook, full answer, sources-only, plain answer |
| U3 | `bot._log_feedback` | Writes JSONL, appends multiple entries |
| U4 | `bot._log_query` | Writes JSONL, tracks has_sources flag |

### M3 — FIFO Alert Pipeline

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 19 | Generate test alerts | `scripts/generate_test_alerts.py` | 8 .json files created in `alerts/inbox/` |
| 20 | Process alerts | `oncall-rag process-alerts` | Files move inbox → outbox + archive |
| 21 | Verify outbox schema | Each outbox file checked | Has: alert_id, title, processed_at, answer, sources, has_runbook |
| 22 | Empty inbox | Run process-alerts with no files | Reports 0 processed |
| 23 | Invalid JSON in inbox | Place a bad .json file in inbox | Error logged, file skipped |
| 24 | Help shows process-alerts | `oncall-rag --help` | Output includes `process-alerts` |

### Unit Tests (M3)

| # | Module | Tests |
|---|---|---|
| U5 | `alert_schema.Alert` | Defaults, from-dict construction |
| U6 | `alert_schema.AlertResult` | Defaults, field types |
| U7 | `alert_processor._build_question` | Title+message, title-only |
| U8 | `alert_processor.process_alerts` | Empty inbox, happy path with mock, invalid JSON |

### Error Handling

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 14 | Index with bad chunking strategy | Set `CHUNKING_STRATEGY=bad` in env | Validates and errors |
| 15 | Missing required arg | `oncall-rag index` without path | Non-zero exit; shows usage |

## Test Structure

Tests live in `tests/e2e/test_cli.py`. Each test creates a temporary corpus, runs the CLI via `subprocess`, and asserts on stdout/stderr/returncode. M3 alerts use mock/in-memory directories via monkeypatch in unit tests, and the `scripts/test_alert_pipeline.sh` script validates the real pipeline end-to-end.

## CI Integration

E2E tests are tagged with `pytest.mark.e2e` and run as part of the test suite.
