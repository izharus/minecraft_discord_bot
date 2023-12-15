"""
Main entry point.
version 1.0.0
"""
from loguru import logger
from src.discord_bot.bot_main import main

# Configure logging to create a new log file each month
# without deleting old ones
logger.add(
    "logs/file_{time:YYYY-MM}.log",
    rotation="1 month",
    retention="1 month",  # Retain log files for 1 month after rotation
    compression="zip",  # Optional: Enable compression for rotated logs
    level="DEBUG",
    serialize=False,
)
main()
