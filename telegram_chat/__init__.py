import re
from typing import List, Dict, Any, Callable
from asyncio import AbstractEventLoop

from mcdreforged.api.command import *
from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import PluginServerInterface, CommandSource, Info
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.event import LiteralEvent
from enum import Enum, unique

from telegram import Update
from telegram.ext import Application, ContextTypes, ExtBot

import requests
import time
from .command_builder import CommandBuilder
from .info import get_system_info
from .version import *
from .telegram import TelegramBot

# 变量声明
bot: TelegramBot

bindings: dict[str, str]

commands: CommandBuilder

class Config(Serializable):
    groups: List[int] = []

    admins: List[str] = []

    whitelist: Dict[str, Any] = {
        "add_when_bind": True,
        "remove_when_leave_group": True,
        "commands": {
            "add": "whitelist add {}",
            "remove": "whitelist remove {}"
        },
        "verify_player": True,
    }

    commands: Dict[str, bool] = {
        "bind": True,
        "command": True,
        "info": True,
        "list": True,
        "mc": True,
        "mcdr": False,
        "qq": True,
        "whitelist": True,
    }

    forwardings: Dict[str, bool] = {
        "tg_to_mc": True,
        "mc_to_tg": False,
    }
    
    telegram: Dict[str, Any] = {
        "token": None,
        "api": None
    }
    
    need_at: bool = True

config: Config
ban_list: List[int]

class MessageType(Enum):
    USER = 0
    ADMIN = 1

class Help():
    basic = """命令列表：
- /list 获取在线玩家列表
- /bind <ID> 绑定当前 Telegram 账号到 Minecraft 账号
- /mc <message> 向 Minecraft 内发送聊天信息
- /ping 查询在线状态并且计算延迟"""
    
    user = f"""TelegramChat Ver.{VERSION_STR}

{basic}
"""

    admin = f"""TelegramChat Ver.{VERSION_STR}

{basic}

管理命令列表：
- /bind 玩家绑定信息相关操作，使用 /bind 获取详细帮助
- /command 向 Minecraft 服务器发送命令
- /mc <message> 向 Minecraft 内发送聊天信息
- /mcdr <command> 向 MCDR 进程发送命令
- /whitelist <add|remove> <玩家名> 管理白名单，使用 /whitelist 获取详细帮助
- /start /stop /restart 启动、关闭、重启服务器
- /info 仅私聊，获取系统信息
- /reload 重载 Bot
- /ban 封禁某人（游戏内）
- /pardon 解除对某人的封禁（游戏内）
- /bot-ban 不允许某人使用 Bot
- /bot-pardon 不再禁止某人使用 Bot
"""

    bind = """/bind <ID> 绑定当前 Telegram 账号到 Minecraft 账号
/bind <TG> <ID> 绑定 Telegram 账号到 Minecraft 账号
/bind unbind <TG> 解除 Telegram 账号与 Minecraft 账号的绑定关系
/bind query "TG"|"ID" <TG|ID> 查询 Telegram 账号或 Minecraft 账号的绑定关系
"""

    whitelist = """/whitelist <add|remove> <玩家名> 管理白名单
/whitelist list 显示白名单列表
/whitelist reload 重新加载白名单配置文件
/whitelist off 关闭白名单功能
/whitelist on 开启白名单功能
/whitelist add <ID> 添加玩家到白名单
/whitelist remove <ID> 移除白名单中的玩家
"""

# 实用函数
def get_id(event: Update) -> int:
    if event.message is None: raise Exception("event.message is none")
    if event.message.from_user is None: raise Exception("event.message.from_user is none")
    return event.message.from_user.id

def execute_bot_command(server: PluginServerInterface, event: Update, context: CommandContext | ContextTypes.DEFAULT_TYPE, content: str, type: MessageType):
    if content.startswith('/'):
        func, args = commands.get(content)
        if func is not None:
            func(server, event, context, args, type)

def check_command(event: Update | None, context: ContextTypes.DEFAULT_TYPE | CommandContext, command: str) -> bool:
    if command not in config.commands: return False
    if config.commands[command] is False:
        if event is not None:
            reply(
                event,
                context,
                f"未开启 \"{command}\" 命令！"
            )
        return False
    return True

def execute(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    if server.is_rcon_running():
        result = server.rcon_query(command)
        if result == "":
            result = "这条命令没有返回值哦~"
    else:
        server.execute(command)
        result = "没开 RCON 所以我也不知道结果~"
    reply(event, context, result)

def save_data(server: PluginServerInterface):
    server.save_config_simple(
        {
            "data": bindings,
        },
        "bindings.json"
    )
    server.save_config_simple(
        {
            "data": ban_list,
        },
        "ban_list.json"
    )

def add_to_whitelist(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, player: str):
    server.execute(config.whitelist["commands"]["add"].format(player))
    reply(
        event,
        context,
        f"把 \"{player}\" 添加到服务器白名单里头去了~"
    )

def remove_from_whitelist(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, player: str):
    server.execute(config.whitelist["commands"]["remove"].format(player))
    reply(
        event,
        context,
        f"把 \"{player}\" 从服务器白名单里头删掉了~"
    )

def send_to_groups(msg: str, context: ContextTypes.DEFAULT_TYPE):
    for i in config.groups:
        _ = context.bot.send_message(chat_id=i, text=msg)

def reply(event: Update | CommandSource, context: ContextTypes.DEFAULT_TYPE, message: str, at_sender: bool = True):
    if isinstance(event, Update) and event.effective_chat is not None:
        _ = context.bot.send_message(chat_id=event.effective_chat.id, text=message, reply_to_message_id=event.effective_chat.id)
    elif isinstance(event, CommandSource):
        event.reply(message)

def parse_event_type(event: Update) -> MessageType:
    return MessageType.ADMIN if str(get_id(event)) in config.admins else MessageType.USER

def register_commands():
    global commands
    commands = CommandBuilder()
    # /mc
    commands.add_command(re.compile(r'/mc (.*)'), [str], tg_command_mc)

    # /list
    commands.add_command("/list", None, tg_command_list)

    #/bind
    commands.add_command("/bind", None, lambda srv, evt, ctx, cmd, typ: reply(evt, ctx, Help.bind))
    commands.add_command(re.compile(r'/bind unbind (\d*)'), [str], tg_command_bind_unbind)
    commands.add_command(re.compile(r'/bind query (TG|ID) (\w*)'), [str, str], tg_command_bind_query)
    commands.add_command(re.compile(r'/bind (\d*) (\w*)'), [str, str], tg_command_bind_admin)
    commands.add_command(re.compile(r'/bind (\w*)'), [str], tg_command_bind_user)

    # /whitelist
    commands.add_command("/whitelist", None, lambda srv, evt, ctx, cmd, typ: reply(evt, ctx, Help.whitelist))
    commands.add_command("/whitelist list", None, lambda srv, evt, ctx, cmd, typ: execute(srv, evt, ctx, "whitelist list") if typ == MessageType.ADMIN else None)
    commands.add_command("/whitelist reload", None, lambda srv, evt, ctx, cmd, typ: execute(srv, evt, ctx, "whitelist reload") if typ == MessageType.ADMIN else None)
    commands.add_command("/whitelist on", None, lambda srv, evt, ctx, cmd, typ: execute(srv, evt, ctx, "whitelist on") if typ == MessageType.ADMIN else None)
    commands.add_command("/whitelist off", None, lambda srv, evt, ctx, cmd, typ: execute(srv, evt, ctx, "whitelist off") if typ == MessageType.ADMIN else None)
    commands.add_command(re.compile(r'/whitelist add (\w*)'), [str], tg_command_whitelist_add)
    commands.add_command(re.compile(r'/whitelist remove (\w*)'), [str], tg_command_whitelist_remove)

    # mcdr
    commands.add_command(re.compile(r'/mcdr (.*)'), [str], tg_command_mcdr)

    # command
    commands.add_command(re.compile(r'/command (.*)'), [str], qq_command_command)

    # /help
    commands.add_command("/help", None, lambda srv, evt, ctx, cmd, typ:
        [reply(evt, ctx, Help.admin), reply(evt, ctx, Help.user)]
    )
    
    # /ping
    commands.add_command("/ping", None, tg_command_ping)
    
    # /start /stop /restart 
    commands.add_command("/start", None, lambda srv, evt, ctx, cmd, typ: srv.start() if typ == MessageType.ADMIN else None)
    commands.add_command("/stop", None, lambda srv, evt, ctx, cmd, typ: srv.stop() if typ == MessageType.ADMIN else None)
    commands.add_command("/restart", None, lambda srv, evt, ctx, cmd, typ: srv.restart() if typ == MessageType.ADMIN else None)
    
    # /info
    commands.add_command("/info", None, tg_command_info)
    
    # /reload
    commands.add_command("/reload", None, tg_command_reload)
    
    # /ban /pardon
    commands.add_command(re.compile(r'/ban (\d*)'), [int], tg_command_ban)
    commands.add_command(re.compile(r'/pardon (\d*)'), [int], tg_command_pardon)
    
    # /bot-
    commands.add_command(re.compile(r'/bot-ban (\d*)'), [int], tg_command_bot_ban)
    commands.add_command(re.compile(r'/bot-pardon (\d*)'), [int], tg_command_bot_pardon)

# MCDR 事件处理函数
def on_load(server: PluginServerInterface, old):
    global config, bindings, ban_list, bot
    
    if old is not None:
        old.bot.application.stop()

    config = server.load_config_simple(target_class=Config)
    bindings = server.load_config_simple(
        "bindings.json",
        default_config={"data": {}},
        echo_in_console=False
    )["data"]
    ban_list = server.load_config_simple(
        "ban_list.json",
        default_config={"data": []},
        echo_in_console=False
    )["data"]

    # server.register_help_message("!!tg", "向 Telegram 群发送聊天信息")
    # server.register_command(
        # Literal("!!tg").then(GreedyText("message").runs(mc_command_tg))
    # )
    server.register_command(
        Literal("!!command").then(GreedyText("command").runs(mc_command_command))
    )

    register_commands()
    
    bot = TelegramBot(config.telegram["token"]) if config.telegram["api"] is None else TelegramBot(config.telegram["token"], config.telegram["api"])
    bot.action = lambda evt, ctx: on_message(server, evt, ctx)

    if old is not None and old.VERSION < VERSION:
        tip: str = f"SALTWO∅Dの自制伯特已从 ver.{old.VERSION_STR} 更新到 ver.{VERSION_STR}"
        # send_to_groups(tip)
        server.say(f"§7{tip}")

def on_message(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE):
    if event.message is None: return
    content = event.message.text
    if content is None: return
    event_type = parse_event_type(event)
    
    # 普通信息
    if config.forwardings["qq_to_mc"] is True:
        id: str = str(get_id(event))
        name: str = f"§a<{bindings[id]}>§7" if id in bindings else f"§4<{event.message.chat.first_name} ({id})>§7"
        server.say(f"§7[TG] <{name}>: {content}")

    # 封禁列表，不作应答
    if get_id(event) in ban_list:
        return
        
    execute_bot_command(server, event, context, content, event_type)

# MC 命令处理器
# def mc_command_tg(src: CommandSource, ctx: CommandContext):
    # if not check_command(None, ctx, "qq"): return
    # player = src.player if src.is_player else "Console"
    # if player not in bindings.values():
        # src.reply("你还没有绑定，请先在群内绑定一下~")
    # elif (not str(next((key for key, value in bindings.items() if value == player), 0)) in config.admins and not src.has_permission(2)) and (player != "Console"):
        # src.reply("你莫得权限哦~")
        # return
    # msg = f"<{player}> {ctx['message']}"
    # send_to_groups(msg)

def mc_command_command(src: CommandSource, ctx: CommandContext):
    if not check_command(None, ctx, "command"): return
    player = src.player if src.is_player else "Console"
    if player not in bindings.values():
        src.reply("你还没有绑定，请先在 QQ 群内绑定一下~")
    elif (not str(next((key for key, value in bindings.items() if value == player), 0)) in config.admins and not src.has_permission(4)) and (player != "Console"):
        src.reply("你莫得权限哦~")
        return
    
    server = src.get_server()
    command = ctx["command"]
    command = command if command.startswith('/') else f"/{command}"
    execute_bot_command(server, src, ctx, command, MessageType.ADMIN)

# QQ 命令处理器
def tg_command_list(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, *args):
    if not check_command(event, context, "list"): return
    online_player_api = server.get_plugin_instance("online_player_api")
    players = online_player_api.get_player_list()

    # generate message
    players_count = len(players)
    message = f"服务器目前有 {players_count} 个玩家在线~"
    if players_count:
        message += f"\n========== 玩家列表 ==========\n"
        for player in players:
            message += f"{player}\n"

    reply(event, context, message)

def tg_command_mc(
        server: PluginServerInterface,
        event: Update,
        context: ContextTypes.DEFAULT_TYPE,
        command: List[str],
        event_type: MessageType
):
    if not check_command(event, context, "mc"): return

    id = str(get_id(event))
    if id in bindings.keys() and id in config.admins:
        server.say(f"§2[QQ] §a<{bindings[id]}>§7 {command[0]}")
    else:
        server.say(f"§7[QQ] §a<{bindings[id]}>§7 {command[0]}")

def tg_command_bind_user(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if not check_command(event, context, "bind"): return
    player = command[0]
    qq = str(get_id(event))

    if config.whitelist["verify_player"] is True:
        # 检查玩家档案是否存在
        response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}")
        if not response.ok:
            reply(
                event,
                context,
                f"没办法获取玩家 \"{player}\" 的资料信息，你是不是输入了一个离线玩家名或者不存在的玩家名？\n详细错误信息：{response.json().get('errorMessage')}"
            )
            return

    if qq in bindings.keys():
        value = bindings[qq]
        reply(
            event,
            context,
            f"你已经绑定了 \"{value}\"，请找管理员修改！"
        )
        return
    else:
        bindings[qq] = player
        reply(
            event,
            context,
            f"成功绑定到 \"{player}\""
        )
        save_data(server)
        if config.whitelist["add_when_bind"] is True:
            add_to_whitelist(server, event, context, player)

def tg_command_bind_admin(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    if not check_command(event, context, "bind"): return
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        player: str = command[1]

        if id in bindings:
            tg_command_bind_unbind(server, event, context, [id], event_type)
        bindings[id] = player
        reply(
            event,
            context,
            f"成功将 Telegram: {id} 绑定到 \"{player}\""
        )
        save_data(server)
        if config.whitelist["add_when_bind"] is True:
            add_to_whitelist(server, event, context, player)

def tg_command_bind_unbind(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                           event_type: MessageType):
    if not check_command(event, context, "bind"): return
    if event_type == MessageType.ADMIN:
        id: str = command[0]
        if id in bindings:
            player: str = bindings[id]
            del bindings[id]
            save_data(server)
            reply(
                event,
                context,
                f"成功解除 Telegram: {id} 对 \"{player}\" 的绑定！"
            )
            if config.whitelist["add_when_bind"] is True:
                remove_from_whitelist(server, event, context, player)

def tg_command_bind_query(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    if not check_command(event, context, "bind"): return
    if event_type == MessageType.ADMIN:
        typ: str = command[0]
        value: str = command[1]
        match typ:
            case "TG":
                result = None
                if value in bindings:
                    result = bindings[value]

                if result is not None:
                    reply(
                        event,
                        context,
                        f"查询到如下结果：\nTelegram: {value} 绑定的是 \"{result}\""
                    )
                else:
                    reply(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
            case "ID":
                result = None
                if value in bindings.values():
                    result = [k for k, v in bindings.items() if v == value]

                if result is not None:
                    reply(
                        event,
                        context,
                        f"查询到如下结果：\n{'\n'.join(map(str, [f'Telegram: {key} 绑定的是 \"{value}\"' for key in result]))}"
                    )
                else:
                    reply(
                        event,
                        context,
                        f"没有查询到结果！"
                    )
            case _:
                ...

def tg_command_whitelist_add(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if not check_command(event, context, "whitelist"): return
    if event_type == MessageType.ADMIN:
        add_to_whitelist(server, event, context, command[0])

def tg_command_whitelist_remove(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                             event_type: MessageType):
    if not check_command(event, context, "whitelist"): return
    if event_type == MessageType.ADMIN:
        remove_from_whitelist(server, event, context, command[0])

def tg_command_mcdr(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if not check_command(event, context, "mcdr"): return
    if event_type == MessageType.ADMIN:
        cmd = command[0]
        cmd = (cmd[2:] if cmd.startswith('!!') else cmd).strip()
        server.execute_command(cmd)
        reply(
            event,
            context,
            f"已执行 MCDR 命令！"
        )

def qq_command_command(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if not check_command(event, context, "command"): return
    cmd = command[0]
    if event_type == MessageType.ADMIN:
        execute(server, event, context, cmd)

def tg_command_info(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event_type == MessageType.ADMIN and check_command(event, context, "info"):
        reply(
            event,
            context,
            get_system_info()
        )

@new_thread("TelegramChat_reload")
def tg_command_reload(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                      event_type: MessageType):
    if event_type == MessageType.ADMIN:
        reply(
            event,
            context,
            f"收到，在 5 秒后重载……"
        )
        time.sleep(5)
        server.reload_plugin("telegram_chat")

def tg_command_ping(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                    event_type: MessageType):
    if event.message is None: raise Exception("event.message is none")
    delay = (time.time() - event.message.date.timestamp()) * 1000
    reply(
        event,
        context,
        f"Pong！服务在线，延迟 {delay:.2f}ms。"
    )

def tg_command_bot_ban(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                       event_type: MessageType):
    id = command[0]
    if id not in ban_list and event_type == MessageType.ADMIN:
        ban_list.append(int(id))
        reply(
            event,
            context,
            f"成功封禁 Telegram: {id}"
        )
        save_data(server)

def tg_command_bot_pardon(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType):
    id = command[0]
    if id in ban_list and event_type == MessageType.ADMIN:
        ban_list.remove(id)
        reply(
            event,
            context,
            f"成功解封账户: {id}"
        )
        save_data(server)

def tg_command_ban(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType): execute(server, event, context, f"ban {command[0]}") if event_type == MessageType.ADMIN else None

def tg_command_pardon(server: PluginServerInterface, event: Update, context: ContextTypes.DEFAULT_TYPE, command: List[str],
                          event_type: MessageType): execute(server, event, context, f"pardon {command[0]}") if event_type == MessageType.ADMIN else None