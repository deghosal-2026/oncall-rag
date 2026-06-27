# Setup: Discord Bot

## Prerequisites

- oncall-rag installed (`pip install -e .`)
- Corpus indexed (`oncall-rag index ./corpus`)
- A Discord account with a server you can invite bots to

## Step 1 — Create a Discord Application

1. Go to https://discord.com/developers/applications
2. Click **New Application**, name it (e.g. "Oncall RAG"), accept the ToS
3. Go to **Bot** in the left sidebar
4. Click **Reset Token** then **Copy** — this is your `DISCORD_BOT_TOKEN`
5. Under **Privileged Gateway Intents**, enable:
   - `MESSAGE CONTENT INTENT` (for future message-based features)
6. Click **Save Changes**

## Step 2 — Invite the Bot to Your Server

1. Go to **OAuth2 → URL Generator**
2. Under **Scopes**, check `bot` and `applications.commands`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Use Slash Commands`
4. Copy the generated URL, open it in your browser
5. Select your server and click **Authorize**

## Step 3 — Configure `.env`

Add to `.env` in the project root:

```env
DISCORD_BOT_TOKEN=your_token_here
```

## Step 4 — Start the Bot

```bash
oncall-rag discord
```

You should see:

```
INFO     oncall-rag.bot: Logged in as Oncall RAG#1234 (ID: 123456789)
```

## Step 5 — Verify the CLI (RAG Pipeline)

Before testing Discord, confirm the full RAG pipeline works on the command line:

```bash
oncall-rag query "How do I debug a CrashLoopBackOff pod?"
```

Expected output — a natural-language answer with source file citations (not just `"I don't have a runbook for this"`). If the pipeline is down, the CLI will fail too.

## Step 6 — Test Discord End-to-End

1. Open Discord, go to your server
2. Type `/ping` and send
3. The bot responds with **Pong!**

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `DISCORD_BOT_TOKEN is not set` | Missing token in `.env` | Add `DISCORD_BOT_TOKEN=...` to `.env` |
| `Privileged intent ... not approved` | Intents not enabled in Developer Portal | Go to Bot settings, enable intents, save |
| Slash commands not appearing | Bot needs `applications.commands` scope | Re-invite with correct OAuth2 scopes |
| `discord.py not found` | Package not installed | Run `pip install -e .` |
| Bot goes offline after startup | Token invalid or rate-limited | Regenerate token in Developer Portal |
