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

    MAX_LEN = 1900
    if len(answer) <= MAX_LEN:
        await interaction.followup.send(answer, ephemeral=True)
    else:
        parts = []
        for i in range(0, len(answer), MAX_LEN):
            parts.append(answer[i : i + MAX_LEN])
        await interaction.followup.send(parts[0], ephemeral=True)
        for part in parts[1:]:
            await interaction.followup.send(part, ephemeral=True)
