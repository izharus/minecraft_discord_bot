"""A module for custom exceptipons."""


class LogFileNotExists(RuntimeError):
    """Raises if minecraft log file not found."""

    def __init__(self, message: str = "Log file not found."):
        super().__init__(message)
