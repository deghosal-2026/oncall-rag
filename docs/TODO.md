# RAGoncall — TODO

> Generated: 2026-06-26
> Repo: https://github.com/deghosal-2026/oncall-rag
>
> **M1 — CLI RAG: ✅ COMPLETE (16/16)**
> **M2 — Discord Bot + Dashboard: ▶️ In progress (1/12)**

## M1 — CLI RAG (16 tickets)

### Done

| # | Title | Issue | Status |
|---|---|---|---|
| M1.1 | Project scaffolding | [#1](https://github.com/deghosal-2026/oncall-rag/issues/1) | ✅ |
| M1.2 | LLM client interface | [#2](https://github.com/deghosal-2026/oncall-rag/issues/2) | ✅ |
| M1.3 | Chunking engine | [#3](https://github.com/deghosal-2026/oncall-rag/issues/3) | ✅ |
| M1.4 | Embedding + indexing | [#4](https://github.com/deghosal-2026/oncall-rag/issues/4) | ✅ |
| M1.5 | Retrieval | [#5](https://github.com/deghosal-2026/oncall-rag/issues/5) | ✅ |
| M1.6 | Responder | [#6](https://github.com/deghosal-2026/oncall-rag/issues/6) | ✅ |
| M1.7 | CLI: index command | [#7](https://github.com/deghosal-2026/oncall-rag/issues/7) | ✅ |
| M1.8 | CLI: query command | [#8](https://github.com/deghosal-2026/oncall-rag/issues/8) | ✅ |
| M1.9 | Eval harness | [#9](https://github.com/deghosal-2026/oncall-rag/issues/9) | ✅ |
| M1.10 | Eval set generation | [#10](https://github.com/deghosal-2026/oncall-rag/issues/10) | ✅ |
| M1.11 | Unit + integration tests | [#11](https://github.com/deghosal-2026/oncall-rag/issues/11) | ✅ — 54 tests passing |
| M1.12 | Chunking experiment | [#12](https://github.com/deghosal-2026/oncall-rag/issues/12) | ✅ — header-split wins (0.9524 MRR) |
| M1.13 | Setup instructions (README) | [#23](https://github.com/deghosal-2026/oncall-rag/issues/23) | ✅ |
| M1.14 | User guide | [#24](https://github.com/deghosal-2026/oncall-rag/issues/24) | ✅ |
| M1.15 | Architecture guide | [#25](https://github.com/deghosal-2026/oncall-rag/issues/25) | ✅ |
| M1.16 | E2E test plan + tests | [#26](https://github.com/deghosal-2026/oncall-rag/issues/26) | ✅ — 9 e2e tests passing |

### Code Review Pass (2026-06-27)

15 issues found and fixed:

| Category | Fixes |
|---|---|
| Bugs | Default strategy → header-split; created .env.example; eval count 14 not 115 in docs; updated stale SPEC.md |
| Performance | Cached HuggingFaceEmbeddings; cached Chroma vectorstore in retriever |
| Correctness | Offset-based line numbers; eval matches by source_lines overlap; file-level dedup; fixed infinite loop guard; config validates overlap < size |
| Code quality | Removed deprecated persist(); header-split applies overlap; removed dead imports; experiment writes to separate file; added logging |

## M2 — Discord Bot + Dashboard (12 tickets)

| # | Title | Issue | Status |
|---|---|---|---|
| M2.1 | Discord bot scaffold | [#13](https://github.com/deghosal-2026/oncall-rag/issues/13) | ✅ — `bot.py`, `/ping`, CLI wiring |
| M2.1a | Discord setup guide | [#27](https://github.com/deghosal-2026/oncall-rag/issues/27) | ✅ — `docs/setup.md` |
| M2.2 | Slash command: /query | [#14](https://github.com/deghosal-2026/oncall-rag/issues/14) | ❌ |
| M2.3 | Feedback collection | [#15](https://github.com/deghosal-2026/oncall-rag/issues/15) | ❌ |
| M2.4 | Rich response formatting | [#16](https://github.com/deghosal-2026/oncall-rag/issues/16) | ❌ |
| M2.5 | Dashboard scaffold | [#17](https://github.com/deghosal-2026/oncall-rag/issues/17) | ❌ |
| M2.6 | Dashboard: query metrics | [#18](https://github.com/deghosal-2026/oncall-rag/issues/18) | ❌ |
| M2.7 | Dashboard: knowledge gaps | [#19](https://github.com/deghosal-2026/oncall-rag/issues/19) | ❌ |
| M2.8 | Dashboard: feedback analysis | [#20](https://github.com/deghosal-2026/oncall-rag/issues/20) | ❌ |
| M2.9 | E2E tests (M2) | [#21](https://github.com/deghosal-2026/oncall-rag/issues/21) | ❌ |
| M2.10 | README + docs update | [#22](https://github.com/deghosal-2026/oncall-rag/issues/22) | ❌ |

## Quick Start

```bash
pip install -e .
oncall-rag index ./corpus
oncall-rag query "How do I check a CrashLoopBackOff pod?"
oncall-rag eval
```
