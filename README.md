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

## Access Configuration
Edit the access.py file and set the following variables:
```python
CHANNEL_ID = YOUR_CHANGE_ID  # Replace with your Discord channel ID
DISCORD_ACCESS_TOKEN = YOUR_ACCESS_TOKEN  # Replace with your Discord access token
MINECRAFT_SERVER_PATH = PATH # Path to minecraft server dir
```

## Docker Container
To create a Docker container on Windows:
```bash
docker build -t halloween-discord-bot-image:version_1.1.0 .
docker run -d -v F:/minecraft_servers/server_dac/itzg/minecraft-server:/app/minecraft-server -v F:/minecraft_servers/discord_tfc_bot/logs:/app/logs -v "//var/run/docker.sock:/var/run/docker.sock" --name halloween-discord-bot halloween-discord-bot-image:version_1.1.0
```
Command structure:
```bash
docker run -d -v minecraft_server_root_dir_path:/app/minecraft-server -v your_custom_path_to_bot_logs_dir:/app/logs -v "//var/run/docker.sock:/var/run/docker.sock" --name halloween-discord-bot halloween-discord-bot-image:version_1.1.0
```

## Args

- --debug: Execute the script in debug mode. If --debug passed, bot will try to get minecraft server latest log file from MINECRAFT_SERVER_PATH, otherwise, it will try to find minecraft server latest log in minecraft-server dir (it's need for docker).