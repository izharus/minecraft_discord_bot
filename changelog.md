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

# Version 1.1.0 - April 04, 2024

## Changes:
- Added support for 1.19.2 minecraft servers
## Fixes:
- Bot now handles correctly server_started_pattern in servers log without voice chat mode.