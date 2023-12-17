"""This modules provides class for extracting a new strings from log files."""
import logging
import os
import time
from typing import Generator

from .custom_exceptions import LogFileNotExists


class FileChangesUtillity:
    """
    A utility class for monitoring and reading changes from a file.

    This class provides methods to check if a file has been modified since the
    last check, and to read new lines from the file while maintaining the last
    read position. It is useful for monitoring log files or other continuously
    updated files.

    Args:
        filename (str): The path to the file to be monitored and read.

    Attributes:
        filename (str): The path to the monitored file.
        _cached_stamp (float): The cached last modification timestamp of the
            file.
        _last_position (int): The last position in the file that was read.
        _iterator (iterator): Iterator for continuous reading of the file.

    Methods:
        is_file_modified(): Checks if the file has been modified since the
            last check.
        get_new_lines(): Generator function to read and yield new lines from
            the file.
    Raises:
        LogFileNotExists: is log file not exists.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self._cached_stamp: float = 0
        try:
            self._last_position = os.path.getsize(self.filename)
        except FileNotFoundError as error:
            raise LogFileNotExists() from error
        self.is_file_modified()
        self._iterator = iter(self._get_new_lines())

    def is_file_modified(self) -> bool:
        """Checks if the file has been modified since the last check.

        This method compares the last modification timestamp of the file with
        a cached timestamp to determine if the file has been modified. If the
        file is found to be modified, it updates the cached timestamp and
        checks if the file size has decreased, resetting the read position if
        necessary.

        Returns:
            bool: True if the file has been modified, False otherwise.
        """
        try:
            stamp = os.stat(self.filename).st_mtime
            if stamp != self._cached_stamp:
                self._cached_stamp = stamp
                if os.path.getsize(self.filename) < self._last_position:
                    self._last_position = 0
                return True
            return False
        except Exception as error:
            logging.error(
                f"is_file_modified() function failed with error: {error}"
            )
            return False

    def _get_new_lines(self) -> Generator[str, None, None]:
        """
        Generator function to read and yield new lines from a file.

        This function reads lines from the specified file, starting from the
        last position read, and yields each line as it's read. It updates the
        last position after each read to remember where it left off.

        Returns:
            str: The next line from the file.
        """
        try:
            if self.is_file_modified():
                with open(self.filename, encoding="utf-8") as file:
                    file.seek(self._last_position)
                    while line := file.readline():
                        yield line
                    self._last_position = file.tell()
        except Exception as error:
            logging.error(f"Error reading log lines: {str(error)}")

    def get_new_line(self) -> str:
        """
        Read and return the next line from the file.

        Returns:
            str: a new line in the file, or an empty string.
        """
        try:
            return next(self._iterator)
        except StopIteration:
            self._iterator = iter(self._get_new_lines())
            try:
                return next(self._iterator)
            except StopIteration:
                return ""

    def set_last_position(self, new_position: int = 0) -> None:
        """
        Sets the last position in the monitored file to the specified
        new position.

        Args:
            new_position (int): The new position to set as the last read
                position. Defaults to 0, indicating the beginning of the file.
        """
        self._last_position = new_position

    def reset_file_modified_timestamp(self) -> None:
        """
        Reset the modified timestamp of the file to force recalculation.
        """
        self._cached_stamp = 0


def main() -> None:
    """Example usage."""
    # pylint: disable = C0301
    filename = "F:\\minecraft_servers\\server_tfc_halloween\\itzg\\minecraft-server\\logs\\latest.log"
    # filename = 'F:\\server_imperial\\itzg\\minecraft-server\\logs\\test.txt'
    observer = FileChangesUtillity(filename)
    while 1:
        time.sleep(1)
        print(observer.get_new_line(), end="")  # noqa: T201
