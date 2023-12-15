"""
This module implements a classes for sending commands
into the console of minecraft server.
"""
import subprocess
from abc import abstractmethod
from typing import Optional


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
        except subprocess.CalledProcessError:
            return None


if __name__ == "__main__":
    rcon = RconLocalDocker("minecraft_server_tfc_halloween")
    # rcon.send_say_command("/list")
    # print(rcon.send_command("/list"))
