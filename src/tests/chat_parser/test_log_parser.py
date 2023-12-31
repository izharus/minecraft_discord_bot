"""Tests for src/chat_parser/log_parser.py."""
# pylint: disable=W0212
import threading
import time
from typing import List

import pytest
from src.chat_parser import log_parser


def add_text(file_path: str, text: str, mode: str = "a") -> None:
    """Add text into file."""
    with open(file_path, mode, encoding="utf-8") as fw:
        fw.write(text)

    # wait until system update file information
    time.sleep(0.1)


class TestFileChangesUtility:
    """Tests for FileChangesUtillity."""

    def test_log_file_not_exists_error(self):
        """
        Attempt for creating a FileChangesUtillity
        instance with incorrect log file path.
        """
        non_existing_file = "non_existing_file"
        with pytest.raises(log_parser.LogFileNotExists):
            log_parser.FileChangesUtillity(non_existing_file)

    def test_with_existing_log_file(self, tmp_path):
        """
        Attempt for creating a FileChangesUtillity
        instance with an existing log file path.
        """
        # Create a temporary text file
        temp_file = tmp_path / "temp_file.txt"
        # Write some content to the file
        content = "Hello, this is a test content."
        temp_file.write_text(content)
        log_parser.FileChangesUtillity(temp_file)

    def test_is_file_modified_modify_file(self, tmp_path):
        """
        Check if is_file_modified() recognises file
        modifications.
        """
        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)

        assert manager.is_file_modified() is False

        add_text(temp_file, "New content!")

        assert manager.is_file_modified() is True

    def test_is_file_modified_rotate_file(self, tmp_path):
        """
        Check if is_file_modified() recognises if file
        was rotated.
        """
        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)

        assert manager.is_file_modified() is False
        assert manager._last_position != 0

        add_text(temp_file, "", mode="w")

        assert manager.is_file_modified() is True
        assert manager._last_position == 0

    def test__get_new_lines(self, tmp_path):
        """
        Test _get_new_lines() function.
        """
        file_content = [f"string{i}\n" for i in range(0, 1000)]
        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)
        add_text(temp_file, "".join(file_content))
        new_lines = list(manager._get_new_lines())
        assert len(new_lines) == len(file_content)
        assert new_lines == file_content

    def set_last_position(self, tmp_path):
        """
        Test set_last_position() function.
        """
        file_content = [f"string{i}\n" for i in range(0, 1000)]
        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)
        add_text(temp_file, "".join(file_content))
        new_lines_1 = list(manager._get_new_lines())
        manager.set_last_position()
        new_lines_2 = list(manager._get_new_lines())
        assert len(new_lines_1) == len(file_content) == len(new_lines_2)
        assert new_lines_1 == file_content == new_lines_2

    def test__get_new_lines_concurrent(self, tmp_path):
        """
        Test _get_new_lines() function with concurrent writes from another
        thread.
        """

        def write_lines_thread(
            temp_file_path: str,
            content_strings: List[str],
        ) -> None:
            for line in content_strings:
                add_text(temp_file_path, line)
                time.sleep(0.01)

        # Generate file content
        file_content = [f"string{i}\n" for i in range(0, 10)]

        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)

        # Start a thread to write lines to the file concurrently
        write_thread = threading.Thread(
            target=write_lines_thread,
            args=(temp_file, file_content),
        )
        write_thread.start()

        new_lines = []
        stop = False
        while not stop:
            if not write_thread.is_alive():
                stop = True
            new_parsed_lines = list(manager._get_new_lines())
            if new_parsed_lines:
                new_lines.extend(new_parsed_lines)

        assert len(new_lines) == len(file_content)
        assert new_lines == file_content

    def test_get_new_line_concurrent(self, tmp_path):
        """
        Test get_new_line() function with concurrent writes from another
        thread.
        """

        def write_lines_thread(
            temp_file_path: str,
            content_strings: List[str],
        ) -> None:
            for line in content_strings:
                add_text(temp_file_path, line)
                time.sleep(0.01)

        # Generate file content
        file_content = [f"string{i}\n" for i in range(0, 10)]

        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Default content.")

        manager = log_parser.FileChangesUtillity(temp_file)

        # Start a thread to write lines to the file concurrently
        write_thread = threading.Thread(
            target=write_lines_thread,
            args=(temp_file, file_content),
        )
        write_thread.start()

        new_lines = []
        stop = False
        while not stop:
            if not write_thread.is_alive():
                stop = True
            new_parsed_line = manager.get_new_line()
            if new_parsed_line:
                new_lines.append(new_parsed_line)

        assert len(new_lines) == len(file_content)
        assert new_lines == file_content

    def test_get_new_line_rotate_file(self, tmp_path):
        """doc string"""
        temp_file = tmp_path / "temp_file.txt"
        add_text(temp_file, "Line_0\n")
        manager = log_parser.FileChangesUtillity(temp_file)
        add_text(temp_file, "Line_1\n")
        add_text(temp_file, "Line_2\n")

        assert manager.get_new_line() == "Line_1\n"
        assert manager.get_new_line() == "Line_2\n"
        add_text(temp_file, "Line_3\n", mode="w")
        add_text(temp_file, "Line_4\n")
        assert manager.get_new_line() == "Line_3\n"
        assert manager.get_new_line() == "Line_4\n"
