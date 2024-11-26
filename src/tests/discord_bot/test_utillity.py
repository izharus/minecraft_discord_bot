"""Unittests for src/discord_bot/utillity.py."""
from configparser import ConfigParser
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from src.discord_bot.utillity import (
    get_config,
    parse_formatted_message_reference,
    parse_message,
    parse_message_reference,
)


@pytest.mark.asyncio
async def test_parse_message_reference_reference_not_found():
    """
    Test case for parse_message_reference when the referenced
    message is not found.
    """
    # Create a mock message
    mock_message = AsyncMock()
    # Set the side_effect of fetch_mock to raise NotFound
    mock_message.channel.fetch_message.side_effect = discord.NotFound(
        response=MagicMock(), message="Resource not found"
    )
    # Call the function under test
    (
        ref_author_name,
        ref_content,
        attachment_images,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert ref_author_name is None
    assert ref_content is None
    assert attachment_images is None


@pytest.mark.asyncio
async def test_parse_message_reference_reference_author_name_is_none():
    """
    Test case for parse_message_reference when the author name of referenced
    message is None.
    """
    # Create a mock reference message
    mock_ref_message = AsyncMock()
    # Set the content attribute
    mock_ref_message.content = "Reference text"
    mock_ref_message.attachments = None
    # Create a mock message
    mock_message = AsyncMock()
    mock_message.channel.fetch_message.return_value = mock_ref_message

    mock_ref_message_user = AsyncMock()
    mock_ref_message_user.nick = None
    mock_ref_message_user.display_name = None
    mock_message.guild.query_members.return_value = [mock_ref_message_user]

    (
        ref_author_name,
        ref_content,
        attachment_images,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert ref_author_name is None
    assert ref_content == "Reference text"
    assert attachment_images is None


@pytest.mark.asyncio
async def test_parse_message_reference_reference_nickname_is_empty():
    """
    Test case for parse_message_reference when the author name of referenced
    message is None.
    """
    # Create a mock reference message
    mock_ref_message = AsyncMock()
    # Set the content attribute
    mock_ref_message.content = "Reference text"
    # Create a mock message
    mock_message = AsyncMock()
    mock_message.channel.fetch_message.return_value = mock_ref_message

    mock_ref_message_user = AsyncMock()
    mock_ref_message_user.nick = None
    mock_ref_message_user.display_name = "display_name"
    mock_message.guild.query_members.return_value = [mock_ref_message_user]

    (
        ref_author_name,
        ref_content,
        _,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert ref_author_name is not None
    assert ref_author_name == "display_name"
    assert ref_content == "Reference text"


@pytest.mark.asyncio
async def test_parse_message_reference_reference_nickname_non_empty():
    """
    Test case for parse_message_reference when the author name of referenced
    message is None.
    """
    # Create a mock reference message
    mock_ref_message = AsyncMock()
    # Create a mock message
    mock_message = AsyncMock()
    mock_message.channel.fetch_message.return_value = mock_ref_message

    mock_ref_message_user = AsyncMock()
    mock_message.guild.query_members.return_value = [mock_ref_message_user]

    (
        _,
        _,
        attachment_images,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert attachment_images == "[картинка] "


@pytest.mark.asyncio
async def test_parse_message_reference_reference_attachment_non_empty():
    """
    Test case for parse_message_reference when the author name of referenced
    message is None.
    """
    # Create a mock reference message
    mock_ref_message = AsyncMock()
    # Set the content attribute
    mock_ref_message.content = "Reference text"
    mock_ref_message.attachment = MagicMock()
    # Create a mock message
    mock_message = AsyncMock()
    mock_message.channel.fetch_message.return_value = mock_ref_message

    mock_ref_message_user = AsyncMock()
    mock_ref_message_user.nick = "nick_name"
    mock_ref_message_user.display_name = "display_name"
    mock_message.guild.query_members.return_value = [mock_ref_message_user]

    (
        ref_author_name,
        ref_content,
        _,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert ref_author_name == "nick_name"
    assert ref_content == "Reference text"


@pytest.mark.asyncio
async def test_parse_message_reference_reference_is_empty():
    """
    Test case for parse_message_reference when the reference is empty.
    """
    # Create a mock reference message
    mock_ref_message = AsyncMock()
    # Set the content attribute
    mock_ref_message.content = "Reference text"
    # Create a mock message
    mock_message = AsyncMock()
    mock_message.reference = None

    (
        ref_author_name,
        ref_content,
        _,
    ) = await parse_message_reference(mock_message)

    # Assert that the result is an empty string
    assert ref_author_name is None
    assert ref_content is None


@pytest.mark.asyncio
async def test_parse_formatted_message_reference_found_message():
    """
    Test the case where a referenced message is found.
    """
    # Create a mock for the discord.Message object
    message_mock = AsyncMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=(
            "JohnDoe",
            "Hello, world!",
            None,
        ),
    ):
        result = await parse_formatted_message_reference(message_mock)

    # Assert the expected formatted message
    assert result == "[JohnDoe: Hello, world!] -> "


@pytest.mark.asyncio
async def test_parse_formatted_message_reference_not_found_message():
    """
    Test the case where the referenced message is not found.
    """
    message_mock = AsyncMock()
    message_mock.reference = None

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=(None, None, None),
    ):
        result = await parse_formatted_message_reference(message_mock)

    # Assert that an empty string is returned
    assert result == ""


@pytest.mark.asyncio
async def test_parse_formatted_message_reference_no_content():
    """
    Test the case where the referenced message has no content.
    """
    message_mock = AsyncMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=("JohnDoe", None, None),
    ):
        result = await parse_formatted_message_reference(message_mock)

    # Assert the expected formatted message
    assert result == "[JohnDoe: None] -> "


@pytest.mark.asyncio
async def test_parse_formatted_message_only_attachment():
    """
    Test the case where the referenced message has no content.
    """
    message_mock = AsyncMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=(
            "JohnDoe",
            "",
            "[картинка] ",
        ),
    ):
        result = await parse_formatted_message_reference(message_mock)

    # Assert the expected formatted message
    assert result == "[JohnDoe: [картинка] ] -> "


@pytest.mark.asyncio
async def test_parse_formatted_message_reference_author_name():
    """
    Test the case where the referenced message has no aothor name.
    """
    message_mock = AsyncMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=(None, "Hello, world!", None),
    ):
        result = await parse_formatted_message_reference(message_mock)

    # Assert the expected formatted message
    assert result == "[unknown: Hello, world!] -> "


@pytest.mark.asyncio
async def test_parse_formatted_message_reference_long_message():
    """
    Test the case where the referenced with long message.
    """
    message_mock = AsyncMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_message_reference",
        return_value=("JohnDoe", "Hello, world!", None),
    ):
        result = await parse_formatted_message_reference(
            message_mock,
            max_ref_message_length=10,
            max_nickname_length=1,
        )

    # Assert the expected formatted message
    assert result == "[J...: Hello, wor...] -> "


@pytest.mark.asyncio
async def test_parse_message_all_prefixes():
    """
    Test the case where a message has both attachments and a referenced
    message.
    """
    message_mock = AsyncMock()
    message_mock.attachments = MagicMock()
    message_mock.author.display_name = "JohnDoe"
    message_mock.content = "Message text"
    message_mock.reference.attachments = MagicMock()

    # Mock the parse_message_reference function
    with patch(
        "src.discord_bot.utillity.parse_formatted_message_reference",
        return_value="[JohnDoe: [картинка] test reference message] -> ",
    ):
        result = await parse_message(message_mock)

    # pylint: disable=C0301
    assert (
        result
        == "<JohnDoe>: [картинка] [JohnDoe: [картинка] test reference message] -> Message text"
    )


def test_get_config_creating_new_config(
    tmp_path: Path,
):
    """
    Test the `get_config` function for creating a new configuration file.
    """

    config = get_config(tmp_path / "config.ini")

    assert "CHANNEL_ID" in config["DISCORD"].keys()
    assert "DISCORD_ACCESS_TOKEN" in config["DISCORD"].keys()
    assert "rcon_host" in config["MC_SERVER"].keys()
    assert "rcon_port" in config["MC_SERVER"].keys()
    assert "rcon_port" in config["MC_SERVER"].keys()


def test_get_config_amending_new_config(
    tmp_path: Path,
):
    """
    Test the `get_config` function for amending an existing
    configuration file.
    """
    channel_id = "id_12345"
    server_path = "/etc/server/test_server"
    rcon_secret = "1234567890"
    tmp_path = tmp_path / "config.ini"
    config = ConfigParser()
    config.add_section("DISCORD")
    config.add_section("MC_SERVER")

    config["DISCORD"]["CHANNEL_ID"] = channel_id
    config["DISCORD"]["MINECRAFT_SERVER_PATH"] = server_path
    config["MC_SERVER"]["RCON_SECRET"] = rcon_secret

    with tmp_path.open("w", encoding="utf-8") as fw:
        config.write(fw)

    config = get_config(tmp_path)

    assert config["DISCORD"]["CHANNEL_ID"] == channel_id
    assert config["DISCORD"]["DISCORD_ACCESS_TOKEN"] == ""
    assert config["MC_SERVER"]["rcon_host"] == ""
    assert config["MC_SERVER"]["rcon_port"] == ""
    assert config["MC_SERVER"]["rcon_secret"] == rcon_secret
