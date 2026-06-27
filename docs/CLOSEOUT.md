# Closeout Report — oncall-rag

**Date:** 2026-06-27
**Status:** Complete — all 37 issues closed

---

## What We Set Out to Build (PRD)

The PRD called for a local-first RAG assistant that indexes runbook-style documentation and answers on-call queries with sourced, ground-truth-verified responses — proving the RAG pipeline before adding team-facing surfaces.

## What We Delivered

### M1 — CLI RAG (16 issues)
| Feature | Status |
|---|---|
| Corpus indexer (55 markdown files, recursive `.md` walk) | ✅ |
| 3 chunking strategies: header-split, recursive, fixed-size | ✅ |
| ChromaDB vector store with `all-MiniLM-L6-v2` embeddings | ✅ |
| CLI: `oncall-rag index <path>`, `oncall-rag query "..."` | ✅ |
| 3 pluggable LLM backends: OMLX, OpenAI, Anthropic | ✅ |
| Eval harness with MRR/Recall@5 (14 Q&A pairs in `data/eval.json`) | ✅ |
| Chunking experiment: header-split winner at **0.9524 MRR** | ✅ |
| 68 unit/integration + 9 e2e tests | ✅ |

### M2 — Discord Bot + Dashboard (12 issues)
| Feature | Status |
|---|---|
| Discord bot with `/ping` and `/query` slash commands | ✅ |
| Rich embed responses with color-coded source fields | ✅ |
| 👍/👎 feedback buttons on every answer | ✅ |
| Feedback logged to `data/feedback.jsonl`, queries to `data/queries.jsonl` | ✅ |
| Streamlit dashboard: overview, query metrics, knowledge gaps, feedback analysis | ✅ |
| 12 unit tests + 3 e2e tests | ✅ |
| Setup guide (`docs/setup.md`) | ✅ |

### M3 — FIFO Alert Pipeline (5 issues)
| Feature | Status |
|---|---|
| `Alert`/`AlertResult` dataclasses, `alerts/inbox|outbox|archive/` dirs | ✅ |
| `oncall-rag process-alerts` CLI command | ✅ |
| Test alert generator (`scripts/generate_test_alerts.py`, 8 templates) | ✅ |
| E2E test script (`scripts/test_alert_pipeline.sh`) | ✅ |

### M4 — Phone Testing (5 issues)
| Feature | Status |
|---|---|
| Discord bot credentials created and token configured | ✅ |
| Bot invited to server, running on local machine | ✅ |
| `/query` tested from Discord mobile app — sourced answer received | ✅ |
| 👍/👎 feedback tested from phone — logged to file | ✅ |

## Architecture Overview

```
                ┌──────────────────┐
                │  corpus/*.md     │
                │  (55 runbooks)   │
                └────────┬─────────┘
                         │ index
                         ▼
                ┌──────────────────┐
                │    ChromaDB      │
                │  (vector store)  │
                └────────┬─────────┘
                         │ retrieve
                         ▼
                ┌──────────────────┐
                │    Responder     │
                │ (prompt + LLM)   │
                └────────┬─────────┘
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
    ┌─────────┐   ┌──────────┐   ┌──────────────┐
    │  CLI    │   │ Discord  │   │ Alert        │
    │ query   │   │  bot     │   │ Pipeline     │
    └─────────┘   └──────────┘   └──────────────┘
                        │
                        ▼
                   ┌──────────┐
                   │Streamlit │
                   │Dashboard │
                   └──────────┘
```

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Chunking | Header-split (default) | MRR 0.9524 vs recursive 0.9048 |
| Vector store | ChromaDB | File-based, no server needed |
| Embedding | `all-MiniLM-L6-v2` | Local, fast, 384-dim |
| LLM default | OMLX (`Llama-3.2-3B-Instruct-4bit`) | Local, free, OpenAI-compatible API |
| Discord responses | Ephemeral | Only querying user sees answer |
| Alert pipeline | FIFO disk files | Zero external dependencies, testable with `curl` |

## Verified Live (2026-06-27)

All four channels tested with real queries from a phone and terminal:

1. **CLI**: `oncall-rag query "CrashLoopBackOff"` → sourced answer
2. **Discord `/query`**: from Discord mobile app → rich embed answer
3. **Feedback**: 👍/👎 from phone → logged to `data/feedback.jsonl`
4. **Dashboard**: `oncall-rag dashboard` → shows metrics and feedback

## Project Stats

| Metric | Value |
|---|---|
| GitHub issues | 37 closed, 0 open |
| Commits | 28 |
| Source files | 17 Python files |
| Source LOC | ~2,100 |
| Test files | 13 |
| Test LOC | ~975 |
| Corpus files | 55 markdown runbooks |
| Eval Q&A pairs | 14 |
| LLM backends | 3 (OMLX, OpenAI, Anthropic) |
| Delivery channels | 4 (CLI, Discord, Dashboard, Alert Pipeline) |

## Known Limitations

- **YAML frontmatter in Grafana runbooks** interferes with header-split chunking, causing 4/14 eval misses (MRR 0.571, Recall@5 0.714). A frontmatter-aware splitter would fix this.
- **No incremental re-indexing** — `index --rebuild` drops and recreates the full collection.
- **No authentication** on the dashboard — local-only.
- **Cold model load** — first OMLX request takes ~30s for 3B-parameter model.

## Tags

### Git Tags
- `v0.1.0` — Initial release with CLI RAG
- `v0.2.0` — Discord bot + dashboard
- `v0.3.0` — Alert pipeline
- `v1.0.0` — Full pipeline verified live from phone

### Technology Tags
| Tag | Description |
|---|---|
| `LLM` | Large Language Model — 3 backends: OMLX, OpenAI, Anthropic |
| `RAG` | Retrieval-Augmented Generation — core architecture |
| `VectorDB` | Vector database for semantic search |
| `ChromaDB` | Local file-based vector store |
| `Embeddings` | `all-MiniLM-L6-v2` sentence transformer |
| `Discord` | Discord bot with slash commands |
| `Streamlit` | Dashboard UI framework |
| `OMLX` | Local LLM provider (macOS) |
| `Llama-3.2-3B-Instruct-4bit` | Default OMLX model |
| `LangChain` | Document splitting utilities |
| `pytest` | Test framework (68 unit/integration + 12 e2e) |
| `FIFO` | File-based alert pipeline pattern |
| `CLI` | Command-line interface via `argparse` |
