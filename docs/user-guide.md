# User Guide

## Overview

oncall-rag indexes your runbook markdown files and lets you ask questions in natural language. It retrieves the most relevant sections and generates a grounded answer with source citations — so you can verify and act quickly during an incident.

## Workflow

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

## 6. Configuration Reference

All settings are read from `.env` in the project root. A minimal config:

```
LLM_PROVIDER=omlx
OMLX_ENDPOINT=http://localhost:11434
OMLX_MODEL=qwen2.5-coder:7b
```

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `omlx` | `omlx`, `openai`, or `anthropic` |
| `OMLX_ENDPOINT` | `http://localhost:11434` | Ollama server URL |
| `OMLX_MODEL` | `qwen2.5-coder:7b` | Ollama model name |
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
oncall-rag index <path> [--rebuild]
oncall-rag query "<question>"
oncall-rag eval
oncall-rag chunking-experiment <path>
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `No documents indexed` | No `.md` files found at path | Check the path; files must be `.md` and under 1 MB |
| LLM returns empty | Model not running | `ollama pull qwen2.5-coder:7b` then `ollama serve` |
| Low MRR | Wrong chunking strategy | Run `chunking-experiment` to find the best strategy for your docs |
| `I don't have a runbook for this` | No relevant chunks retrieved | Check your corpus; try `TOP_K=10` or adjust chunk settings |
| Slow queries | Large index or slow LLM | Reduce `TOP_K` or use a faster model |
