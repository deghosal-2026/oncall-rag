# SPEC: RAGoncall

- **Status:** Approved

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   corpus/    │────▶│  oncall_rag  │────▶│   ChromaDB   │
│  (markdown)  │     │   (index)    │     │  (vector db) │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  oncall_rag  │◀───▶│  LLM Client   │
                      │   (query)    │     │  (omlx/OpenAI) │
                     └──────────────┘     └──────────────┘
```

## E2E Data Flow

### `index <path>` — Ingest

```
┌────────────────────────────────────────────────────────────────────────────┐
│  oncall-rag index ./corpus                                                 │
│  __main__.py: index_documents(path, config, rebuild=False)                 │
│                                                                            │
│  corpus/*.md ──► _walk_markdown(path) ──► list[Path]                      │
│  (recursive        (skips >1MB,             │                              │
│   *.md only)        non-md)                 │                              │
│                                             ▼                              │
│                              _split_file(file, chunk_size, chunk_overlap)  │
│                              RecursiveCharacterTextSplitter                │
│                              separators=["\n\n", "\n", ". ", " "]          │
│                                             │                              │
│                                             ▼                              │
│                              list[Chunk(text, source_file,                 │
│                                        start_line, end_line)]              │
│                                             │                              │
│                                             ▼                              │
│                    HuggingFaceEmbeddings(model_name)                        │
│                    (all-MiniLM-L6-v2)        │                              │
│                                              ▼                             │
│                    Chroma(persist_directory, collection_name="runbooks")    │
│                    vectorstore.add_texts(texts, metadatas)                 │
│                    vectorstore.persist()                                    │
│                                              │                             │
│                                              ▼                             │
│                    Return: {"files_indexed": N, "chunks_created": M}       │
└────────────────────────────────────────────────────────────────────────────┘
```

### `query "<question>"` — Retrieve + Generate

```
┌────────────────────────────────────────────────────────────────────────────┐
│  oncall-rag query "How to debug CrashLoopBackOff?"                        │
│  __main__.py: query_runbooks(question, config)                             │
│                                                                            │
│  question ──► retrieve(question, config) ──► list[RetrievedChunk]         │
│                   │                                                       │
│                   ├─► HuggingFaceEmbeddings(model_name)                   │
│                   ├─► Chroma.similarity_search_with_score(query, k=top_k) │
│                   │                                                       │
│                   ▼                                                       │
│  RetrievedChunk[]                                                          │
│    text: str          (page_content from Chroma doc)                       │
│    source_file: str   (metadata["source_file"])                            │
│    start_line: int    (metadata["start_line"])                             │
│    end_line: int      (metadata["end_line"])                              │
│    score: float       (cosine distance from Chroma)                        │
│                                                                            │
│  if empty ──► return "I don't have a runbook for this."                   │
│                                                                            │
│  _build_llm_client(config)                                                 │
│    LLM_PROVIDER=omlx    ──► OmlxClient(endpoint, model)                   │
│    LLM_PROVIDER=openai  ──► OpenAIClient(api_key, model)                  │
│    LLM_PROVIDER=anthropic──► AnthropicClient(api_key, model)               │
│                                                                            │
│  Prompt template:                                                          │
│    "Context:\n---\n[chunk1 text] (source: file.md:N-M)\n---\n              │
│     ...\n\nQuestion: {question}"                                           │
│                                                                            │
│  client.generate(prompt, temperature=0, max_tokens=1024)                  │
│                                                                            │
│  if LLM returns answer ──► answer + "Sources:\n  - file.md:N-M"           │
│  if LLM fails/empty    ──► fallback: raw sources list                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### `eval` — Measure Retrieval Quality

```
┌────────────────────────────────────────────────────────────────────────────┐
│  oncall-rag eval                                                           │
│  __main__.py: run_eval(config, eval_path="data/eval.json")                │
│                                                                            │
│  data/eval.json ──► load ──► list[questions]                              │
│  {                                                                         │
│    "questions": [                          │                               │
│      {"id": "k8s-001",                     │                               │
│       "question": "...",                   │                               │
│       "answer": "...",                     │                               │
│       "source_file": "kubernetes/....md",  │                               │
│       "source_lines": "42-47"}             │                               │
│    ]                                        │                              │
│  }                                          │                              │
│                                             ▼                              │
│  For each question:                                                        │
│    chunks = retrieve(q["question"], config)                                │
│    find rank of chunk where source_file matches q["source_file"]           │
│    if found: reciprocal_rank = 1/rank; recall@5 += 1                      │
│    if not:   reciprocal_rank = 0                                           │
│                                             │                              │
│                                             ▼                              │
│  MRR = sum(reciprocal_ranks) / len(questions)                              │
│  Recall@5 = correct_in_top5 / len(questions)                               │
│  Return: {"mrr": float, "recall_at_5": float}                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Response Format (M1 — Plain Text)

```
Source: kubernetes/troubleshooting/pods.md:42-47
──────────────────────────────────────────────
Step 1: Run `kubectl describe pod <name>` to check events.

Sources:
  - kubernetes/troubleshooting/pods.md:42-47
  - kubernetes/troubleshooting/pods.md:89-95
```

### Module Dependency Graph

```
  __main__.py
     │
     ├──► config.py         (Config model, load_config from .env)
     │
     ├──► indexer.py        (_walk_markdown, _split_file, _make_embedding_model,
     │       │               index_documents)
     │       │
     │       ├──► langchain_text_splitters.RecursiveCharacterTextSplitter
     │       ├──► langchain_community.embeddings.HuggingFaceEmbeddings
     │       └──► langchain_community.vectorstores.Chroma
     │
     ├──► responder.py      (_build_llm_client, query_runbooks)
     │       │
     │       ├──► retriever.py  (retrieve, RetrievedChunk)
     │       │       │
     │       │       ├──► langchain_community.embeddings.HuggingFaceEmbeddings
     │       │       └──► langchain_community.vectorstores.Chroma
     │       │
     │       └──► llm/
     │               ├── base.py       (LLMClient ABC)
     │               ├── omlx.py       (OmlxClient — httpx POST /api/generate)
     │               ├── openai.py     (OpenAIClient — openai.ChatCompletion)
     │               └── anthropic.py  (AnthropicClient — anthropic.messages)
     │
     └──► eval.py           (run_eval)
             │
             └──► retriever.py
```

## CLI Commands

```
oncall-rag index <path>                    # Ingest markdown files into ChromaDB
oncall-rag index <path> --rebuild          # Drop and recreate collection
oncall-rag query "<question>"              # Retrieve + generate answer
oncall-rag eval                             # Run eval set, print MRR/recall@k
oncall-rag chunking-experiment <path>      # Compare 3 chunking strategies
```

- `index` walks `<path>` recursively, chunks each `.md` file, embeds via `all-MiniLM-L6-v2`, stores in ChromaDB
- `query` embeds the question, retrieves top-k chunks (k=5 default), sends to LLM with context, prints answer + source citations
- `eval` runs the eval Q&A pairs and reports retrieval metrics

## Data Flow

### `index <path>`

1. Walk `<path>` recursively, collect all `.md` files
2. For each file, load raw markdown text
3. Split into chunks using the configured chunking strategy
4. Embed each chunk via `all-MiniLM-L6-v2` → vector
5. Store `(vector, text, source_file, start_line, end_line)` in ChromaDB
6. Print summary: files indexed, chunks created

### `query "<question>"`

1. Embed the question via `all-MiniLM-L6-v2`
2. Query ChromaDB for top-k similar vectors (cosine similarity)
3. Retrieve the raw text of each matching chunk
4. Build prompt:
   ```
   You are an on-call assistant. Answer the question using ONLY the context below.
   If the context doesn't contain the answer, say "I don't have a runbook for this."

   Context:
   ---
   [chunk 1 text] (source: file.md:42-47)
   [chunk 2 text] (source: file.md:89-95)
   ---

   Question: {question}
   ```
5. Send prompt to LLM client
6. Format response with answer + source citations
7. Return to user

## Chunking Strategy

### Recommended: header-split (experiment winner)

Split on markdown headers (`#`, `##`, etc.), then merge small sections up to ~1.5× chunk_size. Sections exceeding chunk_size are further split with `RecursiveCharacterTextSplitter` using the configured overlap. This preserves section boundaries — best for runbooks with `## Step 1` structure.

**Experiment result:** header-split achieved MRR 0.9524 vs recursive 0.9048 vs fixed-size 0.8893. See `docs/chunking-experiment.md`.

Parameters (current defaults):
| Param | Value | Rationale |
|---|---|---|
| `chunk_size` | 500 chars | Small enough for precision, large enough for context |
| `chunk_overlap` | 50 chars | Prevent context loss at boundaries |
| `chunking_strategy` | `header-split` | Winner of chunking experiment |

### Experiment Plan

Compare 3 strategies on the eval set and pick the best:

| Strategy | Why test | MRR |
|---|---|---|
| Header-split (winner) | Better for docs with `## Step 1` structure | **0.9524** |
| Recursive (paragraph-first) | Good for prose runbooks with clear sections | 0.9048 |
| Fixed-size (500 chars) | Baseline — simplest, no semantic awareness | 0.8893 |

Measure MRR, recall@5, and qualitative coherence (does the chunk make sense alone?) for each. Documented in `docs/chunking-experiment.md`.

## LLM Client Interface

```python
# src/oncall_rag/llm/base.py
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        ...
```

Each provider implements `generate`:

- **OmlxClient** — POST to `/api/generate`, stream JSON response
- **OpenAIClient** — `openai.ChatCompletion.create()`
- **AnthropicClient** — `anthropic.Anthropic().messages.create()`

All clients share:
- `system` prompt injected as a constructor arg or default
- `temperature=0` for deterministic on-call answers
- `max_tokens=1024`

## Error Handling

| Scenario | Behavior |
|---|---|
| No `.env` file | Use defaults; warn on missing optional keys |
| Corrupted `.env` | Clear error with line number |
| omlx server down | Error: "omlx not reachable at {endpoint}. Is omlx running?" |
| ChromaDB empty | Error: "No documents indexed. Run `index` first." |
| No relevant chunks found | Response: "I don't have a runbook for this." |
| LLM returns empty/error | Fallback: return raw retrieved chunks without LLM |
| Corpus file unreadable | Skip file, warn, continue |
| File >1MB | Skip with warning: "File too large ({size}). Max: 1MB" |
| Binary/corrupt file | Detect by extension/magic bytes, skip with warning |
| Unicode filename | Handled natively by `pathlib`; test for edge cases |
| Empty corpus | Error: "No markdown files found at {path}" |
| Empty chunk (all whitespace after split) | Skip, don't store in ChromaDB |
| Duplicate file content (same text, different path) | Track by content hash, skip if already indexed |

## Re-indexing

- **Full rebuild:** `index --rebuild` drops and recreates the collection
- **Append-only:** Default `index` adds new files without removing existing
- **Deduplication:** Track by file path hash — skip files already indexed (unless `--rebuild`)
- **Incremental:** Not supported in M1. If a file changes, user runs `index --rebuild`

## Dependencies

```toml
# pyproject.toml
[project]
name = "oncall-rag"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.3.0",
    "langchain-community>=0.3.0",
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "openai>=1.30.0",
    "anthropic>=0.39.0",
]

[project.scripts]
oncall-rag = "oncall_rag.__main__:main"
```

Loaded from `.env` (via `python-dotenv`):

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `omlx` | `omlx`, `openai`, or `anthropic` |
| `OMLX_ENDPOINT` | `http://localhost:11434` | omlx server URL |
| `OMLX_MODEL` | `qwen2.5-coder:7b` | omlx model name |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-3-haiku-20240307` | Anthropic model |
| `CHROMA_PATH` | `./chroma_db` | Vector store directory |
| `CHUNK_SIZE` | `500` | Chunk size in characters |
| `CHUNK_OVERLAP` | `50` | Chunk overlap in characters (must be < chunk_size) |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model name |
| `CHUNKING_STRATEGY` | `header-split` | `header-split`, `recursive`, or `fixed-size` |

## Project Structure

```
oncall-rag/
├── .env
├── .gitignore
├── pyproject.toml
├── README.md
├── docs/
│   ├── PRD.md
│   ├── SPEC.md
│   ├── TODO.md
│   ├── architecture.md
│   ├── chunking-experiment.md
│   ├── e2e-test-plan.md
│   └── user-guide.md
├── scripts/
│   └── generate_eval.py
├── src/
│   └── oncall_rag/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry: index, query, eval, chunking-experiment
│       ├── config.py            # .env loader + pydantic model
│       ├── indexer.py           # Document ingestion + chunking (3 strategies)
│       ├── retriever.py         # ChromaDB embed + search (cached)
│       ├── responder.py         # Format chunks + LLM → answer
│       ├── eval.py              # Eval harness (MRR/Recall@5 with line-range matching)
│       └── llm/
│           ├── __init__.py
│           ├── base.py          # ABC for LLM clients
│           ├── omlx.py          # OmlxClient
│           ├── openai.py        # OpenAIClient
│           └── anthropic.py     # AnthropicClient
├── corpus/                      # Public runbook datasets
│   ├── kubernetes/
│   ├── grafana/
│   ├── google-sre/
│   └── public-runbooks/
├── data/
│   ├── chroma_db/               # Local vector store (gitignored)
│   └── eval.json               # 14 Q&A eval pairs
└── tests/
    ├── conftest.py              # Fixtures: config, small_corpus, mock_vectorstore, eval_json
    ├── unit/                    # 38 tests: chunking, retriever, LLM, config, eval
    ├── integration/             # 6 tests: index, rebuild, query, fallback
    └── e2e/                     # 9 tests: help, index, eval, chunking-experiment
```

## Response Format

### M1 — Plain text

```
Source: kubernetes/troubleshooting/pods.md:42-47
──────────────────────────────────────────────
Step 1: Run `kubectl describe pod <name>` to check events.
Step 2: Run `kubectl logs <name> --previous` for crash loop logs.
Step 3: Check resource limits with `kubectl get pod <name> -o yaml`.
```

Citation template: `<filename>:<start_line>-<end_line>`

Multiple sources:
```
Sources:
  - kubernetes/troubleshooting/pods.md:42-47
  - kubernetes/troubleshooting/pods.md:89-95
──────────────────────────────────────────────
```

### M2 — Rich text

Discord embed:
```json
{
  "title": "Answer",
  "description": "<response text>",
  "fields": [
    { "name": "Source 1", "value": "[pods.md:42-47](<github link>)", "inline": true },
    { "name": "Source 2", "value": "[pods.md:89-95](<github link>)", "inline": true }
  ],
  "footer": { "text": "Thumbs up/down to rate this answer" }
}
```

## Eval Set

Stored at `data/eval.json`. Schema:

```json
{
  "questions": [
    {
      "id": "k8s-001",
      "question": "How do I check why a pod is in CrashLoopBackOff?",
      "answer": "Run `kubectl describe pod <name>` to check events, then `kubectl logs <name> --previous` for crash loop logs.",
      "source_file": "kubernetes/troubleshooting/pods.md",
      "source_lines": "42-47"
    }
  ]
}
```

Generated by AI from the corpus. Validated manually before adding to eval set.

## Testing

| Layer | Scope | Tools |
|---|---|---|
| Unit | Chunking, embedding, retrieval, LLM client | pytest |
| Integration | Index → query end-to-end on small test corpus | pytest |
| E2E | Full CLI flow from scratch | pytest (subprocess) |
| Eval-as-tests | Q&A pairs run in CI; MRR ≥ 0.7 enforced | pytest + eval harness |

## Cost

Per-query cost must be under $0.05 when using remote LLM providers. Local Ollama queries are free beyond electricity.

Budget calculations:
- Embedding: free (local model)
- Retrieval: free (local ChromaDB)
- LLM (remote): `gpt-4o-mini` ~$0.15/1M input tokens → ~$0.0003 per query at ~2k input tokens. Well within budget.
- LLM (local): free

## Performance

End-to-end query latency under 15 seconds. Budget:
- Embedding: ~200ms (local `all-MiniLM-L6-v2`)
- Retrieval: ~50ms (local ChromaDB, small collection)
- LLM: depends on provider. omlx local ~5-10s, `gpt-4o-mini` ~2-5s.

## Milestones — Task Breakdown

Labels: `milestone`, `ticket`

### M1 — CLI RAG (16 tickets)

| # | Title | Description | Acceptance Criteria |
|---|---|---|---|
| M1.1 | Project scaffolding | `pyproject.toml`, `src/oncall_rag/` layout, `.env`, `config.py` with pydantic model, `__main__.py` with CLI skeleton | `oncall-rag --help` prints available commands; config loads from `.env` |
| M1.2 | LLM client interface | `llm/base.py` ABC, `llm/omlx.py`, `llm/openai.py`, `llm/anthropic.py` | All 3 clients implement `generate()` with error handling |
| M1.3 | Chunking engine | `indexer.py` — file walker + `RecursiveCharacterTextSplitter` | Splits markdown files into chunks, handles edge cases (empty, binary, huge files) |
| M1.4 | Embedding + indexing | `indexer.py` — integrate `all-MiniLM-L6-v2` + ChromaDB store | `index <path>` stores all chunks in ChromaDB; dedup by content hash |
| M1.5 | Retrieval | `retriever.py` — embed query + ChromaDB similarity search | Returns top-k chunks with source + score |
| M1.6 | Responder | `responder.py` — build prompt, call LLM, format answer | Returns grounded answer with source citations in plain text |
| M1.7 | CLI: `index` command | Wire indexer + embedding into `oncall-rag index <path>` | Indexes corpus, prints file/chunk summary |
| M1.8 | CLI: `query` command | Wire retriever + responder into `oncall-rag query "..."` | Returns answer with sources or "I don't have a runbook for this" |
| M1.9 | Eval harness | `eval.py` — load `data/eval.json`, run queries, compute MRR/recall@k | `oncall-rag eval` prints per-question results + aggregate metrics |
| M1.10 | Eval set generation | AI-generate 14 Q&A pairs from corpus, validate manually | `data/eval.json` with validated entries |
| M1.11 | Unit + integration tests | Tests for chunking, retriever, LLM clients, pipeline | ≥80% coverage on core modules |
| M1.12 | Chunking experiment | Run 3 strategies (recursive, header-split, fixed-size), document in `docs/chunking-experiment.md` | Recommendation documented with MRR/recall@5 for each |
| M1.13 | Setup instructions (README) | Prerequisites, install, .env config, quick start, troubleshooting | README covers end-to-end setup for M1 |
| M1.14 | User guide | `docs/user-guide.md` with CLI commands, workflows, chunking, eval | User can follow guide without reading source code |
| M1.15 | Architecture guide | `docs/architecture.md` with system diagram, data flow, design decisions | Architecture documented with rationale for each choice |
| M1.16 | E2E test plan + tests | `docs/e2e-test-plan.md` + `tests/e2e/` — happy path, edge cases, errors | All E2E scenarios passing in CI |

### M2 — Discord Bot + Dashboard (11 tickets)

| # | Title | Description | Acceptance Criteria |
|---|---|---|---|
| M2.1 | Discord bot scaffold | `pyproject.toml` dep + bot skeleton with `discord.py` | Bot comes online, responds to `/ping` |
| M2.2 | Slash command: `/query` | Register `query` slash command, wire to RAG pipeline | Returns rich embed with answer + source citations |
| M2.3 | Feedback collection | Thumbs-up/down buttons on each response, store in JSONL | Feedback persisted and queryable |
| M2.4 | Rich response formatting | Discord embed with fields, code blocks, clickable source links | Formatted as spec in Response Format section |
| M2.5 | Dashboard scaffold | FastAPI + HTML (or Streamlit) server, basic route | Server starts, `/dashboard` renders |
| M2.6 | Dashboard: query metrics | Queries per day, sources cited, feedback ratio | Charts/metrics from stored logs |
| M2.7 | Dashboard: knowledge gaps | Most-queried but missing runbooks, lowest-rated retrievals | Table of gap items |
| M2.8 | Dashboard: feedback analysis | Thumbs-up/down breakdown per source | Source quality ranking visible |
| M2.9 | E2E tests (M2) | Discord commands (mocked), dashboard pages | Test coverage for all new features |
| M2.10 | README + docs update | Setup guide for Discord bot, dashboard, full M2 workflow | README covers end-to-end from install to querying via Discord |

### M3 — PagerDuty Integration (Future)

| # | Title | Description | Acceptance Criteria |
|---|---|---|---|
| M3.1 | PagerDuty webhook receiver | Receive alert payload, extract alert context | PagerDuty webhook verified |
| M3.2 | Auto-query on alert | Trigger RAG query with alert context, return suggested runbook | Auto-response posted to alert channel |
| M3.3 | Alert-response logging | Log PagerDuty alerts + RAG responses for audit | Correlatable alert → response trail |

## Glossary

| Term | Definition |
|---|---|
| Chunk | A contiguous segment of text split from a source document for embedding/retrieval |
| Embedding | A vector (list of floats) representing the semantic meaning of a text |
| MRR | Mean Reciprocal Rank — measures how high the first relevant result appears |
| Recall@k | Fraction of relevant documents found in the top-k retrieved results |
| NDCG | Normalized Discounted Cumulative Gain — ranking quality metric |
| Grounding | Ensuring LLM output is faithful to retrieved source content |
| Chunking | The strategy for splitting documents into retrievable pieces |
| Dense retrieval | Vector similarity search using dense embeddings |
| Hybrid retrieval | Combining dense vector search with sparse keyword matching (BM25) |
| Eval set | A curated set of question-answer pairs with known correct source documents |
