"""Pytest conftest module."""
from pathlib import Path

import pytest
from src.chat_parser.chat_parser import VanishHandlerMasterPerki


@pytest.fixture
def vanish_handler(tmp_path: Path) -> VanishHandlerMasterPerki:
    """
    Return a VanishHandlerMasterPerki instance with
    an empty vanished players list.
    """
    return VanishHandlerMasterPerki(tmp_path / "vanished_players.json")
