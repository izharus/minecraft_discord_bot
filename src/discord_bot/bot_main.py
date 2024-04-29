"""Main module of discod bot."""
# pylint: disable=C0411
import asyncio
import sys
from typing import Any

import discord
from access import CHANNEL_ID, DISCORD_ACCESS_TOKEN, MINECRAFT_SERVER_PATH
from discord.ext import commands
from loguru import logger

from ..chat_parser.chat_parser import MinecraftChatParser
from ..rcon_sender.rcon import RconLocalDocker
from .utillity import parse_message

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

DEBUG_MODE = "--debug" in sys.argv
APP_VERSION = "1.0.5"


@bot.event
@logger.catch()
async def on_ready():
    """
    Event handler for when the bot has successfully connected to Discord.

    This function initializes a MinecraftChatParser and continuously checks
    for new chat messages, sending them to a specified channel.

    Note:
        Adjust the DEBUG_MODE variable to switch between debug and
            normal modes.

    """
    logger.info(f"APP_VERSION: {APP_VERSION}")
    logger.info(f"We have logged in as {bot.user}")
    if DEBUG_MODE:
        # pylint: disable = C0301
        log_file_path = MINECRAFT_SERVER_PATH
    else:
        log_file_path = "minecraft-server"
    chat_parser = MinecraftChatParser(log_file_path)
    channel = bot.get_channel(CHANNEL_ID)

    # Check for a new messages every 1 second
    while True:
        message = chat_parser.get_chat_message()
        while message:
            logger.info(f"Message received: {message}")
            await channel.send(message)
            await asyncio.sleep(0.1)
            message = chat_parser.get_chat_message()

        await asyncio.sleep(1)


@bot.command(name="list")
@logger.catch()
async def get_list_of_players(ctx: commands.Context) -> None:
    """
    Get the list of online players on the Minecraft server.

    Parameters:
    - ctx: Context object for the command execution.
    """
    logger.info("Command received: list")
    rcon = RconLocalDocker("minecraft_dac")
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
@logger.catch()
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
@logger.catch()
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
@logger.catch()
async def on_message(message: discord.Message) -> None:
    """
    Event handler for processing incoming messages.

    Parameters:
        message (discord.Message): The incoming message.

    Returns:
        None
    """
    await bot.process_commands(message)
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    if message.author == bot.user:
        return
    # Check if the message is from the desired channel
    if message.channel.id == CHANNEL_ID:
        message_text = await parse_message(message)
        logger.info(message_text)
        rcon.send_say_command(message_text)


def main():
    """Main entry point."""
    bot.run(DISCORD_ACCESS_TOKEN)
