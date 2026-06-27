from __future__ import annotations

import asyncio
import logging
from functools import partial

import discord
from discord import app_commands

from oncall_rag.config import Config

logger = logging.getLogger("oncall-rag.bot")


class OncallBot(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.config = config
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.add_command(ping_command)
        self.tree.add_command(query_command)
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)


@app_commands.command(name="ping", description="Check if the bot is responsive")
async def ping_command(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong!", ephemeral=True)


@app_commands.command(name="query", description="Ask a question from runbooks")
@app_commands.describe(question="Your on-call question")
async def query_command(
    interaction: discord.Interaction,
    question: str,
) -> None:
    await interaction.response.defer(ephemeral=True)
    config = interaction.client.config  # type: ignore[union-attr]
    loop = asyncio.get_running_loop()
    try:
        from oncall_rag.responder import query_runbooks
        fn = partial(query_runbooks, question, config)
        answer = await loop.run_in_executor(None, fn)
    except Exception:
        logger.exception("RAG query failed")
        answer = "Something went wrong. Check the logs."

    embed = _answer_to_embed(answer)
    await interaction.followup.send(embed=embed, ephemeral=True)


def _answer_to_embed(raw: str) -> discord.Embed:
    if raw == "I don't have a runbook for this.":
        embed = discord.Embed(
            title="No runbook found",
            description=raw,
            color=discord.Color.orange(),
        )
        return embed

    if raw.startswith("Sources:\n"):
        answer_text = "*No LLM answer generated — showing raw sources.*"
        sources_text = raw[len("Sources:\n"):]
    elif "\n\nSources:\n" in raw:
        answer_text, sources_text = raw.split("\n\nSources:\n", 1)
    else:
        embed = discord.Embed(
            title="Answer",
            description=raw[:4096],
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Thumbs up/down to rate this answer")
        return embed

    embed = discord.Embed(
        title="Answer",
        description=answer_text[:4096] if len(answer_text) > 4096 else answer_text,
        color=discord.Color.blue(),
    )

    sources_lines = [s.strip("- ").strip() for s in sources_text.strip().split("\n") if s.strip()]
    for i, src in enumerate(sources_lines, 1):
        name = f"Source {i}"
        value = f"`{src}`"[:1024]
        embed.add_field(name=name, value=value, inline=True)

    embed.set_footer(text="Thumbs up/down to rate this answer")
    return embed
