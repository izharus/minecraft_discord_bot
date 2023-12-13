"""This modules provides class for extracting a new strings from log files."""
import logging
import os
import threading
import time
from collections import deque
from typing import Callable, Generator

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

    Methods:
        is_file_modified(): Checks if the file has been modified since the
            last check.
        get_new_lines(): Generator function to read and yield new lines from
            the file.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self._cached_stamp: float = 0
        try:
            self._last_position = os.path.getsize(self.filename)
        except FileNotFoundError as error:
            raise LogFileNotExists() from error
        self.is_file_modified()

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
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            if os.path.getsize(self.filename) < self._last_position:
                self._last_position = 0
            return True
        return False

    def get_new_lines(self) -> Generator[str, None, None]:
        """
        Generator function to read and yield new lines from a file.

        This function reads lines from the specified file, starting from the
        last position read, and yields each line as it's read. It updates the
        last position after each read to remember where it left off.

        Returns:
            str: The next line from the file.

        Raises:
            Exception: If there is an error while reading the file, an error
                message is logged using the logging module.
        """
        try:
            with open(self.filename, encoding="utf-8") as file:
                file.seek(self._last_position)
                while line := file.readline():
                    yield line
                self._last_position = file.tell()
        except Exception as error:
            logging.error(f"Error reading log lines: {str(error)}")


class FileChangesHandler(FileChangesUtillity):
    """
    A class that extends FileChangesUtility to handle file changes and provide
    additional functionality for logging and retrieving lines.

    This class inherits the capability to monitor and read changes from a file
    using the FileChangesUtility class. It extends the functionality by
    providing the ability to log lines, maintain a line buffer, and retrieve
    lines from the buffer.

    Args:
        filename (str): The path to the file to be monitored and read.

    Attributes:
        _worker_thread (threading.Thread): A thread used for asynchronous file
            observation.
        _line_buffer (collections.deque): A double-ended queue used to store
            lines read from the file.
        _max_buffer_len (int): max len of buffer for storing file changes.
        _observing_delay (int)L delay in secodns between besrve iterations.
    Methods:
        _save_new_lines(): Internal method to save and log new lines from the
            file.
        file_observer(is_working: Callable[[], bool]): Continuously observes
            the file for changes and saves new lines.
        get_new_line(): Retrieve the next line from the line buffer.
    """

    def __init__(
        self,
        filename: str,
        max_buffer_len: int = 1000,
        observing_delay: int = 1,
    ) -> None:
        super().__init__(filename)
        self._worker_thread: threading.Thread
        self._line_buffer: deque = deque()
        self._max_buffer_len: int = max_buffer_len
        self._observing_delay = observing_delay

    def _save_new_lines(self) -> None:
        """Save and log new lines from a file.

        Note:
            The `get_new_lines` method is used internally to obtain new lines.

        """
        for line in self.get_new_lines():
            logging.info(line)
            self._line_buffer.append(line)

    def file_observer(self, is_working: Callable[[], bool]):
        """
        Continuously observes a file for changes and saves new lines.

        Args:
            is_working (Callable[[], bool]): A callable function that
                returns True as long as the observation should continue,
                and False to stop it.

        Notes:
            This function runs in a loop, periodically checking for changes in
            the observed file. It sleeps for one second between iterations to
            avoid unnecessary resource consumption. If the line buffer exceeds
            the maximum allowed length, a warning message is logged,
            and the observation continues. Upon detecting file modifications,
            new lines are saved.

        Returns:
            None

        """
        while is_working():
            time.sleep(self._observing_delay)
            if self._max_buffer_len < len(self._line_buffer):
                logging.warning("Buffer is overloaded.")
                continue
            if self.is_file_modified():
                self._save_new_lines()

    def get_new_line(self) -> str:
        """Retrieve the next line from the line buffer.

        Returns the next line from the line buffer if it is not empty. If the
        buffer is empty, a message is printed, and an empty string is returned.

        Returns:
            str: The next line from the line buffer, or an empty string if the
                buffer is empty.
        """
        if self._line_buffer:
            return self._line_buffer.popleft()
        else:
            # print("buffer is empty")
            return ""


class FileCnageObserver(FileChangesHandler):
    """
    A class that extends FileChangesHandler to provide the ability to start and
    stop observing a file for changes using a separate thread.

    Args:
        file_name (str): The path to the file to be monitored and read.

    Attributes:
        is_working (bool): A boolean flag that indicates whether the
            observation is currently active.

    Methods:
        start(): Start the file observation in a separate thread.
        stop(): Stop the file observation.

    """

    def __init__(self, file_name) -> None:
        super().__init__(file_name)
        self.is_working: bool = False

    def __del__(self) -> None:
        self.stop()

    def start(self) -> None:
        """
        Start the file observation in a separate thread.

        This method sets the `is_working` flag to True and creates a new thread
        that runs the `file_observer` method from the parent class. The thread
        is set as a daemon to exit when the main program exits.

        """
        self.is_working = True
        self._worker_thread = threading.Thread(
            target=self.file_observer, args=[lambda: self.is_working]
        )
        # Make the thread a daemon so it exits when the main program exits
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def stop(self) -> None:
        """
        Stop the file observation.

        This method sets the `is_working` flag to False, which signals the file
        observation to stop. It should be called to gracefully stop the
        observation before the program exits.

        """
        self.is_working = False


def main() -> None:
    """Example usage."""
    # pylint: disable = C0301
    filename = "F:\\minecraft_servers\\server_tfc_halloween\\itzg\\minecraft-server\\logs\\latest.log"
    # filename = 'F:\\server_imperial\\itzg\\minecraft-server\\logs\\test.txt'
    observer = FileCnageObserver(filename)
    observer.start()
    while 1:
        time.sleep(1)
        print(observer.get_new_line(), end="")  # noqa: T201


# main()
