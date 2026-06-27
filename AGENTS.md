# AGENTS.md — Persistent context for opencode

## 🎯 Milestone: Full Pipeline Verified Live (2026-06-27)

## What We Built

A local-first RAG assistant for on-call engineers with 3 delivery channels:

**M1 — CLI RAG (16 issues)**
- Index markdown runbooks → ChromaDB vector store
- Query via CLI → retrieve chunks → LLM generates grounded answer with source citations
- Eval harness (MRR/Recall@5), chunking experiment (header-split wins at 0.9524)
- 3 pluggable LLM backends: OMLX, OpenAI, Anthropic
- 68 unit/integration tests + 9 e2e tests

**M2 — Discord Bot + Streamlit Dashboard (12 issues)**
- Discord bot with `/ping`, `/query` slash commands, rich embed responses, 👍/👎 feedback
- Streamlit dashboard: overview tab, query metrics tab, knowledge gaps tab, feedback analysis tab

**M3 — FIFO Alert Pipeline (5 issues)**
- File-based alert pipeline: `alerts/inbox/` → RAG → `alerts/outbox/` + `alerts/archive/`
- `oncall-rag process-alerts` CLI command
- Test alert generator (`scripts/generate_test_alerts.py`) and E2E test script

## OMLX Verification (2026-06-27) 
- **Pipeline verified working** with OMLX + `Llama-3.2-3B-Instruct-4bit`
- Query: "How do I debug a CrashLoopBackOff pod?" returned sourced LLM answer via RAG pipeline
- OMLX endpoint: `http://localhost:8000/v1` (OpenAI-compatible API, not Ollama `/api/generate`)
- API key: `omlx-test` (set in `.env`)
- Model cold-load takes ~30s on first request; subsequent queries are fast

## Chunking Default
- `header-split` (MRR 0.9524)

## Eval
- 14 Q&A pairs in `data/eval.json`
- Current MRR: 0.571, Recall@5: 0.714 (4 grafana misses due to YAML frontmatter chunking)

## Closeout
- All 37 issues closed across 4 milestones
- Full pipeline verified live: CLI, Discord bot (phone-tested), Dashboard, Alert Pipeline
- Detailed closeout: `docs/CLOSEOUT.md`
- Git tags: `v0.1.0`, `v0.2.0`, `v0.3.0`, `v1.0.0`
