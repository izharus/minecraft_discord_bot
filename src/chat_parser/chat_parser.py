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
from typing import List

from loguru import logger

from .log_parser import FileChangesUtillity


class MinecraftChatParser(FileChangesUtillity):
    """
    This class extends a FileChangesUtillity class and
    implements a get_chat_message() function for parsing
    a chat messages from the server log files.
    """

    def __init__(
        self,
        minecraft_server_dir: str,
        vanish_handler: "VanishHandlerMasterPerki",
        is_server_working: bool = True,
    ) -> None:
        self.log_path = os.path.join(
            minecraft_server_dir,
            "logs",
            "latest.log",
        )
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
            r"^\<[a-zA-Z]+[a-zA-z0-9]*\> .*?$|"
            r"^[a-zA-Z]+[a-zA-z0-9]* [a-zA-Z]+[a-zA-z0-9]* .*?$"
        )
        FileChangesUtillity.__init__(self, self.log_path)
        self._is_server_working = is_server_working

        self._stopped_server_pattern = (
            r"^\[.*?\] "
            r"\[Server thread/INFO\] \[net.minecraft.server.MinecraftServer/\]: Stopping server$"
        )
        self._starting_server_pattern = (
            r"^\[.*?\] \[main/INFO\] \[.*?\]: ModLauncher running: args "
            r"\[.*?\]$"
        )

        self._started_server_patterns_list = [
            (
                # server with the with the voicechat mode
                r"^\[.*?\] \[VoiceChatServerThread/INFO\] \[voicechat/\]: \[voicechat\] "
                r"Voice chat server started at port \d{4,6}$"
            ),
            (
                # server version 1.19.2
                r"^\[.*?\] \[Server thread/INFO\] \[net.minecraft.server.rcon.thread.RconThread/\]: "
                r"RCON running on .*?:\d{4,6}$"
            ),
        ]

    @staticmethod
    def _match_patterns(patterns: List[str], text: str):
        """
        Checks if the text matches at least one of the regular expressions
        in the provided list of patterns.

        Args:
            text (str): The text to check.
            patterns (list): A list of regular expressions
                to match against the text.

        Returns:
            bool: True if at least one expression in patterns
                matches the text, False otherwise.
        """
        # Iterate through the list of patterns
        for pattern in patterns:
            # If at least one pattern matches the text, return True
            if re.search(pattern, text):
                return True
        # If no pattern matches, return False
        return False

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
        if re.findall(self._stopped_server_pattern, message):
            logger.info("SERVER WAS STOPPED")
            self._is_server_working = False
            return "# Сервер остановлен."
        elif re.findall(self._starting_server_pattern, message):
            logger.info("SERVER IS STARTING")
            self._is_server_working = False
            return "# Сервер запускается..."

        elif self._match_patterns(self._started_server_patterns_list, message):
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

        if re.findall(self._message_struct_pattern, chat_message):
            return self._vanish_handler.process_message(chat_message)
        return ""

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


class VanishHandlerBase:
    """A class to handle vanished players for a given data file."""

    LEFT_GAME_PATTERN = "{} left the game"
    JOINED_GAME_PATTERN = "{} joined the game"

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

    def process_message(self, msg: str) -> str:
        """
        Processes a message to determine if a player is vanishing,
        unvanishing, or is already vanished. Takes actions accordingly
        and logs the events.

        Args:
            msg (str): The message to be processed.

        Returns:
            str: An empty string if the player vanishes or unvanishes, or
                if the player is already vanished. Otherwise, returns
                the original message.
        """
        username = self.extract_username(msg)
        if self.is_vanished(msg):
            self._vanish_player(username)
            logger.info(f"Player vanished: {username}")
            return self.LEFT_GAME_PATTERN.format(username)
        if self.is_unvanished(msg):
            self._unvanish_player(username)
            logger.info(f"Player unvanished: {username}")
            return self.JOINED_GAME_PATTERN.format(username)
        if username in self._vanished_players:
            logger.info(f"Skipping vanished player msg: {msg}")
            return ""
        return msg


class VanishHandlerMasterPerki(VanishHandlerBase):
    """
    Vanish handler for the mode from author MasterPerki:
    https://www.curseforge.com/minecraft/mc-mods/vanishmod
    """

    # [Iluvator: [Vanishmod] Iluvator vanished]
    VANISHED_PATTERN: Final = r"^\[\w+: \[Vanishmod\] \w+ vanished\]$"
    # [Iluvator: [Vanishmod] Iluvator unvanished]
    UNVANISHED_PATTERN: Final = r"^\[\w+: \[Vanishmod\] \w+ unvanished\]$"
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
    filename = (
        "F:\\minecraft_servers\\server_tfc_halloween\\itzg\\minecraft-server"
    )
    # filename = 'F:\\server_imperial\\itzg\\minecraft-server\\logs\\test.txt'
    observer = MinecraftChatParser(
        filename, VanishHandlerMasterPerki(Path("data\\vanished.json"))
    )
    while 1:
        time.sleep(1)
        print(observer.get_chat_message(), end="")  # noqa: T201
