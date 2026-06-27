# RAGoncall — TODO

> Generated: 2026-06-27
> Repo: https://github.com/deghosal-2026/oncall-rag
>
> **M1 — CLI RAG: ✅ COMPLETE (16/16)**
> **M2 — Discord Bot + Dashboard: ✅ COMPLETE (12/12)**
> **M3 — FIFO Alert Pipeline: ✅ COMPLETE (5/5)**
> **M4 — Phone Testing: ✅ COMPLETE (5/5)**
>
> **🎯 Key Milestone (2026-06-27): Full pipeline verified live with OMLX (`Llama-3.2-3B-Instruct-4bit`) — CLI query returned grounded LLM answer with source citations**

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
| M1.11 | Unit + integration tests | [#11](https://github.com/deghosal-2026/oncall-rag/issues/11) | ✅ — 68 tests passing |
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
| M2.2 | Slash command: /query | [#14](https://github.com/deghosal-2026/oncall-rag/issues/14) | ✅ |
| M2.3 | Feedback collection | [#15](https://github.com/deghosal-2026/oncall-rag/issues/15) | ✅ |
| M2.4 | Rich response formatting | [#16](https://github.com/deghosal-2026/oncall-rag/issues/16) | ✅ |
| M2.5 | Dashboard scaffold | [#17](https://github.com/deghosal-2026/oncall-rag/issues/17) | ✅ |
| M2.6 | Dashboard: query metrics | [#18](https://github.com/deghosal-2026/oncall-rag/issues/18) | ✅ |
| M2.7 | Dashboard: knowledge gaps | [#19](https://github.com/deghosal-2026/oncall-rag/issues/19) | ✅ |
| M2.8 | Dashboard: feedback analysis | [#20](https://github.com/deghosal-2026/oncall-rag/issues/20) | ✅ |
| M2.9 | E2E tests (M2) | [#21](https://github.com/deghosal-2026/oncall-rag/issues/21) | ✅ — 68 tests total (54 + 12 new + 2 e2e) |
| M2.10 | README + docs update | [#22](https://github.com/deghosal-2026/oncall-rag/issues/22) | ✅ |

## M3 — FIFO Alert Pipeline (5 tickets)

| # | Title | Issue | Status |
|---|---|---|---|
| M3.1 | Alert schema + FIFO directory setup | [#28](https://github.com/deghosal-2026/oncall-rag/issues/28) | ✅ — schena, dirs, dataclasses |
| M3.2 | process-alerts CLI command | [#29](https://github.com/deghosal-2026/oncall-rag/issues/29) | ✅ — processor, CLI wiring, unit tests |
| M3.3 | Test alert generator script | [#30](https://github.com/deghosal-2026/oncall-rag/issues/30) | ✅ — scripts/generate_test_alerts.py |
| M3.4 | E2E test: generate → process → verify | [#31](https://github.com/deghosal-2026/oncall-rag/issues/31) | ✅ — scripts/test_alert_pipeline.sh |
| M3.5 | Docs: update TODO, SPEC, e2e-test-plan | [#32](https://github.com/deghosal-2026/oncall-rag/issues/32) | ✅ |

## Quick Start

```bash
pip install -e .
oncall-rag index ./corpus
oncall-rag query "How do I check a CrashLoopBackOff pod?"
oncall-rag eval
oncall-rag discord     # Start the Discord bot
oncall-rag dashboard   # Launch the Streamlit dashboard
# M3 — Alert pipeline
python scripts/generate_test_alerts.py   # Drop test alerts in inbox/
oncall-rag process-alerts                # Process them through RAG
```

---

## M4 — Phone Testing (5 tickets)

| # | Title | Issue | Status |
|---|---|---|---|
| M4.1 | Discord bot phone testing: send alert snippet from phone, receive RAG answer | [#33](https://github.com/deghosal-2026/oncall-rag/issues/33) | ✅ |
| M4.2 | Set up Discord bot credentials (app, token, invite to server) | [#34](https://github.com/deghosal-2026/oncall-rag/issues/34) | ✅ |
| M4.3 | Add DISCORD_BOT_TOKEN to .env and start bot | [#35](https://github.com/deghosal-2026/oncall-rag/issues/35) | ✅ |
| M4.4 | Test Discord bot from phone — send /query, get answer | [#36](https://github.com/deghosal-2026/oncall-rag/issues/36) | ✅ |
| M4.5 | E2E test: full flow from phone Discord query to answer | [#37](https://github.com/deghosal-2026/oncall-rag/issues/37) | ✅ |
