"""Tests for src/chat_parser/chat_parser.py."""
# pylint: disable = W0212
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from src.chat_parser import chat_parser
from src.chat_parser.chat_parser import (
    VanishHandlerBase,
    VanishHandlerMasterPerki,
)
from src.chat_parser.custom_exceptions import ServerStarted, ServerStopped

TEST_DATA_DIR = Path(__file__).parent / "test_data"


class MockVanishHandlerBase(VanishHandlerBase):
    """Mock VanishHandlerBase."""

    def extract_username(self, msg):
        """Mock extract_username."""
        return ""

    def is_vanished(self, _: str) -> bool:
        """Mock is_vanished."""
        return False

    def is_unvanished(self, _: str) -> bool:
        """Mock is_unvanished."""
        return False


def add_text(file_path: str, text: str = "") -> None:
    """Add text into file."""
    with open(file_path, "a", encoding="utf-8") as fw:
        fw.write(text)

    # wait until system update file information
    time.sleep(0.1)


def test_manage_server_status_stopped_message(vanish_handler):
    """Simulate message with 'stopped' pattern from server."""
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.18.2", vanish_handler
    )
    # pylint: disable = C0301
    test_message = "[25Nov2024 23:05:38.154] [Server thread/INFO] [net.minecraft.server.MinecraftServer/]: [Rcon] SERVER STOPPED..."

    assert chat._is_server_working is True
    with pytest.raises(ServerStopped):
        chat._detect_server_status_change(test_message)

    assert chat._is_server_working is False


def test_manage_server_status_started_message(vanish_handler):
    """
    Simulate message with 'started' pattern from server
    with the voice chat mode.
    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.18.2",
        vanish_handler,
        is_server_working=False,
    )
    # pylint: disable = C0301
    test_message = "[25Nov2024 23:03:38.562] [Server thread/INFO] [net.minecraft.server.MinecraftServer/]: [Rcon] SERVER STARTED!!!"

    assert chat._is_server_working is False

    with pytest.raises(ServerStarted):
        chat._detect_server_status_change(test_message)

    assert chat._is_server_working is True


def test_extract_chat_message_server_not_working(tmp_path, vanish_handler):
    """Check if message do not extracts when server status is stopped."""
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(
        tmp_path,
        vanish_handler,
        is_server_working=False,
    )
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " <Iluvator> TEST"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_existing(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with existing chat message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " <Iluvator> TEST"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "<Iluvator> TEST"


def test_extract_chat_message_joined_the_game(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with "joined the game" message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator joined the game"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator joined the game"


def test_extract_chat_message_left_the_game(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with "left the game" message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator left the game"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator left the game"


def test_extract_chat_message_slain_message(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with "player slain by" message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator was slain by Zombie"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator was slain by Zombie"


def test_extract_chat_message_goal_message(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with "player slain by" message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " MACTEP has reached the goal [Pink Unicorn]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "MACTEP has reached the goal [Pink Unicorn]"


def test_extract_chat_message_empty(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with empty chat message.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " "
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_dismatch_pattern(vanish_handler):
    """
    Test extract_chat_message() with dismatching pattern.
    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.18.2", vanish_handler
    )
    test_message = (
        "test 1"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " test message"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_anti_pattern(vanish_handler):
    """
    Test extract_chat_message() with anti pattern.
    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.18.2", vanish_handler
    )
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " [Iluvator: Set own game mode to Creative Mode]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_incorrect_message_type(tmp_path, vanish_handler):
    """
    Test extract_chat_message() with incorrect message type.
    """
    # Create a temporary text file
    temp_dir = os.path.join(
        tmp_path,
        "logs",
    )
    os.makedirs(temp_dir)
    temp_log = os.path.join(
        temp_dir,
        "latest.log",
    )
    add_text(temp_log, "")
    chat = chat_parser.MinecraftChatParser(tmp_path, vanish_handler)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " [Iluvator: Set own game mode to Creative Mode]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_get_chat_message(vanish_handler):
    """
    Test the extraction of chat messages from a Minecraft log file.

    This test sets up a MinecraftChatParser, sets the last position,
    and then retrieves chat messages until none are left. It compares
    the extracted messages with the expected ones.

    Note: Uncommented lines in expected_messages are exist in the log
    file.

    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.18.2", vanish_handler
    )
    chat.set_last_position()
    chat.reset_file_modified_timestamp()
    expected_messages = [
        "velada joined the game",
        "velada left the game",
        # "[Rcon] test",
        # "[Rcon] test",
        # "[Rcon] test11",
        "Iluvator joined the game",
        # "[Iluvator: Set own game mode to Creative Mode]",
        "# Сервер остановлен.",
        "# Сервер запущен.",
        "<Iluvator> TEST",
        "<Iluvator> из игры",
        "Iluvator was slain by Zombie",
        "<Iluvator> из игры",
        "Iluvator left the game",
        "Iluvator joined the game",
        "Iluvator left the game",
    ]
    new_messages = []
    while True:
        try:
            message = chat.get_chat_message()
        except (ServerStopped, ServerStarted) as msg:
            message = str(msg)
        if not message:
            break
        new_messages.append(message)

    for index, (expected, actual) in enumerate(
        zip(expected_messages, new_messages)
    ):
        assert expected == actual, (
            f"Message mismatch at index {index}:\n"
            f"  Expected: {expected}\n"
            f"  Actual: {actual}\n"
            f"  Full context: {new_messages}"
        )


def test_get_chat_message_1_19_2(vanish_handler):
    """
    Test for minecraft version 1.19.2
    Test the extraction of chat messages from a Minecraft log file.

    This test sets up a MinecraftChatParser, sets the last position,
    and then retrieves chat messages until none are left. It compares
    the extracted messages with the expected ones.

    Note: Uncommented lines in expected_messages are exist in the log
    file.

    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.19.2", vanish_handler
    )
    chat.set_last_position()
    chat.reset_file_modified_timestamp()
    expected_messages = [
        "# Сервер остановлен.",
        "# Сервер запущен.",
        "Iluvator joined the game",
        "Iluvator has made the advancement [Alex's Mobs]",
        "Iluvator has made the advancement [A Small Smackerel]",
        "<Iluvator> Test",
        "<Iluvator> kill",
        "Iluvator fell out of the world",
        "Iluvator left the game",
    ]
    new_messages = []

    while True:
        try:
            message = chat.get_chat_message()
        except (ServerStopped, ServerStarted) as msg:
            message = str(msg)
        if not message:
            break
        new_messages.append(message)

    for expected, actual in zip(expected_messages, new_messages):
        assert expected == actual, f"Expected: {expected}, Actual: {actual}"


@pytest.mark.parametrize(
    "msg",
    (
        "Iluvator joined the game",
        "Iluvator has made the advancement [Alex's Mobs]",
        "Iluvator has made the advancement [A Small Smackerel]",
        "<Iluvator> Test",
        "<Iluvator> kill",
        "Iluvator fell out of the world",
        "Iluvator left the game",
    ),
)
def test___extract_username_valid_format(
    vanish_handler,
    msg: str,
):
    """
    Tests the `_extract_username` method with messages
    that follow valid formats.
    """
    chat = chat_parser.MinecraftChatParser(
        TEST_DATA_DIR / "1.19.2", vanish_handler
    )

    username = chat._extract_username(msg)

    assert username == "Iluvator", f"Username was notfound: {msg}"


class TestVanishHandlerBase:
    """Tests for VanishHandler class."""

    def test_initialize_handler_if_vanished_file_is_not_exists(
        self, tmp_path: Path
    ):
        """
        Test initialization when the vanished file does not exist.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)

        assert handler._vanished_players == set()

    def test_load_data_with_valid_file(self, tmp_path: Path):
        """
        Test loading data from a valid file.
        """
        data = {"player1", "player2"}
        path = tmp_path / "temp"
        path.write_text(json.dumps(list(data)), encoding="utf-8")
        handler = MockVanishHandlerBase(path)

        assert handler._vanished_players == data

    def test_load_data_with_invalid_format(self, tmp_path: Path):
        """
        Test loading data from a file with invalid format.
        """
        path = tmp_path / "temp"
        path.write_text('{"invalid": "format"}', encoding="utf-8")

        handler = MockVanishHandlerBase(path)

        assert handler._vanished_players == set()

    def test_dump_data_creates_file(self, tmp_path: Path):
        """
        Test that _dump_data creates the file if it does not exist
        and writes the data.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        handler._vanished_players = {"player1", "player2"}

        handler._dump_data()

        assert path.exists()
        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert set(data) == handler._vanished_players

    def test_dump_data_overwrites_existing_file(self, tmp_path: Path):
        """
        Test that _dump_data overwrites the content of an existing file.
        """
        path = tmp_path / "temp"
        initial_data = ["initial_player"]
        path.write_text(json.dumps(initial_data), encoding="utf-8")

        handler = MockVanishHandlerBase(path)
        handler._vanished_players = {"player1", "player2"}

        handler._dump_data()

        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert set(data) == handler._vanished_players

    def test_dump_data_with_empty_list(self, tmp_path: Path):
        """
        Test that _dump_data correctly writes an empty list.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        handler._vanished_players = set()

        handler._dump_data()

        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert data == []

    def test__vanish_player(self, tmp_path: Path):
        """
        Test that _unvanish_player removes a username from vanished players
        and updates the data file.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        vanished_players = ["test1", "test2"]

        handler._vanish_player(vanished_players[0])
        handler._vanish_player(vanished_players[1])

        assert handler._vanished_players == set(vanished_players)
        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert set(data) == set(vanished_players)

    def test__vanish_player_is_case_insensitive(self, tmp_path: Path):
        """
        Test that _vanish_player treats usernames case-insensitively.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)

        handler._vanish_player("TestUser")
        handler._vanish_player("testuser")  # Same name, different case

        assert handler._vanished_players == {"testuser"}
        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert data == ["testuser"]

    def test__unvanish_player_raises_keyerror_if_not_found(
        self, tmp_path: Path
    ):
        """
        Test that _unvanish_player raises KeyError if the username
        does not exist.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)

        handler._vanished_players = {"test1"}
        handler._unvanish_player("test2")  # Username not in the set

        assert handler._vanished_players == {"test1"}

    def test__vanish_and_unvanish_combined(self, tmp_path: Path):
        """
        Test the combined behavior of _vanish_player and _unvanish_player.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)

        # Vanish players
        handler._vanish_player("user1")
        handler._vanish_player("user2")
        assert handler._vanished_players == {"user1", "user2"}

        # Unvanish one player
        handler._unvanish_player("user1")
        assert handler._vanished_players == {"user2"}

        # Vanish another player
        handler._vanish_player("user3")
        assert handler._vanished_players == {"user2", "user3"}

        # Check final state in file
        with path.open(encoding="utf-8") as fr:
            data = json.load(fr)
        assert set(data) == {"user2", "user3"}

    def test_process_message_vanished_msg(
        self, tmp_path: Path, mocker: MockerFixture
    ):
        """
        Test processing a "vanished" message adds the player
        to the vanished list and calls _dump_data.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        mocker.patch.object(handler, "is_vanished", return_value=True)
        handler._dump_data = MagicMock()  # type: ignore

        username = "MACTEP"
        msg = f"{username} vanished"
        mocker.patch.object(handler, "extract_username", return_value=username)
        output = handler.process_message(msg, None)

        assert output == handler.LEFT_GAME_PATTERN.format(username)
        assert username.lower() in handler._vanished_players
        handler._dump_data.assert_called_once()

    def test_process_message_unvanished_msg(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ):
        """
        Test processing an "unvanished" message removes the player
        from the vanished list and calls _dump_data.
        """
        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        mocker.patch.object(handler, "is_unvanished", return_value=True)
        handler._dump_data = MagicMock()  # type: ignore
        handler._vanished_players = {"mactep", "velada"}
        username = "MACTEP"
        mocker.patch.object(handler, "extract_username", return_value=username)
        msg = f"{username} unvanished"

        output = handler.process_message(msg)

        assert output == handler.JOINED_GAME_PATTERN.format(username)
        assert username.lower() not in handler._vanished_players
        handler._dump_data.assert_called_once()

    def test_process_message_simple_msg(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ):
        """
        Test processing a normal message does not modify vanished
        players or call _dump_data.
        """

        path = tmp_path / "temp"
        handler = MockVanishHandlerBase(path)
        handler._dump_data = MagicMock()  # type: ignore
        handler._vanished_players = {"velada"}
        username = "MACTEP"
        msg = f"{username} unvanished"
        mocker.patch.object(handler, "extract_username", return_value=username)

        output = handler.process_message(msg, username)

        assert output == msg
        assert username.lower() not in handler._vanished_players
        handler._dump_data.assert_not_called()


class TestVanishHandlerMasterPerki:
    """Tests for VanishHandlerMasterPerki."""

    def test_extract_username(self, tmp_path: Path):
        """
        Test extracting a username from a message.
        """
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        message = "[Player123: [Vanishmod] Player123 vanished]"
        result = handler.extract_username(message)

        assert result == "Player123"

    def test_is_vanished_valid_message(self, tmp_path: Path):
        """Test is_vanished with a valid vanished message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = "[Iluvator: [Vanishmod] Iluvator vanished]"
        assert handler.is_vanished(msg) is True

    def test_is_vanished_invalid_message(self, tmp_path: Path):
        """Test is_vanished with an invalid vanished message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = "[Iluvator: [Vanishmod] Iluvator something else]"
        assert handler.is_vanished(msg) is False

    def test_is_unvanished_valid_message(self, tmp_path: Path):
        """Test is_unvanished with a valid unvanished message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = "[Iluvator: [Vanishmod] Iluvator unvanished]"
        assert handler.is_unvanished(msg) is True

    def test_is_unvanished_invalid_message(self, tmp_path: Path):
        """Test is_unvanished with an invalid unvanished message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = "[Iluvator: [Vanishmod] Iluvator vanished]"
        assert handler.is_unvanished(msg) is False

    def test_is_vanished_empty_message(self, tmp_path: Path):
        """Test is_vanished with an empty message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = ""
        assert handler.is_vanished(msg) is False

    def test_is_unvanished_empty_message(self, tmp_path: Path):
        """Test is_unvanished with an empty message."""
        handler = VanishHandlerMasterPerki(tmp_path / "temp")
        msg = ""
        assert handler.is_unvanished(msg) is False

    def test_get_chat_message_with_vanish_mod_1_20_1(
        self,
        vanish_handler,
    ):
        """
        Test whether MinecraftChatParser correctly parses chat messages,
        including scenarios where players vanish or unvanish.
        """
        chat = chat_parser.MinecraftChatParser(
            TEST_DATA_DIR / "1.20.1_vanish_master_perki", vanish_handler
        )
        chat.set_last_position()
        chat.reset_file_modified_timestamp()
        expected_messages = [
            "Iluvator joined the game",
            "<Iluvator> 213",
            "Iluvator was killed",
            # [Iluvator: Killed Iluvator]\n
            "Iluvator left the game",  # Here vanished
            # <Iluvator> 213
            # Iluvator left the game
            # Iluvator joined the game
            # "<Iluvator> 123",
            # "Iluvator left the game",
            # Iluvator joined the game
            # "<Iluvator> 456",
            "Iluvator joined the game",  # Here unvanished
            "<Iluvator> 123",
            "Iluvator left the game",
        ]
        new_messages = []

        for _ in range(len(expected_messages)):
            message = chat.get_chat_message()
            new_messages.append(message)

        for index, (expected, actual) in enumerate(
            zip(expected_messages, new_messages)
        ):
            assert expected == actual, (
                f"Message mismatch at index {index}:\n"
                f"  Expected: {expected}\n"
                f"  Actual: {actual}\n"
                f"  Full context: {new_messages}"
            )
