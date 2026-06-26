# PRD: RAGoncall — Runbook RAG Assistant

- **Status:** Approved
- **Author:** deghosal
- **Repo:** github.com/deghosal-2026/oncall-rag

## Problem

When on-call engineers respond to incidents, they waste minutes searching wiki pages, runbooks, and postmortems for the right procedure. First-response time is slow, and resolution quality varies heavily based on who's on call. RAG over runbooks is the highest-ROI AI investment for engineering teams, but it needs to prove measurable value — not a toy demo.

## Goal

Ship a local-first RAG assistant that indexes runbook-style documentation and answers on-call queries with sourced, ground-truth-verified responses. Prove the RAG pipeline works before adding any team-facing surface area.

## Target Users

- **Primary:** deghosal (local dev, proving RAG works)
- **Secondary:** Future engineering teams that adopt the tool

## Source Corpus

Public runbook-style datasets:
- Kubernetes troubleshooting guides
- Grafana On-Call public runbooks
- Google SRE book (incident response chapters)
- GitHub public runbook repos (e.g., Adidas, Grafana)

All ingested from raw text/markdown.

## Non-Goals

- PagerDuty integration (M3+)
- Multi-team onboarding
- Production hosting
- Authentication/authorization (local-only)
- Real user data ingestion

## Milestones

### M1 — CLI RAG (Current)

Query runbooks from the terminal. Core RAG pipeline.

**Interface:** CLI — two commands: `index` (ingest documents) and `query` (ask questions).

**RAG Pipeline:**
- Embedding: local (`all-MiniLM-L6-v2` via sentence-transformers)
- Vector store: ChromaDB (local, file-based)
- Framework: LangChain
- LLM: pluggable (local via Ollama, or OpenAI/Anthropic)
- Retrieval: dense vector search
- Chunking: experiment with fixed-size and semantic chunking

**Eval:**
- 10–15 Q&A pairs (AI-generated from source corpus)
- Track MRR, recall@k

**Grounding:**
- Responses cite source document + chunk
- If no relevant chunk found, respond: "I don't have a runbook for this"

**Deliverables:**
- CLI that indexes a directory of markdown files and answers queries
- Eval set + basic retrieval metrics
- Chunking strategy documented with eval results

### M2 — Discord Bot + Dashboard

**Discord Bot:**
- Slash command interface
- Embeds responses with source citations
- Thumbs-up/down feedback on each response
- Runs on local machine

**Dashboard:**
- Streamlit or FastAPI + HTML
- Metrics: queries per day, sources cited, feedback ratio, top queried runbooks
- Knowledge gap identification (most-thumbed-down retrievals)

**Feedback Loop:**
- Store feedback (thumbs up/down)
- No re-ranking yet — log only, analyze on dashboard

### M3 — PagerDuty Integration (Future)

- Auto-trigger from PagerDuty alert with alert context

## System Requirements

- Python 3.11+
- omlx (for local LLM) or an OpenAI/Anthropic API key
- ~2GB disk for vector store + models

## Key Decisions

| Decision | Choice |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` (local) |
| Framework | LangChain |
| Vector store | ChromaDB |
| CLI | One-shot `query` command |
| Discord bot | Local machine |
| LLM | Pluggable (local + remote) |
| Retrieval | Dense vector search (hybrid later) |
| Chunk strategy | TBD — experiment in M1 |

## Dos and Don'ts

- ✅ Do: Cite sources in every response
- ✅ Do: Say "I don't know" when no relevant content found
- ✅ Do: Design for stressed engineers — fast, accurate, no fluff
- ❌ Don't: Launch without eval
- ❌ Don't: Let the bot generate advice not grounded in retrieved content
- ❌ Don't: Over-chunk or under-chunk

## Success Criteria

### M1
- [ ] Indexes all runbooks from public datasets
- [ ] Answers queries with sourced, ground-truth-verified responses on eval set of 10–15 queries
- [ ] MRR > 0.7 on eval set
- [ ] CLI works: `python -m oncall_rag query "Kafka consumer lag exceeded 10K"`
- [ ] Chunking strategy evaluated and documented

### M2
- [ ] Discord slash command operational
- [ ] Responses rendered with source citations
- [ ] Thumbs-up/down feedback stored
- [ ] Dashboard shows basic metrics
- [ ] Dashboard identifies knowledge gaps

## Timeline

- M1: ~2-3 weeks
- M2: ~2-3 weeks
- M3: Future
