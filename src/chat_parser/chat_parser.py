"""
This modules provides class for extracting a new chat messages from
a minecraft log file.
"""
import os
import re
import time
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
        is_server_working: bool = True,
    ) -> None:
        self.log_path = os.path.join(
            minecraft_server_dir,
            "logs",
            "latest.log",
        )
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
            return chat_message
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


def main() -> None:
    """Example usage."""
    # pylint: disable = C0301
    filename = (
        "F:\\minecraft_servers\\server_tfc_halloween\\itzg\\minecraft-server"
    )
    # filename = 'F:\\server_imperial\\itzg\\minecraft-server\\logs\\test.txt'
    observer = MinecraftChatParser(filename)
    while 1:
        time.sleep(1)
        print(observer.get_chat_message(), end="")  # noqa: T201
