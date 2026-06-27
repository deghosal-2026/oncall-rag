from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import discord
from discord import app_commands
from discord.ui import Button, View

from oncall_rag.config import Config

logger = logging.getLogger("oncall-rag.bot")

FEEDBACK_PATH = Path("data/feedback.jsonl")


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

    embed, sources = _answer_to_embed(answer)
    view = FeedbackView(question, answer, sources)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


def _parse_sources(raw: str) -> list[str]:
    sources_text = ""
    if raw.startswith("Sources:\n"):
        sources_text = raw[len("Sources:\n"):]
    elif "\n\nSources:\n" in raw:
        _, sources_text = raw.split("\n\nSources:\n", 1)

    if not sources_text:
        return []
    return [s.strip("- ").strip() for s in sources_text.strip().split("\n") if s.strip()]


def _answer_to_embed(raw: str) -> tuple[discord.Embed, list[str]]:
    sources = _parse_sources(raw)
    has_feedback = bool(sources)

    if raw == "I don't have a runbook for this.":
        embed = discord.Embed(
            title="No runbook found",
            description=raw,
            color=discord.Color.orange(),
        )
        return embed, []

    if raw.startswith("Sources:\n"):
        answer_text = "*No LLM answer generated — showing raw sources.*"
    elif "\n\nSources:\n" in raw:
        answer_text, _ = raw.split("\n\nSources:\n", 1)
    else:
        embed = discord.Embed(
            title="Answer",
            description=raw[:4096],
            color=discord.Color.blue(),
        )
        if has_feedback:
            embed.set_footer(text="Thumbs up/down to rate this answer")
        return embed, []

    embed = discord.Embed(
        title="Answer",
        description=answer_text[:4096] if len(answer_text) > 4096 else answer_text,
        color=discord.Color.blue(),
    )

    for i, src in enumerate(sources, 1):
        name = f"Source {i}"
        value = f"`{src}`"[:1024]
        embed.add_field(name=name, value=value, inline=True)

    if has_feedback:
        embed.set_footer(text="Thumbs up/down to rate this answer")
    return embed, sources


def _log_feedback(
    question: str,
    answer: str,
    sources: list[str],
    rating: str,
    user_id: int,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "sources": sources,
        "rating": rating,
        "user_id": user_id,
    }
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info("Feedback logged: %s for Q=%r", rating, question[:60])


class FeedbackView(View):
    def __init__(self, question: str, answer: str, sources: list[str]) -> None:
        super().__init__(timeout=86400)
        self._question = question
        self._answer = answer
        self._sources = sources

    async def _rate(self, interaction: discord.Interaction, rating: str) -> None:
        assert interaction.user is not None
        _log_feedback(
            question=self._question,
            answer=self._answer,
            sources=self._sources,
            rating=rating,
            user_id=interaction.user.id,
        )
        for child in self.children:
            child.disabled = True  # type: ignore[union-attr]
        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.set_footer(text=f"Rated: {rating}")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="👍", style=discord.ButtonStyle.success)
    async def thumbs_up(self, interaction: discord.Interaction, _button: Button) -> None:
        await self._rate(interaction, "up")

    @discord.ui.button(label="👎", style=discord.ButtonStyle.danger)
    async def thumbs_down(self, interaction: discord.Interaction, _button: Button) -> None:
        await self._rate(interaction, "down")
