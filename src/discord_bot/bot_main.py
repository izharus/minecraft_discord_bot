"""Main module of discod bot."""
# pylint: disable=C0411
import asyncio
import sys
from typing import Any

import discord
from access import CHANNEL_ID, DISCORD_ACCESS_TOKEN
from discord.ext import commands

from ..chat_parser.chat_parser import MinecraftChatParser
from ..rcon_sender.rcon import RconLocalDocker

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

DEBUG_MODE = "--debug" in sys.argv


@bot.event
async def on_ready():
    """
    Event handler for when the bot has successfully connected to Discord.

    This function initializes a MinecraftChatParser and continuously checks
    for new chat messages, sending them to a specified channel.

    Note:
        Adjust the DEBUG_MODE variable to switch between debug and
            normal modes.

    """
    # print(f"We have logged in as {bot.user}")

    if DEBUG_MODE:
        # pylint: disable = C0301
        log_file_path = "F:\\minecraft_servers\\server_tfc_halloween\\itzg\\minecraft-server"
    else:
        log_file_path = "minecraft-server"
    chat_parser = MinecraftChatParser(log_file_path)
    channel = bot.get_channel(CHANNEL_ID)

    # Check for a new messages every 1 second
    while True:
        message = chat_parser.get_chat_message()
        while message:
            await channel.send(message)
            await asyncio.sleep(0.1)
            message = chat_parser.get_chat_message()

        await asyncio.sleep(1)


@bot.command(name="list")
async def get_list_of_players(ctx: commands.Context) -> None:
    """
    Get the list of online players on the Minecraft server.

    Parameters:
    - ctx: Context object for the command execution.
    """
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        try:
            players_list = rcon.send_command("/list")
            if players_list:
                players_list = players_list.split("\n")[0]
                await ctx.send(players_list)
            else:
                await ctx.send("Не удалось получить список игроков.")
        except Exception:
            await ctx.send("Не удалось отправить сообщение не сервер...")


@bot.command(name="info")
async def get_list_of_cammands(ctx: commands.Context) -> None:
    """
    Get the list of available commands.

    Parameters:
    - ctx: Context object for the command execution.
    """
    # Check if the message is from the desired channel
    if ctx.channel.id == CHANNEL_ID:
        await ctx.send("Доступные команды: /list, /info")


@bot.event
async def on_command_error(ctx: commands.Context, error: Any) -> None:
    """
    Handle errors that occur during command execution.

    Parameters:
    - ctx: Context object for the command execution.
    - error: The error that occurred during command execution.
    """
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "Неизвестная комманда, введите /info "
            "чтобы узнать все доступные команды."
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
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    if message.author == bot.user:
        return
    # Check if the message is from the desired channel
    if message.channel.id == CHANNEL_ID:
        # Process the message or reply to it
        try:
            rcon.send_say_command(
                f"<{message.author.display_name}>: {message.content}"
            )
        except Exception:
            await message.channel.send(
                "Не удалось отправить сообщение не сервер..."
            )


@bot.command()
async def send_message(message: discord.Message) -> None:
    """
    Send a message to a specified channel.

    Parameters:
        message (str): The message to be sent.

    Returns:
        None
    """
    # Get the desired channel by ID
    channel = bot.get_channel(CHANNEL_ID)

    # Send a message to the channel
    await channel.send(message)


def main():
    """Main entry point."""
    bot.run(DISCORD_ACCESS_TOKEN)
