"""Main module of discod bot."""

# pylint: disable=C0411
from pathlib import Path
from typing import Optional

import discord
from aiohttp_socks import ProxyConnector
from discord import app_commands
from discord.ext import commands, tasks
from loguru import logger

from ..chat_parser.chat_parser import (
    MinecraftChatParser,
    VanishHandlerMasterPerki,
)
from ..chat_parser.custom_exceptions import ServerStarted, ServerStopped
from ..rcon_sender.rcon import AIOMcRcon, RCONSendCmdError
from .cogs.server_commands import ServerCommands
from .utillity import get_config, parse_message


class MCBot(commands.Bot):
    """Initialize variables."""

    def __init__(self, *args, channel_id: int, **kwargs) -> None:
        """Initialize the Minecraft chat parser and RCON client."""
        super().__init__(*args, **kwargs)

        self._channel_id = channel_id
        self.chat_parser = MinecraftChatParser(
            MINECRAFT_SERVER_PATH,
            vanish_handler,
        )
        self.aiomcrcon = AIOMcRcon(RCON_HOST, RCON_PORT, RCON_SECRET)
        self.channel: Optional[discord.TextChannel] = None

    async def setup_hook(self) -> None:
        await self.add_cog(ServerCommands(self))  # Register cog
        self.tree.error(self.on_app_command_error)
        await self.tree.sync()  # Register commands globally

    @property
    def channel_id(self) -> int:
        """Return the channel ID."""
        return self._channel_id

    async def on_ready(self):
        """
        Event handler for when the bot has successfully connected to Discord.

        This function initializes a MinecraftChatParser and starts a loop
        to check for new chat messages, sending them to a specified channel.
        """

        logger.info(f"APP_VERSION: {APP_VERSION}")
        logger.info(f"We have logged in as {self.user}")

        await self.aiomcrcon.connect()
        logger.info("Connected to Minecraft server via RCON.")

        # Get the channel
        self.channel = self.get_channel(CHANNEL_ID)
        if self.channel is None:
            logger.error(
                f"Channel with ID {CHANNEL_ID} not found or no access."
            )
            return

        # Start the background task
        self.check_chat_messages.start()

        await self.aiomcrcon.send_cmd("/say Discord joined the game")
        await self.channel.send("## Discord joined the chat.")

    @tasks.loop(seconds=0.1)
    async def check_chat_messages(self):
        """
        Periodically checks for new Minecraft chat messages and sends
        them to the Discord channel.
        """
        try:
            if not self.chat_parser or not self.channel:
                logger.error("Chat parser or channel is not initialized.")
                return
            try:
                message = self.chat_parser.get_chat_message()
                if message:
                    logger.info(f"Message received: {message}")
                    await self.channel.send(message)
            except ServerStarted as msg:
                logger.info("Server started.")
                logger.info("Reconnecting to the mc-rcon...")
                await self.channel.send(str(msg))
                await self.aiomcrcon.close()
                await self.aiomcrcon.connect()
            except ServerStopped as msg:
                logger.info("Server stopped.")
                await self.channel.send(str(msg))

        except Exception as e:
            logger.exception(f"Error in chat message checking loop: {e}")

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        """Handle application command errors."""

        async def send(msg: str):
            # If deffer is already done, use followup instead.
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original  # <- вот тут твоя реальная ошибка

            if isinstance(original, RCONSendCmdError):
                await send(
                    "Сервер не доступен. Попробуйте позже.",
                )
                logger.error(
                    f"RCON error: {original}",
                )
                return

        await send(
            "Произошла ошибка при выполнении команды.",
        )

    async def on_message(  # pylint: disable=W0221
        self,
        message: discord.Message,
    ) -> None:
        """
        Event handler for processing incoming messages.

        Parameters:
            message (discord.Message): The incoming message.

        Returns:
            None
        """
        await self.process_commands(message)
        if message.author == self.user:
            return
        # Check if the message is from the desired channel
        if message.channel.id == CHANNEL_ID:
            message_text = await parse_message(message)
            logger.info(message_text)
            try:
                if not self.aiomcrcon:
                    raise RCONSendCmdError("Rcon have not initialized yet.")
                await self.aiomcrcon.send_cmd(f"/say {message_text}")
            except RCONSendCmdError:
                await message.channel.send(
                    "Сервер в данный момент недоступен."
                )

    async def close(self):
        """
        Event triggered when the bot is shutting down.
        Closes the RCON client connection.
        """
        logger.debug("Bot is shutting down...")

        if self.aiomcrcon:
            await self.aiomcrcon.close()
            logger.debug("Bot and RCON client disconnected.")
        else:
            logger.debug("RCON client not initialized.")

        if self.channel:
            await self.channel.send("## Discord left the chat.")
            logger.debug("Bot sent a goodbye message to the Discord channel.")
        else:
            logger.debug("Discord channel not initialized.")


intents = discord.Intents.default()
intents.message_content = True


APP_VERSION = "1.6.1"

DATA_PATH = Path("data")

vanish_handler = VanishHandlerMasterPerki(DATA_PATH / "vanished.json")
config = get_config(DATA_PATH / "config.ini")
RCON_HOST = config["MC_SERVER"]["RCON_HOST"]
RCON_SECRET = config["MC_SERVER"]["RCON_SECRET"]
try:
    RCON_PORT = config.getint("MC_SERVER", "RCON_PORT")
except ValueError as e:
    raise ValueError(f"Invalid rcon port: {e}") from e

try:
    CHANNEL_ID = config.getint("DISCORD", "CHANNEL_ID")
except ValueError as e:
    raise ValueError(f"Invalid CHANNEL_ID: {e}") from e
DISCORD_ACCESS_TOKEN = config["DISCORD"]["DISCORD_ACCESS_TOKEN"]
MINECRAFT_SERVER_PATH = "minecraft-root-dir"
SUPPORTED_COMMANDS = "/info, /list, /tps"
PROXY_URL = config["DISCORD"]["PROXY_URL"]


async def main():
    """Main entry point."""
    # Configure logging to create a new log file each month
    # without deleting old ones
    logger.add(
        DATA_PATH / "logs/file_{time:YYYY-MM}.log",
        rotation="1 month",
        retention="1 month",  # Retain log files for 1 month after rotation
        compression="zip",  # Optional: Enable compression for rotated logs
        level="DEBUG",
        serialize=False,
    )

    try:
        proxy_connector = None
        if PROXY_URL:
            proxy_connector = ProxyConnector.from_url(PROXY_URL)
            logger.info("Proxy connector created successfully.")
        else:
            logger.info("No proxy configured.")

        async with MCBot(
            command_prefix="/",
            intents=intents,
            connector=proxy_connector,
            channel_id=CHANNEL_ID,
        ) as bot:
            await bot.start(DISCORD_ACCESS_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.error(f"Bot crashed with exception: {e}")
        logger.warning(
            "Check if proxy format is correct: "
            "socks5://[PROXY_LOGIN:PROXY_PASS@]PROXY_HOST:PROXY_PORT"
        )
