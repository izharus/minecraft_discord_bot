"""Tests for src/log_parser/parser.py."""

import pytest
from src.log_parser import parser


def test_log_file_not_exists_error():
    """
    Attempt for creating a FileChangesUtillity
    instance with incoorect log file path.
    """
    non_existing_file = "non_existing_file"
    with pytest.raises(parser.LogFileNotExists):
        parser.FileChangesUtillity(non_existing_file)
