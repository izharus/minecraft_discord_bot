"""Tests for rcon.py module."""
# pylint: disable=W0212
import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiomcrcon
import pytest
from pytest_mock import MockerFixture
from src.rcon_sender.rcon import AIOMcRcon, RCONSendCmdError


async def async_mock_connect(self: aiomcrcon.Client):
    """Mock aiomcrcon.Client.connect method."""
    self._ready = True


async def async_mock_close(self: aiomcrcon.Client):
    """Mock aiomcrcon.Client.close method."""
    self._ready = False


@pytest.mark.asyncio
async def test_connect_success(mocker: MockerFixture):
    """Test successful connection."""
    mock_connect = AsyncMock()
    mocker.patch.object(aiomcrcon.Client, "connect", mock_connect)
    client = AIOMcRcon(host="localhost", port=25575, password="password")
    await client.connect()
    mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_send_cmd_success(mocker: MockerFixture):
    """Test successful command send."""
    mock_send_cmd = AsyncMock(return_value=("OK", 0))
    mocker.patch.object(aiomcrcon.Client, "send_cmd", mock_send_cmd)
    client = AIOMcRcon(host="localhost", port=25575, password="password")
    result = await client.send_cmd("command")
    mock_send_cmd.assert_called_once_with("command")
    assert result == ("OK", 0)


@pytest.mark.asyncio
async def test_send_cmd_failed(mocker: MockerFixture):
    """Test send_cmd failure triggers reconnection."""
    mock_create_task = MagicMock()

    # Mocking create_task and connect methods
    mocker.patch.object(asyncio, "create_task", mock_create_task)
    mocker.patch.object(aiomcrcon.Client, "connect", async_mock_connect)
    mocker.patch.object(aiomcrcon.Client, "close", async_mock_close)
    mocker.patch.object(aiomcrcon.Client, "send_cmd", side_effect=Exception)
    client = AIOMcRcon(host="localhost", port=25575, password="password")

    # Establish initial connection
    await client.connect()

    # Expecting RCONSendCmdError when send_cmd fails
    with pytest.raises(RCONSendCmdError):
        await client.send_cmd("command")

    # Ensure reconnection task is triggered
    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_send_cmd_failed_multiple_retries(mocker: MockerFixture):
    """
    Test send_cmd failure retries multiple times but only calls
    create_task once.
    """

    mock_create_task = MagicMock()
    mocker.patch.object(asyncio, "create_task", mock_create_task)
    mocker.patch.object(aiomcrcon.Client, "connect", async_mock_connect)
    mocker.patch.object(aiomcrcon.Client, "close", async_mock_close)
    mocker.patch.object(
        aiomcrcon.Client, "send_cmd", side_effect=Exception
    )  # Simulating failure

    client = AIOMcRcon(host="localhost", port=25575, password="password")

    # Initial connection setup
    await client.connect()
    client._ready = True

    # Test send_cmd failure and RCONSendCmdError raised
    for _ in range(100):
        with pytest.raises(RCONSendCmdError):
            await client.send_cmd("command")

    # Ensure create_task was called only once (for the reconnection)
    mock_create_task.assert_called_once()
