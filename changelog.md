# Version 1.0.1 - December 16, 2023

## Changes:
- Added a ping method to prevent bot shutdown.

# Version 1.0.4 - December 16, 2023

## Changes:
- Added messages for server status information(started, stopped, starting).
- All messages between "stopped" - "starting" and "starting - "started" will be ignored.

# Version 1.0.5 - December 31, 2023

## Changes:
- The send_heartbeat function was removed as it was unused. Furthermore, the stop method was never called for the send_heartbeat task. This could have led to duplicate messages in the Discord on December 31, 2023.


# Version 1.0.6 - 2024
## Fixes:
- All unexpected exceptions should be rerised, it's a bad practice to catch wide exception. (rerise=True param was passed into logger.catch). Maybe, catching wide exceptions in on_ready may led to duplicate messages in the Discord on December 31, 2023.

# Version 1.1.0 - April 04, 2024

## Changes:
- Added support for 1.19.2 minecraft servers
## Fixes:
- Bot now handles correctly server_started_pattern in servers log without voice chat mode.

# Version 1.1.1 - May 18, 2024
## Fixes:
- Stop sending messages like "world saved" into discord channel.
# Version 1.3.0 - Nov 05, 2024
## Changes:
- Added config.ini

# Version 1.3.1 - Nov 21, 2024
- Deleted an infinite loop in on_ready method.

# Version 1.4.0 - Nov 21, 2024
### Features
- Added `/tps` command for real-time server performance monitoring.  
- Implemented "hello" messages from the bot.  
- Integrated `aiomcrcon` into the bot for seamless server communication.  
- Added a vanish mod handler to process player visibility.  

### Fixes
- Improved handling of server start and stop messages.  
- Fixed username extraction logic for better chat parsing.  
- Updated Dockerfile to use a slim Python image.  
- Restructured test data directories for better organization.  

# Version 1.4.1 - Nov 21, 2024
### Fixes
- Close method was not called.
- Duplicates in logs if mc-server connection failed.

# Version 1.5.0 - Nov 29, 2024
### Features
- Auto reconnect mc-rcon if server was restarted (ML-40).

