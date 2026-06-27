from __future__ import annotations

import logging

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
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)


@app_commands.command(name="ping", description="Check if the bot is responsive")
async def ping_command(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong!", ephemeral=True)
