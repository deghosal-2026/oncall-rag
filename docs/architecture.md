# Architecture Guide

## System Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   corpus/    │────▶│  oncall_rag  │────▶│   ChromaDB   │
│  (markdown)  │     │   (index)    │     │  (vector db) │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  oncall_rag  │◀───▶│  LLM Client   │
                     │   (query)    │     │  (omlx/OpenAI)│
                     └──────────────┘     └──────────────┘
```

## Module Dependency Graph

```
  __main__.py          # CLI entrypoint: index, query, eval, chunking-experiment
     │
     ├──► config.py    # Pydantic model + .env loader
     │
     ├──► indexer.py   # Document ingestion + chunking + embedding + ChromaDB storage
     │
     ├──► responder.py  # Orchestrates retrieval → LLM → answer formatting
     │     │
     │     ├──► retriever.py  # Embed query + ChromaDB similarity search
     │     │
     │     └──► llm/         # LLM provider clients
     │           ├── base.py       # ABC: LLMClient.generate()
     │           ├── omlx.py       # HTTP POST to local Ollama
     │           ├── openai.py     # OpenAI ChatCompletion API
     │           └── anthropic.py  # Anthropic Messages API
     │
     └──► eval.py      # Load eval set, run retrieval, compute MRR/Recall@5
```

## Data Flow

### Indexing

```
corpus/*.md
    │
    ▼
_walk_markdown(path)        # Recursive *.md walker, skips >1MB files
    │
    ▼
_split_file(file, config)   # Chunk via configured strategy
    │                          header-split | recursive | fixed-size
    ▼
list[Chunk(text, source_file, start_line, end_line)]
    │
    ▼
HuggingFaceEmbeddings(model_name)   # all-MiniLM-L6-v2
    │
    ▼
Chroma.add_texts(texts, metadatas)  # Store vectors
    │
    ▼
Return: {"files_indexed": N, "chunks_created": M}
```

### Querying

```
Question: "How to debug CrashLoopBackOff?"
    │
    ▼
retrieve(question, config)
    │
    ├──► HuggingFaceEmbeddings(model_name)     # Embed question
    ├──► Chroma.similarity_search_with_score()  # Top-k nearest vectors
    │
    ▼
list[RetrievedChunk(text, source_file, start_line, end_line, score)]
    │
    ├──► [empty]  →  "I don't have a runbook for this."
    │
    ▼
_build_llm_client(config)
    │
    ├──► LLMClient.generate(prompt with context)
    │
    ▼
Answer with source citations
```

### Evaluation

```
data/eval.json
    │
    ▼
For each Q&A pair:
    chunks = retrieve(q["question"], config)
    find rank of chunk matching q["source_file"]
    if found → reciprocal_rank = 1/rank; recall@5 += 1
    if not   → reciprocal_rank = 0
    │
    ▼
MRR = sum(reciprocal_ranks) / len(questions)
Recall@5 = correct_in_top5 / len(questions)
```

## Design Decisions

### Chunking: header-split by default

We tested 3 strategies (recursive, header-split, fixed-size) on 14 eval pairs. Header-split achieved the highest MRR (0.9524) because runbooks are naturally organized by markdown headers. Each chunk maps to a coherent section — the entire relevant procedure stays in one chunk. See `docs/chunking-experiment.md`.

### Embedding: all-MiniLM-L6-v2

Chosen for being lightweight (80 MB), fast, and good enough for technical documents. It's used both at index time (to embed chunks) and query time (to embed questions). The model runs locally, so there are no API costs or data privacy concerns.

### Vector store: ChromaDB (local)

We use ChromaDB with cosine similarity. It's file-based, requires no server, and persists to disk. Good for single-user or small-team use. For larger deployments, consider pgvector or Qdrant.

### LLM client abstraction

Each provider (Ollama, OpenAI, Anthropic) implements the same `LLMClient` ABC. This makes it easy to switch backends without changing any business logic. The system prompt enforces grounded answers: "Answer using ONLY the context below."

### Retrieval: dense-only (current)

Currently uses dense vector search only. Hybrid retrieval (dense + sparse BM25) is planned — it typically improves precision for technical documents where exact keyword matches matter.

### Eval metric: MRR

MRR measures how high the first relevant result appears. It's the right metric for question-answering where you only need one correct answer. Recall@5 is reported as a secondary metric.

## File Layout

```
oncall-rag/
├── .env                    # User config (gitignored)
├── pyproject.toml          # Package metadata + dependencies
├── README.md               # Quick start
├── corpus/                 # Runbook markdown files
├── data/
│   ├── chroma_db/          # Vector store (gitignored)
│   └── eval.json           # 14 Q&A eval pairs
├── docs/
│   ├── PRD.md
│   ├── SPEC.md
│   ├── TODO.md
│   ├── architecture.md     # This file
│   ├── chunking-experiment.md
│   └── user-guide.md
├── scripts/
│   └── generate_eval.py
├── src/
│   └── oncall_rag/
│       ├── __init__.py
│       ├── __main__.py     # CLI entrypoint
│       ├── config.py       # Pydantic config model
│       ├── indexer.py      # Ingestion + chunking
│       ├── retriever.py    # Vector search
│       ├── responder.py    # LLM answer generation
│       ├── eval.py         # MRR/Recall@5
│       └── llm/
│           ├── __init__.py
│           ├── base.py     # ABC
│           ├── omlx.py
│           ├── openai.py
│           └── anthropic.py
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── e2e/
```
