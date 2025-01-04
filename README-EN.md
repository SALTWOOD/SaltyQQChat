<div align="center">

![SaltyQQChat](https://socialify.git.ci/SALTWOOD/SaltyQQChat/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

# SaltyQQChat
✨🎉 **An Extensible QQ Bot Plugin Powered by QQAPI!** 🎉✨
</div>

# Introduction
This is a QQ bot plugin based on [QQAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_api), essentially a reworked version of [QQChat](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_chat). It removes many features that I consider unnecessary and optimizes the code structure.

Additionally, it supports simple bot extension through **API calls**, allowing you to add your own custom commands!

**New features compared to QQChat include:**
- [x] Supports ignoring commands from specific users via `/bot-ban` and `/bot-pardon`
- [x] Allows the bot to execute more Minecraft native commands without using `/command` (such as `/ban`, `/pardon`)
- [x] Allows starting and stopping the server through the bot
- [x] Supports replying when the bot is mentioned, instead of just responding to a command
- [x] Supports executing QQ bot commands within Minecraft
- [x] Check bot status via `/ping` and `/info` commands
- [x] **[Development Feature]** Remote plugin reload via `/reload`
- [x] Customizable one-way/two-way MC <==> QQ group forwarding
- [x] Easily extendable command tree based on regular expressions

**Removed or modified features:**
- [x] No "management group", "main group", or "message sync group" functionality. Instead, it uses multi-group synchronization (though typically, only one group is used)
- [x] No "MultiServer" feature, as it leads to unpredictable bugs and has limited use
- [x] Permissions are added to the `!!qq` command to prevent misuse, as CQ codes are not escaped, potentially allowing the bot account to send inappropriate content
- [x] Spacing added between Chinese, numbers, and English, with a more humorous tone in the responses

# Installation
## Install via MCDR
Use `!!MCDR plugin install salty_qq_chat` in the MCDR console, then `!!MCDR confirm`.

## Install via Release
Download the corresponding `.mcdr` file from the [Releases page](https://github.com/SALTWOOD/SaltyQQChat/releases) and place it in the `plugins` folder, then reload the plugin.

## Install via Source Code
Run `git clone https://github.com/SALTWOOD/SaltyQQChat` or `git clone git@github.com:SALTWOOD/SaltyQQChat` in the `plugins` folder, then reload the plugin.

# API
One of the most interesting features of this plugin is that you can extend it by adding custom commands via other MCDR plugins. Here's an example of a single-file plugin:

```Python
from mcdreforged.api.types import PluginServerInterface
from typing import Callable, List
import re

reply: Callable
PLUGIN_METADATA = {
    'id': 'sqc_extension',
    'version': '1.0.0',
    'name': 'SQC extension plugin',
    'description': 'SaltyQQChat\'s extension plugin',
    'author': 'NONE',
    'link': 'https://github.com',
    'dependencies': {
        'salty_qq_chat': '>=1.0.0'
    }
}

def on_load(server: PluginServerInterface, old):
    global reply
    sqc = server.get_plugin_instance("salty_qq_chat")
    qqapi = server.get_plugin_instance("qq_api")

    reply = sqc.reply

    sqc.commands.add_command(re.compile(r'/your-command (.*)'), [str], handler)

def handler(server: PluginServerInterface, event, command: List[str],
            event_type):
    message = command[0]
    reply(
        event,
        f"[CQ:at,qq={event.user_id}] You provided the parameter: \"{message}\""
    )
```

# Special Thanks
- [QQAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_api) - Provides a WebSocket interface to CQHttp
- [AnzhiZhang](https://github.com/AnzhiZhang) - Special thanks for providing LGPL license, although I used GPL (lol)
- **SALTWO∅D server members** - For helping me test the bot and discovering security vulnerabilities before the release

# Random Thoughts
- This project is not just a direct copy of QQChat. It's just that the only available API that fits my environment is QQAPI, and QQChat is the only downstream implementation of this API, so some parts inevitably resemble it.
