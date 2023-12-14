"""
This modules provides class for extracting a new chat messages from
a minecraft log file.
"""
import os
import re
import time

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
    ) -> None:
        self.log_path = os.path.join(
            minecraft_server_dir,
            "logs",
            "latest.log",
        )
        # pylint: disable=C0301
        self._chat_message_pattern = "[Server thread/INFO] [net.minecraft.server.dedicated.DedicatedServer/]: "
        self._message_struct_pattern = (
            r"\<.*?\>.*?|\b\w+\b left the game|\b\w+\b joined the game"
        )
        FileChangesUtillity.__init__(self, self.log_path)

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
        if self._chat_message_pattern not in message:
            return ""
        chat_message = message.split(self._chat_message_pattern)[-1]

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
