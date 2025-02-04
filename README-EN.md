<div align="center">

![TelegramChat](https://socialify.git.ci/SALTWOOD/TelegramChat/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

# TelegramChat
✨🎉 **An Extensible Telegram Bot Plugin Powered by python-telegram-bot!** 🎉✨
</div>

> [!WARNING]  
> Due to f**king Tencent's issues, the entire plugin is now being developed for Telegram. QQ-based versions will no longer be supported.
> The plugin wrote for SaltyQQChat can still be used; simply modify a little of the codes.

# Introduction
This is a Telegram bot plugin based on [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).

Additionally, it supports simple bot extension through **API calls**, allowing you to add your own custom commands!

**Features we have:**
- [x] Supports ignoring commands from specific users via `/ban` and `/pardon`
- [x] Allows the bot to execute more Minecraft native commands without using `/command` (such as `/ban`, `/pardon`)
- [x] Allows starting and stopping the server through the bot
- [x] Supports replying when the bot is mentioned, instead of just responding to a command
- [x] Supports executing bot commands within Minecraft
- [x] Check bot status via `/ping` and `/info` commands
- [x] **[Development Feature]** Remote plugin reload via `/reload`
- [x] Customizable one-way/two-way MC <==> Telegram group forwarding
- [x] Easily extendable command tree based on regular expressions
- [x] Automatically handle group join requests, friend requests, and group invitations.
- [x] Verify if the Minecraft player exists when binding to a player.
- [x] Spacing added between Chinese, numbers, and English, with a more humorous tone in the responses

**Features we don't have:**
- [x] No "management group", "main group", or "message sync group" functionality. Instead, it uses multi-group synchronization (though typically, only one group is used)
- [x] No "MultiServer" feature, as it leads to unpredictable bugs and has limited use

# Installation
## Install via MCDR
Use `!!MCDR plugin install telegram_chat` in the MCDR console, then `!!MCDR confirm`.

## Install via Release
Download the corresponding `.mcdr` file from the [Releases page](https://github.com/SALTWOOD/TelegramChat/releases) and place it in the `plugins` folder, then reload the plugin.

## Install via Source Code
Run `git clone https://github.com/SALTWOOD/TelegramChat` or `git clone git@github.com:SALTWOOD/TelegramChat` in the `plugins` folder, then reload the plugin.

# API
One of the most interesting features of this plugin is that you can extend it by adding custom commands via other MCDR plugins. Here's an example of a single-file plugin:

```Python
from mcdreforged.api.types import PluginServerInterface
from typing import Callable, List
import re

reply: Callable
PLUGIN_METADATA = {
    'id': 'tc_extension',
    'version': '1.0.0',
    'name': 'TC extension plugin',
    'description': 'TelegramChat\'s extension plugin',
    'author': 'NONE',
    'link': 'https://github.com',
    'dependencies': {
        'telegram_chat': '>=1.0.0'
    }
}

def on_load(server: PluginServerInterface, old):
    global reply
    sqc = server.get_plugin_instance("telegram_chat")

    reply = sqc.reply

    sqc.commands.add_command(re.compile(r'/your-command (.*)'), [str], handler)

def handler(server: PluginServerInterface, event, command: List[str],
            event_type):
    message = command[0]
    reply(
        event,
        f"You provided the parameter: \"{message}\""
    )
```

# Special Thanks
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Provides a way to access Telegram.
- **SALTWO∅D server members** - For helping me test the bot and discovering security vulnerabilities before the release