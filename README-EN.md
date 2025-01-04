<div align="center">

![SaltyQQChat](https://socialify.git.ci/SALTWOOD/SaltyQQChat/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

# SaltyQQChat
✨🎉 **An extensible QQ bot plugin based on QQAPI!** 🎉✨
</div>

# Introduction
This is a QQ bot plugin based on [QQAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_api), which can be considered a rewrite of [QQChat](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_chat), with many unnecessary features removed and the code structure optimized.

At the same time, it supports extending the bot simply through the **API** to add your own commands!

Compared to QQChat, the following new features have been added:
- [x] Supports rejecting responses from certain users via `/bot-ban` and `/bot-pardon`
- [x] Supports executing more native commands without using `/command` (such as `/ban`, `/pardon`)
- [x] Supports starting and stopping the server through the bot
- [x] Supports replying when the bot is mentioned, instead of just responding to a command
- [x] Supports executing QQ bot commands within Minecraft
- [x] Check the bot's status via `/ping` and `/info` commands
- [x] **[Development Feature]** Reload the plugin remotely via `/reload`
- [x] Customizable one-way/two-way MC <==> QQ group forwarding
- [x] Easily extendable command tree based on regular expressions

Meanwhile, the following features have been removed or modified:
- [x] No "management group", "main group", or "message sync group" functionality, replaced with multi-group synchronization (though usually only one group is used)
- [x] No "MultiServer" feature, as it can lead to unpredictable bugs and has limited use
- [x] Permission restrictions have been added to the `!!qq` command to prevent misuse, as CQ codes are not escaped, which could result in the bot account being used to send inappropriate content
- [x] Added spacing between Chinese, numbers, and English, and a more humorous tone in the messages

# Installation
## Install via MCDR
In the MCDR console, use `!!MCDR plugin install salty_qq_chat`, then `!!MCDR confirm`.

## Install via Release
Download the corresponding `.mcdr` file from the [Releases page](https://github.com/SALTWOOD/SaltyQQChat/releases) and place it in the `plugins` folder, then reload.

## Install via Source Code
Run `git clone https://github.com/SALTWOOD/SaltyQQChat` or `git clone git@github.com:SALTWOOD/SaltyQQChat` in the `plugins` directory, then reload the plugin.

# API
This is one of the most interesting features of the plugin. You can add custom commands to the plugin by integrating other MCDR plugins.
Here is an example of a single-file plugin:

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
