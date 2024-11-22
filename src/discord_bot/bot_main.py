"""Main module of discod bot."""
# pylint: disable=C0411
import asyncio
import sys
from pathlib import Path
from typing import Any, Optional

import discord
from discord.ext import commands, tasks
from loguru import logger

from ..chat_parser.chat_parser import MinecraftChatParser
from ..rcon_sender.rcon import RconLocalDocker
from .utillity import get_config, parse_message


class MyBot(commands.Bot):
    """Initialize variables."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_parser: Optional[MinecraftChatParser] = None
        self.channel: Optional[discord.TextChannel]


intents = discord.Intents.default()
intents.message_content = True
bot = MyBot(command_prefix="/", intents=intents)

DEBUG_MODE = "--debug" in sys.argv
APP_VERSION = "1.3.1"

DATA_PATH = Path("data")

config = get_config(DATA_PATH / "config.ini")
CONTAINER_NAME = config["DISCORD"]["CONTAINER_NAME"]
try:
    CHANNEL_ID = config.getint("DISCORD", "CHANNEL_ID")
except ValueError as e:
    raise ValueError(f"Invalid CHANNEL_ID: {e}") from e
DISCORD_ACCESS_TOKEN = config["DISCORD"]["DISCORD_ACCESS_TOKEN"]
MINECRAFT_SERVER_PATH = "minecraft-root-dir"


@bot.event
@logger.catch(reraise=True)
async def on_ready():
    """
    Event handler for when the bot has successfully connected to Discord.

    This function initializes a MinecraftChatParser and starts a loop
    to check for new chat messages, sending them to a specified channel.
    """
    logger.info(f"APP_VERSION: {APP_VERSION}")
    logger.info(f"We have logged in as {bot.user}")

    # Initialize chat parser
    bot.chat_parser = MinecraftChatParser(MINECRAFT_SERVER_PATH)

    # Get the channel
    bot.channel = bot.get_channel(CHANNEL_ID)
    if bot.channel is None:
        logger.error(f"Channel with ID {CHANNEL_ID} not found or no access.")
        return

    # Start the background task
    check_chat_messages.start()


@tasks.loop(seconds=1.0)
async def check_chat_messages():
    """
    Periodically checks for new Minecraft chat messages and sends
    them to the Discord channel.
    """
    try:
        if not bot.chat_parser or not bot.channel:
            logger.error("Chat parser or channel is not initialized.")
            return

        message = bot.chat_parser.get_chat_message()
        while message:
            logger.info(f"Message received: {message}")
            await bot.channel.send(message)
            await asyncio.sleep(0.1)  # Optional delay to prevent rate limits
            message = bot.chat_parser.get_chat_message()

    except Exception as e:
        logger.exception(f"Error in chat message checking loop: {e}")


@bot.command(name="list")
@logger.catch(reraise=True)
async def get_list_of_players(ctx: commands.Context) -> None:
    """
    Get the list of online players on the Minecraft server.

    Parameters:
    - ctx: Context object for the command execution.
    """
    logger.info("Command received: list")
    rcon = RconLocalDocker(CONTAINER_NAME)
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        try:
            players_list = rcon.send_command("/list")
        except Exception as error:
            logger.error(f"Failed to receive players_list: {error}")
            await ctx.send("Некорректный ответ от сервера.")
        if players_list:
            players_list = players_list.split("\n")[0]
            await ctx.send(players_list)
        else:
            logger.error("Unable to get players_list")
            await ctx.send("Не удалось получить список игроков.")


@bot.command(name="info")
@logger.catch(reraise=True)
async def get_list_of_cammands(ctx: commands.Context) -> None:
    """
    Get the list of available commands.

    Parameters:
    - ctx: Context object for the command execution.
    """
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        logger.info("get_list_of_cammands entry")
        await ctx.send("Доступные команды: /list, /info")


@bot.event
@logger.catch(reraise=True)
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
            "Неизвестная комманда, введите /info "
            "чтобы узнать все доступные команды."
        )


@bot.event
@logger.catch(reraise=True)
async def on_message(message: discord.Message) -> None:
    """
    Event handler for processing incoming messages.

    Parameters:
        message (discord.Message): The incoming message.

    Returns:
        None
    """
    await bot.process_commands(message)
    rcon = RconLocalDocker(CONTAINER_NAME)
    if message.author == bot.user:
        return
    # Check if the message is from the desired channel
    if message.channel.id == CHANNEL_ID:
        message_text = await parse_message(message)
        logger.info(message_text)
        rcon.send_say_command(message_text)


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
