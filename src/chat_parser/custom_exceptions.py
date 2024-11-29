"""A module for custom exceptipons."""


class LogFileNotExists(RuntimeError):
    """Raises if minecraft log file not found."""

    def __init__(self, message: str = "Log file not found."):
        super().__init__(message)


class ServerStopped(Exception):
    """Raises when server stopped"""

    def __str__(self):
        return "# Сервер остановлен."


class ServerStarted(Exception):
    """Raises when server started"""

    def __str__(self):
        return "# Сервер запущен."
