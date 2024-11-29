"""Main module of discod bot."""
# pylint: disable=C0411
from pathlib import Path
from typing import Any, Optional

import discord
from discord.ext import commands, tasks
from loguru import logger

from ..chat_parser.chat_parser import (
    MinecraftChatParser,
    VanishHandlerMasterPerki,
)
from ..chat_parser.custom_exceptions import ServerStarted, ServerStopped
from ..rcon_sender.rcon import AIOMcRcon, RCONSendCmdError
from .utillity import get_config, parse_message


class MyBot(commands.Bot):
    """Initialize variables."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.chat_parser: Optional[MinecraftChatParser] = None
        self.channel: Optional[discord.TextChannel]
        self.aiomcrcon: Optional[AIOMcRcon] = None


intents = discord.Intents.default()
intents.message_content = True
bot = MyBot(command_prefix="/", intents=intents)

APP_VERSION = "1.4.1"

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


@bot.event
async def on_ready():
    """
    Event handler for when the bot has successfully connected to Discord.

    This function initializes a MinecraftChatParser and starts a loop
    to check for new chat messages, sending them to a specified channel.
    """
    logger.info(f"APP_VERSION: {APP_VERSION}")
    logger.info(f"We have logged in as {bot.user}")

    # Initialize chat parser
    bot.chat_parser = MinecraftChatParser(
        MINECRAFT_SERVER_PATH,
        vanish_handler,
    )
    bot.aiomcrcon = AIOMcRcon(RCON_HOST, RCON_PORT, RCON_SECRET)
    await bot.aiomcrcon.connect()
    # Get the channel
    bot.channel = bot.get_channel(CHANNEL_ID)
    if bot.channel is None:
        logger.error(f"Channel with ID {CHANNEL_ID} not found or no access.")
        return

    # Start the background task
    check_chat_messages.start()

    await bot.aiomcrcon.send_cmd("/say Discord joined the game")
    await bot.channel.send("## Discord joined the chat.")


@tasks.loop(seconds=0.1)
async def check_chat_messages():
    """
    Periodically checks for new Minecraft chat messages and sends
    them to the Discord channel.
    """
    try:
        if not bot.chat_parser or not bot.channel:
            logger.error("Chat parser or channel is not initialized.")
            return
        try:
            message = bot.chat_parser.get_chat_message()
            logger.info(f"Message received: {message}")
            await bot.channel.send(message)
        except ServerStarted as msg:
            logger.info("Server started.")
            logger.info("Reconnecting to the mc-rcon...")
            await bot.channel.send(str(msg))
            await bot.aiomcrcon.connect()
        except ServerStopped as msg:
            logger.info("Server stopped.")
            await bot.channel.send(str(msg))

    except Exception as e:
        logger.exception(f"Error in chat message checking loop: {e}")


@bot.command(name="tps")
async def get_server_tps(ctx: commands.Context) -> None:
    """
    Get the TPS of the Minecraft server.
    """
    logger.info("Command received: tps")
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        try:
            if not bot.aiomcrcon:
                raise RCONSendCmdError("Rcon have not initialized yet.")
            tps = await bot.aiomcrcon.send_cmd("/forge tps")
        except RCONSendCmdError as error:
            logger.warning(f"/tps failed: {error}")
        if tps:
            await ctx.send(tps[0])
        else:
            logger.error("Unable to get players_list")
            await ctx.send("Не удалось получить список игроков.")


@bot.command(name="list")
async def get_list_of_players(ctx: commands.Context) -> None:
    """
    Get the list of online players on the Minecraft server.

    Parameters:
    - ctx: Context object for the command execution.
    """
    logger.info("Command received: list")
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        try:
            if not bot.aiomcrcon:
                raise RCONSendCmdError("Rcon have not initialized yet.")
            players_list = await bot.aiomcrcon.send_cmd("/list")
        except RCONSendCmdError as error:
            logger.warning(f"/list failed: {error}")
        if players_list:
            await ctx.send(players_list[0].rstrip(":"))
        else:
            logger.error("Unable to get players_list")
            await ctx.send("Не удалось получить список игроков.")


@bot.command(name="info")
async def get_list_of_cammands(ctx: commands.Context) -> None:
    """
    Get the list of available commands.

    Parameters:
    - ctx: Context object for the command execution.
    """
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        logger.info("get_list_of_cammands entry")
        await ctx.send(f"Доступные команды: {SUPPORTED_COMMANDS}")


@bot.event
async def on_command_error(ctx: commands.Context, error: Any) -> None:
    """
    Handle errors that occur during command execution.

    Parameters:
    - ctx: Context object for the command execution.
    - error: The error that occurred during command execution.
    """
    if isinstance(error, commands.CommandNotFound):
        logger.info("on_command_error entry")
        await ctx.send(
            "Неизвестная команда. Доступные команды:" f"{SUPPORTED_COMMANDS}"
        )


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Event handler for processing incoming messages.

    Parameters:
        message (discord.Message): The incoming message.

    Returns:
        None
    """
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    # Check if the message is from the desired channel
    if message.channel.id == CHANNEL_ID:
        message_text = await parse_message(message)
        logger.info(message_text)
        try:
            if not bot.aiomcrcon:
                raise RCONSendCmdError("Rcon have not initialized yet.")
            await bot.aiomcrcon.send_cmd(f"/say {message_text}")
        except RCONSendCmdError:
            await message.channel.send("Сервер в данный момент недоступен.")


@bot.event
async def close():
    """
    Event triggered when the bot is shutting down.
    Closes the RCON client connection.
    """
    await bot.aiomcrcon.close()
    logger.debug("Bot and RCON client disconnected.")
    await bot.channel.send("## Discord left the chat.")


def main():
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
    bot.run(DISCORD_ACCESS_TOKEN)
