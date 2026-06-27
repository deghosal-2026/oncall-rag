# oncall-rag

Runbook RAG assistant for on-call engineers — answers queries from runbooks via CLI (and eventually Slack/Discord) with source citations.

## Prerequisites

- **Python 3.11+**
- **LLM backend** (one of):
  - [Ollama](https://ollama.com) (local, free) — recommended for development
  - OpenAI API key (`gpt-4o-mini` or similar)
  - Anthropic API key (`claude-3-haiku` or similar)
- ~2 GB disk for embedding model + vector store

## Installation

```bash
# Clone the repo
git clone https://github.com/deghosal-2026/oncall-rag.git
cd oncall-rag

# Install the package
pip install -e .
```

## Configuration

Copy `.env.example` or create `.env`:

```bash
# LLM provider: omlx, openai, or anthropic
LLM_PROVIDER=omlx
OMLX_ENDPOINT=http://localhost:11434
OMLX_MODEL=qwen2.5-coder:7b

# For remote providers:
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-haiku-20240307

# Chunking (optional, default: header-split)
CHUNKING_STRATEGY=header-split
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Retrieval
TOP_K=5

# Vector store path
CHROMA_PATH=./data/chroma_db
```

## Quick Start

### 1. Index your runbooks

```bash
# Index all markdown files in ./corpus
oncall-rag index ./corpus

# Rebuild from scratch (drops existing index)
oncall-rag index ./corpus --rebuild
```

### 2. Query

```bash
oncall-rag query "Why is my pod stuck in CrashLoopBackOff?"
```

The tool retrieves relevant runbook sections and generates a grounded answer with source citations.

### 3. Evaluate retrieval quality

```bash
oncall-rag eval
```

Runs 14 Q&A pairs and reports MRR (Mean Reciprocal Rank) and Recall@5.

### 4. Run chunking strategy comparison

```bash
oncall-rag chunking-experiment ./corpus
```

Indexes with each strategy, runs eval, and writes a report to `docs/chunking-experiment.md`.

## CLI Commands

| Command | Description |
|---|---|
| `index <path>` | Ingest markdown files into ChromaDB |
| `index <path> --rebuild` | Drop and recreate the collection |
| `query "<question>"` | Retrieve + generate answer |
| `eval` | Run eval set, print MRR/Recall@5 |
| `chunking-experiment <path>` | Compare chunking strategies on the eval set |

## Chunking Strategies

| Strategy | Description | MRR |
|---|---|---|
| `header-split` (default) | Split on markdown headers — best for runbooks | **0.9524** |
| `recursive` | LangChain RecursiveCharacterTextSplitter | 0.9048 |
| `fixed-size` | Blind character split at chunk_size | 0.8893 |

See [docs/chunking-experiment.md](docs/chunking-experiment.md) for full results.

## Project Structure

```
oncall-rag/
├── .env                    # Configuration (gitignored)
├── pyproject.toml          # Package metadata + dependencies
├── README.md
├── corpus/                 # Runbook markdown files
├── data/
│   ├── chroma_db/          # Vector store (gitignored)
│   └── eval.json           # Eval Q&A pairs
├── docs/
│   ├── PRD.md              # Product requirements
│   ├── SPEC.md             # Technical specification
│   ├── TODO.md             # Task tracker
│   └── chunking-experiment.md
├── scripts/
│   └── generate_eval.py    # Eval set generation script
├── src/
│   └── oncall_rag/
│       ├── __main__.py     # CLI entrypoint
│       ├── config.py       # .env + pydantic config
│       ├── indexer.py      # Document ingestion + chunking
│       ├── retriever.py    # ChromaDB embed + search
│       ├── responder.py    # LLM answer generation
│       ├── eval.py         # MRR/Recall@5 evaluation
│       └── llm/            # LLM clients (omlx, openai, anthropic)
└── tests/
    ├── unit/               # Unit tests (chunking, retriever, LLM, config, eval)
    ├── integration/        # Integration tests (index → query pipeline)
    └── e2e/                # End-to-end CLI tests
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -e .` |
| `omlx not reachable` | Start Ollama: `ollama serve`, then `ollama pull qwen2.5-coder:7b` |
| `No documents indexed` | Run `oncall-rag index ./corpus` first |
| `I don't have a runbook for this` | No relevant content found — check your corpus and retrieval config |
| Low MRR | Try `header-split` chunking or adjust `CHUNK_SIZE`/`CHUNK_OVERLAP` |
