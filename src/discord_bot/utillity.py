"""Module for discord_bot utillity finctions."""
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional, Tuple

import discord
from loguru import logger


async def parse_message_reference(
    message: discord.Message,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse a Discord message reference and return the nickname
    (or display name if server-nickname not exists), of the referenced
    user, the content (text) of the referenced message and information
    about attachment images.

    Args:
        message (discord.Message): The incoming message.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: A tuple
            containing the nickname of the referenced user (or None),
            the content of the referenced message (or None) and information
            about attachment images (or None).
    """
    ref_author_name, ref_content, attachment_images = None, None, None
    if message.reference:
        try:
            ref_message = await message.channel.fetch_message(
                message.reference.message_id
            )

        except discord.NotFound:
            # Handle case where the referenced message is not found.
            logger.warning("Message reference NotFound.")
            return ref_author_name, ref_content, attachment_images

        # Retrieve the user associated with the referenced message.
        ref_message_users = await message.guild.query_members(
            user_ids=[ref_message.author.id]
        )

        if ref_message_users:
            # There should be only one user, so get the first item in the list.
            ref_message_user = ref_message_users[0]
            # Extract the nickname (or display name) of the referenced user.
            ref_author_name = (
                ref_message_user.nick or ref_message_user.display_name
            )
        if ref_message.attachments:
            attachment_images = "[картинка] "
        # Get the content of the referenced message.
        ref_content = ref_message.content
    return ref_author_name, ref_content, attachment_images


async def parse_formatted_message_reference(
    message: discord.Message,
    max_ref_message_length: int = 100,
    max_nickname_length: int = 10,
) -> str:
    """
    Parse a Discord message reference to create a formatted
    message string.

    Args:
        message (discord.Message): The incoming message.
        max_ref_message_length (int): Maximum length for the referenced
            message.
        max_nickname_length (int):  Maximum length for the referenced
            message author.
    Returns:
        str: Formatted message string, including the referenced message
            content.

    Note:
        If the referenced message is not found or an error occurs during
        retrieval, an empty string will be returned.
    """
    ref_message = ""
    if message.reference:
        try:
            ref_message = await message.channel.fetch_message(
                message.reference.message_id
            )

        except discord.NotFound:
            logger.warning("Message reference NotFound.")
            return ""

        (
            ref_author_name,
            ref_content,
            attachment_images,
        ) = await parse_message_reference(message)
        if ref_content:
            if not ref_author_name:
                ref_author_name = "unknown"

        if not attachment_images:
            attachment_images = ""
        if ref_content and len(ref_content) > max_ref_message_length:
            ref_content = f"{ref_content[:max_ref_message_length]}..."
        if ref_author_name and len(ref_author_name) > max_nickname_length:
            ref_author_name = f"{ref_author_name[:max_nickname_length]}..."
        ref_message = (
            f"[{ref_author_name}: {attachment_images}{ref_content}] -> "
        )
    return ref_message


async def parse_message(
    message: discord.Message,
    max_ref_message_length: int = 100,
    max_nickname_length: int = 10,
) -> str:
    """
    Parse a Discord message to create a formatted message string.

    Args:
        message (discord.Message): The incoming message.
        max_ref_message_length (int): Maximum length for the
            referenced message.
        max_nickname_length (int):  Maximum length for the referenced
            message author.
    Returns:
        str: Formatted message string.
    """
    message_attachment = ""
    if message.attachments:
        message_attachment = "[картинка] "

    message_reference = await parse_formatted_message_reference(
        message,
        max_ref_message_length=max_ref_message_length,
        max_nickname_length=max_nickname_length,
    )
    message_text = (
        f"<{message.author.display_name}>: "
        f"{message_attachment}{message_reference}{message.content}"
    )
    return message_text


def get_config(config_path: str | os.PathLike) -> ConfigParser:
    """
    Loads and validates a configuration file, ensuring all required sections
    and options are present. If any required section or option is missing,
    it is added with a default value.

    Args:
        config_path (str | os.PathLike): The file path
            to the configuration file.

    Returns:
        ConfigParser: The configuration object with all required
            sections and options
    """

    default_config = {
        "DISCORD": {
            "CHANNEL_ID": "",
            "DISCORD_ACCESS_TOKEN": "",
        },
        "MC_SERVER": {
            "RCON_HOST": "",
            "RCON_PORT": "",
            "RCON_SECRET": "",
        },
    }
    config = ConfigParser()

    # Read the configuration file if it exists
    config_path = Path(config_path)
    config.read(config_path)

    # Ensure each section and option exists, based on DEFAULT_CONFIG
    for section, options in default_config.items():
        if not config.has_section(section):
            config.add_section(section)

        for option, default_value in options.items():
            if option not in config[section]:
                config[section][option] = str(default_value)

    # Write the updated config if any new parameters were added
    with config_path.open("w", encoding="utf-8") as fw:
        config.write(fw)

    return config
