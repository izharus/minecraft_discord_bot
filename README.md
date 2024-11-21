# Minecraft Discord Bot

Python 3.11 and Windows 10/11 are required for this project.

## Installation

```bash
git clone https://github.com/izharus/halloween_web_server.git
cd halloween_web_server
python -m venv dev_venv
.\dev_venv\Scripts\activate
python -m pip install -r requirements/dev.txt
pre-commit install
```

## To compile new requirements, use pip-compile.
```bash
.\dev_venv\Scripts\activate
pip-compile requirements/dev.in

```
Edit the config.ini file and set the following variables
CHANNEL_ID - Discord channel ID
DISCORD_ACCESS_TOKEN - Discord access token
CONTAINER_NAME - Docker container name with minecraft server

Forward the root directory of the Minecraft server:
/path/to/your/server:/app/minecraft-root-dir:ro 



## Docker Container
To create a Docker container on Windows:
```bash
docker build -t discord-bot:1.3.1 .
docker save -o discord.tar discord-bot:1.3.1
docker run -d -v E:/MAIN/source/repos/Retsam/minecraft_discord_bot/data:/app/data -v F:/minecraft_servers/server_dac/itzg/minecraft-server:/app/minecraft-root-dir:ro --name halloween-discord-bot halloween-discord-bot-image:1.3.1
```

## Args

- --debug: Execute the script in debug mode. If --debug passed, bot will try to get minecraft server latest log file from MINECRAFT_SERVER_PATH, otherwise, it will try to find minecraft server latest log in minecraft-server dir (it's need for docker).