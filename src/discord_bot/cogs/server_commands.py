"""All server commands for the bot."""

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

if TYPE_CHECKING:
    from ..bot_main import MCBot


class ServerCommands(commands.Cog):
    """Cog for server commands."""

    def __init__(
        self,
        bot: "MCBot",
    ):
        self._bot = bot

    @app_commands.command(name="tps", description="Получить TPS сервера.")
    async def tps_command(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the TPS of the Minecraft server.
        """
        logger.info("Slash command received: /tps")
        await interaction.response.defer()
        tps = await self._bot.aiomcrcon.send_cmd("/forge tps")
        await interaction.followup.send(tps[0])

    @app_commands.command(
        name="list", description="Получить список игроков на сервере."
    )
    async def players_list_command(
        self,
        interaction: discord.Interaction,
    ) -> None:
        """
        Get the list of online players on the Minecraft server.

        Parameters:
        - ctx: Context object for the command execution.
        """
        logger.info("Slash command received: list")
        await interaction.response.defer()
        players_list = await self._bot.aiomcrcon.send_cmd("/list")
        await interaction.followup.send(players_list[0])
