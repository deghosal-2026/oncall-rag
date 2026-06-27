# Discord Bot Architecture

## Overview

The Discord bot (`src/oncall_rag/bot.py`) exposes `/ping` and `/query` slash commands, wires each query through the RAG pipeline, and collects 👍/👎 feedback. It runs on the local machine — no cloud hosting.

## Entrypoint

```
oncall-rag discord
```

`__main__.py` creates an `OncallBot` from `bot.py` and runs it with the config token.

```
  __main__.py
      │
      └──► bot.OncallBot(config)
              └──► client.run(config.discord_bot_token)
```

## Class Diagram

```
┌─────────────────────────────────────────────┐
│                 OncallBot                    │
│  discord.Client subclass                     │
│                                              │
│  setup_hook()                                │
│    └── tree.add_command(ping_command)        │
│    └── tree.add_command(query_command)       │
│    └── tree.sync()                           │
│                                              │
│  on_ready()                                   │
│    └── log "Logged in as ..."                 │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│          Slash Commands (top-level fns)       │
│                                              │
│  ping_command(interaction)                    │
│    └── "Pong!"                                │
│                                              │
│  query_command(interaction, question)         │
│    └── defer()                                │
│    └── run_in_executor(query_runbooks)        │
│    └── _answer_to_embed(answer)               │
│    └── _log_query(question, answer, sources)  │
│    └── FeedbackView(question, answer, sources)│
│    └── followup.send(embed, view)             │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│           Helpers (module-level)              │
│                                              │
│  _parse_sources(raw)     → list[str]         │
│  _answer_to_embed(raw)   → (Embed, [str])    │
│  _log_feedback(...)      → writes JSONL      │
│  _log_query(...)         → writes JSONL      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│              FeedbackView                     │
│  discord.ui.View subclass                     │
│  timeout=86400s (24h)                         │
│                                              │
│  thumbs_up(interaction, button)               │
│    └── _rate(interaction, "up")               │
│  thumbs_down(interaction, button)             │
│    └── _rate(interaction, "down")             │
│                                              │
│  _rate(interaction, rating)                   │
│    └── _log_feedback(...)                     │
│    └── disable all buttons                    │
│    └── update footer → "Rated: up/down"       │
└──────────────────────────────────────────────┘
```

## Query Flow (Discord)

```
  Phone/Desktop Discord App
         │
         │  /query "How do I debug CrashLoopBackOff?"
         ▼
  Discord Gateway
         │
         ▼
  OncallBot.query_command()
         │
         ├── interaction.response.defer()     ← "bot is thinking..."
         │
         ├── run_in_executor(None, fn)
         │     └── responder.query_runbooks()
         │           ├── retriever.retrieve()
         │           ├── build LLM prompt
         │           └── llm.generate(prompt)
         │
         ├── _answer_to_embed(raw)            ← parse sources, build Embed
         ├── _log_query(...)                  ← write data/queries.jsonl
         └── FeedbackView(...)                ← attach 👍/👎 buttons
                │
                ▼
         interaction.followup.send(embed, view)
                │
                ▼
         User sees rich embed answer in Discord
```

## Data Files

| File | Purpose |
|---|---|
| `data/queries.jsonl` | Every `/query` call logged with question, answer, sources, timestamp |
| `data/feedback.jsonl` | Every 👍/👎 rating logged with question, answer, sources, user_id, timestamp |

Both files are consumed by the Streamlit dashboard (`oncall-rag dashboard`).

## Response Format

Embeds are color-coded:
- **Blue** — successful answer with sources and source fields
- **Orange** — `"I don't have a runbook for this."`
- **Blue (no sources)** — raw LLM output without retrievable source metadata

Each embed with sources has a footer: `"Thumbs up/down to rate this answer"`.

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `run_in_executor` (thread pool) | `query_runbooks` is synchronous (ChromaDB + httpx). Running in executor avoids blocking the Discord event loop. |
| Ephemeral responses | Only the querying user sees the answer — avoids channel clutter. |
| 24h button timeout | Buttons expire after 1 day to prevent stale feedback on old answers. |
| Buttons disabled after rating | Prevents double-votes. Footer updated to reflect the rating. |
| JSONL logging | Append-only, parseable by pandas/Streamlit. No DB dependency. |
