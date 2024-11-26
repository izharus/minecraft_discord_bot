"""
This module implements a classes for sending commands
into the console of minecraft server.
"""
import asyncio
import subprocess
from abc import abstractmethod
from typing import Optional

import aiomcrcon
from loguru import logger as log


class RCONSendCmdError(RuntimeError):
    """Raises if any error occurs due sending of cmd command."""


class RconBase:
    """Base class for RCON communication."""

    @abstractmethod
    def send_command(
        self,
        rcon_command: str,
        command_args: Optional[str] = None,
    ) -> Optional[str]:
        """Send an RCON command.

        Args:
            rcon_command (str): The RCON command to be executed.
            command_args (str): Additional arguments for the RCON command.

        Returns:
            str: The result text of the RCON command.
        """

    def send_say_command(self, message: str) -> None:
        """
        Send a /say command into rcon.
        This command will print a message for the all users.
        """
        self.send_command("/say", f'"{message}"')


class RconLocalDocker(RconBase):
    """Send an RCON command to a local Docker instance."""

    def __init__(self, container_name: str):
        """Initialize RconLocalDocker instance.

        Args:
            container_name (str): Name of the Docker container.
        """
        RconBase.__init__(self)
        self._docker_rcon_command = f"docker exec {container_name} rcon-cli"

    def send_command(
        self,
        rcon_command: str,
        command_args: Optional[str] = None,
    ) -> Optional[str]:
        """Send an RCON command to the local Docker instance.

        Args:
            rcon_command (str): The RCON command to be executed.
            command_args (str): Additional arguments for the RCON command.

        Returns:
            str or None: The result text of the RCON command,
                or None if an error occurs.

        Raises:
            subprocess.CalledProcessError: If the subprocess call
                returns a non-zero exit code.
        """
        try:
            if not command_args:
                command_args = ""
            result = subprocess.run(
                f"{self._docker_rcon_command} {rcon_command} {command_args}",
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as error:
            log.error(f"Failed to send command: {error.stderr}")
            return None


class AIOMcRcon(aiomcrcon.Client):
    """
    A subclass of `aiomcrcon.Client` that adds automatic reconnection logic
    and improved error handling
    """

    def __init__(
        self, host: str, port: int, password: str, reconnect_interval: int = 10
    ):
        """
        Initializes the AIOMcRcon client with the specified host, port,
        and password.

        Args:
            host (str): The host address of the RCON server.
            port (int): The port number of the RCON server.
            password (str): The password to authenticate with the RCON server.
            reconnect_interval (int, optional): The time interval (in seconds)
                to wait before retrying a failed connection.
        """
        super().__init__(host, port, password)
        self.reconnect_interval = reconnect_interval

    async def connect(self, *args, **kwargs):
        while not self._ready:
            try:
                await super().connect(*args, **kwargs)
                log.debug(
                    f"Rcon connection success to to: {self.host}:{self.port}"
                )
                return
            except aiomcrcon.errors.RCONConnectionError as error:
                log.warning(f"Rcon connection failed: {error}")
                await asyncio.sleep(self.reconnect_interval)

    async def send_cmd(self, *args, **kwargs):
        try:
            return await super().send_cmd(*args, **kwargs)
        except Exception as error:
            log.debug(f"Failed to send_cmd command: {error}")
            if self._ready:
                await self.close()
                asyncio.create_task(self.connect())
            raise RCONSendCmdError(
                f"Failed to send cmd command: {error}"
            ) from error


if __name__ == "__main__":
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    # rcon.send_say_command("/list")
    # print(rcon.send_command("/list"))
