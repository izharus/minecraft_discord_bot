"""Tests for src/chat_parser/chat_parser.py."""
# pylint: disable = W0212
import os
import time

from src.chat_parser import chat_parser


def add_text(file_path: str, text: str = "") -> None:
    """Add text into file."""
    with open(file_path, "a", encoding="utf-8") as fw:
        fw.write(text)

    # wait until system update file information
    time.sleep(0.1)


def test_manage_server_status_stopped_message():
    """Simulate message with 'stopped' pattern from server."""
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(temp_server_dir)
    # pylint: disable = C0301
    test_message = "[05Dec2023 22:03:16.966] [Server thread/INFO] [net.minecraft.server.MinecraftServer/]: Stopping server"

    assert chat._is_server_working is True
    server_message = chat._manage_server_status(test_message)

    assert server_message == "# Сервер остановлен."
    assert chat._is_server_working is False


def test_manage_server_status_starting_message():
    """Simulate message with 'starting' pattern from server."""
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(temp_server_dir)
    # pylint: disable = C0301
    test_message = "[20Dec2023 07:50:48.256] [main/INFO] [cpw.mods.modlauncher.Launcher/MODLAUNCHER]: ModLauncher running: args [--launchTarget, forgeserver, --fml.forgeVersion, 40.2.9, --fml.mcVersion, 1.18.2, --fml.forgeGroup, net.minecraftforge, --fml.mcpVersion, 20220404.173914]"

    assert chat._is_server_working is True

    server_message = chat._manage_server_status(test_message)

    assert server_message == "# Сервер запускается..."
    assert chat._is_server_working is False


def test_manage_server_status_started_message():
    """Simulate message with 'started' pattern from server."""
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(
        temp_server_dir,
        is_server_working=False,
    )
    # pylint: disable = C0301
    test_message = "[20Dec2023 07:51:15.915] [VoiceChatServerThread/INFO] [voicechat/]: [voicechat] Voice chat server started at port 3520"

    assert chat._is_server_working is False

    server_message = chat._manage_server_status(test_message)
    assert server_message == "# Сервер запущен."
    assert chat._is_server_working is True


def test_extract_chat_message_server_not_working(tmp_path):
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
        is_server_working=False,
    )
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " <Iluvator> TEST"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_existing(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " <Iluvator> TEST"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "<Iluvator> TEST"


def test_extract_chat_message_joined_the_game(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator joined the game"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator joined the game"


def test_extract_chat_message_left_the_game(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator left the game"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator left the game"


def test_extract_chat_message_slain_message(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " Iluvator was slain by Zombie"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "Iluvator was slain by Zombie"


def test_extract_chat_message_goal_message(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " MACTEP has reached the goal [Pink Unicorn]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == "MACTEP has reached the goal [Pink Unicorn]"


def test_extract_chat_message_empty(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " "
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_dismatch_pattern():
    """
    Test extract_chat_message() with dismatching pattern.
    """
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(temp_server_dir)
    test_message = (
        "test 1"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " test message"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_anti_pattern():
    """
    Test extract_chat_message() with anti pattern.
    """
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(temp_server_dir)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " [Iluvator: Set own game mode to Creative Mode]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_extract_chat_message_incorrect_message_type(tmp_path):
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
    chat = chat_parser.MinecraftChatParser(tmp_path)
    test_message = (
        "[14Dec2023 07:29:06.982] [Server thread/INFO]"
        " [net.minecraft.server.dedicated.DedicatedServer/]:"
        " [Iluvator: Set own game mode to Creative Mode]"
    )
    test_message = chat.extract_chat_message(test_message)
    assert test_message == ""


def test_get_chat_message():
    """
    Test the extraction of chat messages from a Minecraft log file.

    This test sets up a MinecraftChatParser, sets the last position,
    and then retrieves chat messages until none are left. It compares
    the extracted messages with the expected ones.

    Note: Uncommented lines in expected_messages are exist in the log
    file.

    """
    temp_server_dir = os.path.dirname(__file__)
    chat = chat_parser.MinecraftChatParser(temp_server_dir)
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
        "# Сервер запускается...",
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
        message = chat.get_chat_message()
        if not message:
            break
        new_messages.append(message)

    assert len(expected_messages) == len(new_messages)
    for expected, actual in zip(expected_messages, new_messages):
        assert expected == actual, f"Expected: {expected}, Actual: {actual}"
