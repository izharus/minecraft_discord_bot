# Minecraft Discord Bot

## Introduction
This bot acts as a simple proxy between the Minecraft server's log file (latest.log) and a Discord channel. It forwards messages from players in the game to Discord and vice versa, allowing for seamless communication between Minecraft and Discord.

## Why use this bot if there are mods and plugins
This bot eliminates the need for mods or plugins, as it works on both Forge servers and those that only support plugins. It interacts with the Minecraft server through the log file to parse game messages and uses RCON to send messages to the server. The bot should be run on the same machine as the Minecraft server for optimal performance.

## Installation

### Requirements
Python 3.11 required for this project.

### Setup
```bash
git clone https://github.com/izharus/minecraft_discord_bot.git
cd minecraft_discord_bot
python -m venv dev_venv
.\dev_venv\Scripts\activate
python -m pip install -r requirements/dev.txt
pre-commit install
```

### To compile new requirements, use pip-compile.
```bash
.\dev_venv\Scripts\activate
pip-compile requirements/dev.in
```

## Configuration


### Edit the `config.ini` File
Set the following variables in the `config.ini` file:
- `CHANNEL_ID`: Discord channel ID where messages will be sent.
- `DISCORD_ACCESS_TOKEN`: Your Discord bot access token.
- `rcon_host`: Ip of your mc server.
- `rcon_port`: RCON port of your mc-server
- `rcon_secret`: RCON password of your mc-server.

### Discord Bot Message Patterns
The Discord bot expects the following patterns in your server `run.sh` script:
- '"^.*\[Rcon\] SERVER STOPPED\.\.\.$"' - '[Rcon] SERVER STOPPED...'
- '^.*\[Rcon\] SERVER STARTED!!!$' - [Rcon] SERVER STARTED!!!



## Docker Container
To create a Docker container on Windows:
```bash
docker build -t discord-bot:1.3.1 .
docker save -o discord.tar discord-bot:1.3.1
```
