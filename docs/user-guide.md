# User Guide

## Overview

oncall-rag indexes your runbook markdown files and lets you ask questions in natural language. It retrieves the most relevant sections and generates a grounded answer with source citations — so you can verify and act quickly during an incident.

### Setup Layout

```
project root/
├── corpus/                     # your runbook .md files
├── data/
│   ├── chroma_db/              # vector store (created by index)
│   ├── eval.json               # Q&A pairs for eval
│   └── feedback.jsonl          # user feedback (thumbs up/down)
├── alerts/
│   ├── inbox/                  # incoming alert JSON files
│   ├── outbox/                 # processed alert results
│   └── archive/                # processed originals
├── .env                        # config: LLM provider, keys, chunking
├── src/oncall_rag/             # source
└── AGENTS.md                   # opencode context
```

### Query Flow

When you run `oncall-rag query "How do I debug a CrashLoopBackOff pod?"`:

```
  ┌─────────────────┐
  │   oncall-rag     │
  │   query "..."    │
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  1. Embed query │  all-MiniLM-L6-v2 → 384-dim vector
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  2. ChromaDB    │  cosine-similarity search on stored chunks
  │  vector search  │  returns TOP_K (default: 5) best-matching chunks
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  3. Build       │  retrieved chunks stitched into a prompt
  │  LLM prompt     │  with system instruction + source citations
  └────────┬────────┘
           │
           ▼
  ┌──────────────────────────────┐
  │  4. LLM generates answer     │  OMLX / OpenAI / Anthropic
  │  (grounded on context only)  │  ~30s first request (cold model load)
  └────────┬─────────────────────┘
           │
           ▼
  ┌──────────────────────┐
  │  5. Print response   │  answer text + source file:line refs
  │  to terminal         │  (or Discord embed / Streamlit)
  └──────────────────────┘
```

### Workflow

```
1. Prepare runbooks  →  2. Index  →  3. Query  →  4. Evaluate (optional)
```

---

## 1. Preparing Runbooks

Place your markdown files in a directory (e.g., `./corpus`). The tool recursively finds all `.md` files. Files over 1 MB are skipped with a warning.

Recommended structure:

```
corpus/
├── kubernetes/
│   ├── debug-pods.md
│   └── troubleshooting.md
├── grafana/
│   └── alerts.md
└── sre/
    └── incident-response.md
```

Runbooks with markdown headers (`##`, `###`) work best — the tool uses header-split chunking by default, which preserves section boundaries.

---

## 2. Indexing

```bash
oncall-rag index ./corpus
```

The tool:
1. Walks the directory recursively for `.md` files
2. Splits each file into chunks
3. Embeds each chunk as a vector
4. Stores everything in a local ChromaDB vector database

**Output:**
```
Indexed 18 files, 142 chunks
```

### Rebuilding

Run `--rebuild` to drop the existing index and re-index from scratch (e.g., after changing chunking settings or updating runbooks):

```bash
oncall-rag index ./corpus --rebuild
```

---

## 3. Querying

```bash
oncall-rag query "How do I debug a CrashLoopBackOff pod?"
```

The tool:
1. Embeds your question
2. Searches the vector store for the most similar chunks
3. Sends the retrieved chunks to an LLM as context
4. Returns a grounded answer with source citations

**Output:**
```
Source: kubernetes/debug-pods.md:42-47
──────────────────────────────────────────────
Step 1: Run `kubectl describe pod <name>` to check events.
Step 2: Run `kubectl logs <name> --previous` for crash loop logs.

Sources:
  - kubernetes/debug-pods.md:42-47
  - kubernetes/debug-pods.md:89-95
```

If no relevant content is found:
```
I don't have a runbook for this.
```

---

## 4. Evaluating

```bash
oncall-rag eval
```

Runs 14 predefined Q&A pairs against your index and reports retrieval quality metrics:

- **MRR (Mean Reciprocal Rank):** How high the first correct result appears. 1.0 = always rank 1.
- **Recall@5:** Fraction of queries where the correct source is in the top 5 results.

**Output:**
```
MRR: 0.952, Recall@5: 1.000
```

Use this to measure whether changes to chunking, embedding, or retrieval improve or degrade quality.

---

## 5. Chunking Strategies

Chunking controls how documents are split before embedding. The right strategy depends on your document structure.

| Strategy | How it works | Best for |
|---|---|---|
| `header-split` (default) | Splits on `##`/`###` headers, merges small sections | Runbooks with clear step-by-step headers |
| `recursive` | Splits on paragraph → sentence → word boundaries | Prose-heavy docs without headers |
| `fixed-size` | Blind character split at N chars | Baseline comparison only |

To switch strategy, set in `.env`:

```
CHUNKING_STRATEGY=header-split
```

Then re-index with `--rebuild`.

To compare strategies on your own data:

```bash
oncall-rag chunking-experiment ./corpus
```

This indexes with each strategy, runs eval, and writes a comparison to `docs/chunking-experiment.md`.

---

## 6. Discord Bot

```bash
oncall-rag discord
```

The bot registers two slash commands:
- `/ping` — health check, responds with `Pong!`
- `/query <question>` — runs the RAG pipeline and returns a rich embed answer with source citations

Each `/query` response includes 👍/👎 buttons for feedback collection. Feedback is logged to `data/feedback.jsonl`.

Full setup guide: [docs/setup.md](setup.md)

---

## 7. Alert Pipeline

The FIFO alert pipeline processes JSON alert files through the RAG pipeline:

```bash
# Drop alert files into alerts/inbox/ (one JSON per alert)
# Each file needs: title, message, severity, source, timestamp

# Generate 8 sample alerts:
python scripts/generate_test_alerts.py

# Generate more:
python scripts/generate_test_alerts.py --count 20

# Process all pending alerts:
oncall-rag process-alerts
```

Processing flow:
1. Reads all `.json` files from `alerts/inbox/`
2. For each alert, queries the RAG pipeline with the alert title + message
3. Writes `AlertResult` (RAG answer + sources) to `alerts/outbox/`
4. Moves the original alert file to `alerts/archive/`

---

## 8. Configuration Reference

All settings are read from `.env` in the project root. A minimal config:

```
LLM_PROVIDER=omlx
OMLX_ENDPOINT=http://localhost:8000
OMLX_MODEL=Llama-3.2-3B-Instruct-4bit
OMLX_API_KEY=omlx-test
```

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `omlx` | `omlx`, `openai`, or `anthropic` |
| `OMLX_ENDPOINT` | `http://localhost:8000` | OMLX server URL |
| `OMLX_MODEL` | `Llama-3.2-3B-Instruct-4bit` | OMLX model name |
| `OMLX_API_KEY` | `omlx-test` | API key for OMLX |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-3-haiku-20240307` | Anthropic model |
| `CHUNKING_STRATEGY` | `header-split` | `header-split`, `recursive`, or `fixed-size` |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks (chars) |
| `TOP_K` | `5` | Number of chunks to retrieve per query |
| `CHROMA_PATH` | `./data/chroma_db` | Vector store directory |

---

## CLI Reference

```
oncall-rag index <path> [--rebuild]    # Index runbooks into ChromaDB
oncall-rag query "<question>"          # Query the RAG pipeline
oncall-rag eval                        # Run eval set, print MRR/Recall@5
oncall-rag chunking-experiment <path>  # Compare chunking strategies
oncall-rag discord                     # Start the Discord bot
oncall-rag dashboard                   # Launch Streamlit dashboard
oncall-rag process-alerts              # Process alert files through RAG
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `No documents indexed` | No `.md` files found at path | Check the path; files must be `.md` and under 1 MB |
| LLM returns empty | Model not running | Ensure OMLX is running on `localhost:8000` with a model loaded |
| Low MRR | Wrong chunking strategy | Run `chunking-experiment` to find the best strategy for your docs |
| `I don't have a runbook for this` | No relevant chunks retrieved | Check your corpus; try `TOP_K=10` or adjust chunk settings |
| Slow queries | Large index or slow LLM | Reduce `TOP_K` or use a faster model |
