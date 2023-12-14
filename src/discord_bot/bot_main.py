"""Main module of discod bot."""
# pylint: disable=C0411
import asyncio
import sys

import discord
from access import CHANNEL_ID, DISCORD_ACCESS_TOKEN
from discord.ext import commands

from ..chat_parser.chat_parser import MinecraftChatParser
from ..rcon_sender.rcon import RconLocalDocker

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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


@bot.event
async def on_message(message: str) -> None:
    """
    Event handler for processing incoming messages.

    Parameters:
        message (discord.Message): The incoming message.

    Returns:
        None
    """
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    if message.author == bot.user:
        return
    # Check if the message is from the desired channel
    if message.channel.id == CHANNEL_ID:
        # Process the message or reply to it
        try:
            if message.content == "/list":
                # TODO create method: get_list_of_player()
                await message.channel.send(rcon.send_command("/list"))
            else:
                rcon.send_say_command(message.content)
            # await message.channel.send(f"You said: {message.content}")
        except Exception:
            await message.channel.send(
                "Не удалось отправить сообщение не сервер..."
            )


@bot.command()
async def send_message(message: str) -> None:
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
