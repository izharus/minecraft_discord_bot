"""
This modules provides class for extracting a new chat messages from
a minecraft log file.
"""
import json
import os
import re
import time
from abc import abstractmethod
from pathlib import Path
from typing import Final, Optional

from loguru import logger

from .log_parser import FileChangesUtillity

USERNAME_P: Final = r"[a-zA-Z]+[a-zA-z0-9]*"


class MinecraftChatParser(FileChangesUtillity):
    """
    This class extends a FileChangesUtillity class and
    implements a get_chat_message() function for parsing
    a chat messages from the server log files.
    """

    def __init__(
        self,
        minecraft_server_dir: os.PathLike,
        vanish_handler: "VanishHandlerBase",
        is_server_working: bool = True,
    ) -> None:
        self.log_path = Path(minecraft_server_dir) / "logs" / "latest.log"
        self._vanish_handler = vanish_handler
        # pylint: disable=C0301
        self._chat_message_patterns_list = [
            # Minecraft version 1.19.2
            "[Server thread/INFO] [net.minecraft.server.MinecraftServer/]: ",
            # Minecraft version 1.18.4
            "[Server thread/INFO] [net.minecraft.server.dedicated.DedicatedServer/]: ",
            "[Not Secure] ",
        ]
        self._message_struct_pattern = (
            rf"^\<({USERNAME_P})\> .*?$|"
            rf"^({USERNAME_P}) [a-zA-Z]+[a-zA-z0-9]* .*?$"
        )
        FileChangesUtillity.__init__(self, self.log_path)
        self._is_server_working = is_server_working

        self._stopped_server_pattern = r"^.*\[Rcon\] SERVER STOPPED\.\.\.$"
        self._started_server_pattern = r"^.*\[Rcon\] SERVER STARTED!!!$"

    def _manage_server_status(
        self,
        message: str,
    ) -> str:
        """
        Changes _is_server_working server status if any patterns im nessage
        will found.

        Args:
            message (str): New string on log file from server.

        Returns:
            str: A custom server message in human-reading style or an
                empty string, if no any patterns will be found.
        """
        if re.match(self._stopped_server_pattern, message):
            logger.info("SERVER WAS STOPPED")
            self._is_server_working = False
            return "# Сервер остановлен."
        elif re.match(self._started_server_pattern, message):
            logger.info("SERVER WAS STARTED")
            self._is_server_working = True
            return "# Сервер запущен."
        return ""

    def extract_chat_message(self, message: str) -> str:
        """
        Extracts the user chat message from the input log message,
        skipping other logs.

        Args:
            message (str): The input log message.

        Returns:
            str: The extracted user chat message, or an empty
                string if not found.
        """
        server_message = self._manage_server_status(message)
        if server_message:
            return server_message
        if not self._is_server_working or (
            self._chat_message_patterns_list[0] not in message
            and self._chat_message_patterns_list[1] not in message
        ):
            return ""

        # Apply the split_message function to each pattern in the list
        chat_message = message
        for pattern in self._chat_message_patterns_list:
            chat_message = chat_message.split(pattern)[-1]

        username = self._extract_username(chat_message)
        return self._vanish_handler.process_message(chat_message, username)

    def get_chat_message(self) -> str:
        """
        Retrieves the next user chat message from the continuously
        monitored log file.

        Returns:
            str: The extracted user chat message, or an empty
                string if no new chat messages are found.
        """
        while True:
            line = self.get_new_line()
            if not line:
                break
            chat_message = self.extract_chat_message(line)
            if chat_message:
                return chat_message.rstrip()
        return ""

    def _extract_username(self, msg: str) -> Optional[str]:
        matched = re.match(self._message_struct_pattern, msg)
        if matched:
            # Find the first non-None group in the match
            for group in matched.groups():
                if group:
                    return group
        return None


class VanishHandlerBase:
    """A class to handle vanished players for a given data file."""

    LEFT_GAME_PATTERN = "{} left the game"
    JOINED_GAME_PATTERN = "{} joined the game"

    # [Iluvator: [Vanishmod] Iluvator vanished]
    VANISHED_PATTERN: str
    # [Iluvator: [Vanishmod] Iluvator unvanished]
    UNVANISHED_PATTERN: str

    def __init__(self, data_path: Path):
        """
        Initializes the VanishHandler with the specified data file path.

        Args:
            data_path (Path): The path to the data file.
        """
        self._data_path = data_path
        self._vanished_players = self._load_data(self._data_path)

    def _load_data(self, data_path: Path) -> set:
        """
        Loads vanished players from the data file, creating it if necessary.

        Args:
            data_path (Path): The path to the data file.

        Returns:
            set: A set of vanished players.
        """
        try:
            with data_path.open(encoding="utf-8") as fr:
                data = json.load(fr)
                if not isinstance(data, list):
                    logger.warning("Data file must contain a set.")
                else:
                    return set(data)
        except FileNotFoundError:
            logger.info(f"Data file {data_path} does not exist.")
        except json.JSONDecodeError as e:
            logger.warning(
                f"Data file {data_path} is corrupted: {e}. "
                "Replacing with an empty list."
            )
        return set()

    def _dump_data(self):
        with self._data_path.open("w", encoding="utf-8") as fw:
            json.dump(list(self._vanished_players), fw)

    @abstractmethod
    def extract_username(self, msg: str) -> str:
        """
        Extracts the username from the message if it matches
        a vanished or unvanished pattern.

        Args:
            msg (str): The message string.

        Returns:
            str: The extracted username in lowercase, or
                an empty string if no match is found.
        """

    @abstractmethod
    def is_vanished(self, msg: str) -> bool:
        """True if msg indicates that player was vanished."""

    @abstractmethod
    def is_unvanished(self, msg: str) -> bool:
        """True if msg indicates that player was unvanished."""

    def _vanish_player(self, username: str) -> None:
        """Make username vanished."""
        self._vanished_players.add(username.lower())
        self._dump_data()

    def _unvanish_player(self, username: str) -> None:
        """Make username vanished."""
        try:
            self._vanished_players.remove(username.lower())
        except KeyError:
            logger.warning(f"Player is not vanished: {username}")
            return
        self._dump_data()

    def process_message(self, msg: str, username: Optional[str] = None) -> str:
        """
        Processes a message to handle vanished/unvanished player actions.

        Args:
            msg (str): The message to be processed.
            username (str): Username from the message.

        Returns:
            str:
                - For valid user messages:
                    - An empty string if the player is vanished.
                    - The original message otherwise.
                - For vanish mod messages:
                    - A fake "player left" message if the player vanishes.
                    - A fake "player joined" message if the player unvanishes.
                - For unrecognized server messages: An empty string.
        """
        if username:
            # If message recognized as valid user message
            if username.lower() in self._vanished_players:
                logger.info(f"Skipping vanished player msg: {msg}")
                return ""
            return msg

        # It's not a valid user message
        # Check if it's a message from a vanish mod
        username = self.extract_username(msg)
        if not username:
            return ""  # Message is no recognized, it's a server message

        if self.is_vanished(msg):
            self._vanish_player(username)
            logger.info(f"Player vanished: {username}")
            return self.LEFT_GAME_PATTERN.format(username)
        if self.is_unvanished(msg):
            self._unvanish_player(username)
            logger.info(f"Player unvanished: {username}")
            return self.JOINED_GAME_PATTERN.format(username)
        logger.warning(
            f"Could not recognize message as vanished/unvanished: {msg}"
        )
        return ""


class VanishHandlerMasterPerki(VanishHandlerBase):
    """
    Vanish handler for the mode from author MasterPerki:
    https://www.curseforge.com/minecraft/mc-mods/vanishmod
    """

    # [Iluvator: [Vanishmod] Iluvator vanished]
    VANISHED_PATTERN = rf"^\[({USERNAME_P}): \[Vanishmod\] {USERNAME_P} vanished\]$"  # pylint: disable=C0301
    # [Iluvator: [Vanishmod] Iluvator unvanished]
    UNVANISHED_PATTERN = rf"^\[({USERNAME_P}): \[Vanishmod\] {USERNAME_P} unvanished\]$"  # pylint: disable=C0301

    def extract_username(self, msg):
        for pattern in (self.VANISHED_PATTERN, self.UNVANISHED_PATTERN):
            match = re.match(pattern, msg)
            if match:
                return match.group(1)
        return ""

    def is_vanished(self, msg: str) -> bool:
        """True if msg indicates that player was vanished."""
        return bool(re.match(self.VANISHED_PATTERN, msg))

    def is_unvanished(self, msg: str) -> bool:
        """True if msg indicates that player was unvanished."""
        return bool(re.match(self.UNVANISHED_PATTERN, msg))


def main() -> None:
    """Example usage."""
    # pylint: disable = C0301
    filename = r"src\tests\chat_parser\test_data\1.18.2\logs\latest.log"
    # filename = 'F:\\server_imperial\\itzg\\minecraft-server\\logs\\test.txt'
    observer = MinecraftChatParser(
        Path(filename), VanishHandlerMasterPerki(Path("data\\vanished.json"))
    )
    while 1:
        time.sleep(1)
        print(observer.get_chat_message(), end="")  # noqa: T201
