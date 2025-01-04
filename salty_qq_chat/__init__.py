import re
from typing import List, Dict, Any, Callable
from asyncio import AbstractEventLoop

from qq_api import MessageEvent
from aiocqhttp import CQHttp, Event
from mcdreforged.api.command import *
from mcdreforged.api.utils import Serializable
from mcdreforged.api.types import PluginServerInterface, CommandSource, Info
from mcdreforged.api.decorator import new_thread
from enum import Enum, unique

import requests
import time
from .command_builder import CommandBuilder
from .info import get_system_info
from .version import *

# 变量声明
bindings: dict[str, str]

bot: CQHttp
event_loop: AbstractEventLoop

commands: CommandBuilder

class Config(Serializable):
    groups: List[int] = []
    treat_qq_admin_as_bot_admin: bool = True

    admins: List[str] = []

    whitelist: Dict[str, Any] = {
        "add_when_bind": False,
        "remove_when_leave_group": True,
        "commands": {
            "add": "whitelist add {}",
            "remove": "whitelist remove {}"
        },
        "verify_player": True,
    }

    debug: bool = False

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
        "qq_to_mc": True,
        "mc_to_qq": False,
    }
    
    need_at: bool = True

config: Config
ban_list: List[int]

class EventType(Enum):
    NONE = 0
    PRIVATE_ADMIN = 1
    PRIVATE_USER = 2
    GROUP_ADMIN = 3
    GROUP_USER = 4

ADMIN = [EventType.PRIVATE_ADMIN, EventType.GROUP_ADMIN]
USER = [EventType.PRIVATE_USER, EventType.GROUP_USER]
PRIVATE = [EventType.PRIVATE_ADMIN, EventType.PRIVATE_USER]
GROUP = [EventType.GROUP_ADMIN, EventType.GROUP_USER]

class Help():
    basic = """命令列表：
- /list 获取在线玩家列表
- /bind <ID> 绑定当前 QQ 号到 Minecraft 账号
- /mc <message> 向 Minecraft 内发送聊天信息
- /ping 查询在线状态并且计算延迟"""
    
    user = f"""SALTWO∅Dの自制伯特 Ver.{VERSION_STR}

{basic}
"""

    admin = f"""SALTWO∅Dの自制伯特 Ver.{VERSION_STR}

{basic}

管理命令列表：
- /bind 查看 /bind 命令详细帮助
- /command 向 Minecraft 服务器发送命令
- /mc <message> 向 Minecraft 内发送聊天信息
- /mcdr <command> 向 MCDR 进程发送命令
- /whitelist <add|remove> <玩家名> 管理白名单
- /start /stop /restart 启动、关闭、重启服务器
- /info **仅私聊**，获取系统信息
- /reload 重载 Bot
- /ban 封禁服务器中的某人
- /pardon 接触某人的服务器封禁
- /bot-ban 不允许某人使用 Bot
- /bot-pardon 不再禁止某人使用 Bot
"""

    bind = """/bind <ID> 绑定当前 QQ 号到 Minecraft 账号
/bind <QQ> <ID> 绑定 QQ 号到 Minecraft 账号
/bind unbind <QQ> 解除 QQ 号与 Minecraft 账号的绑定关系
/bind query "QQ"|"ID" <QQ|ID> 查询 QQ 号或 Minecraft 账号的绑定关系
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
def extract_command(event):
    # 获取 raw_message 中的艾特部分和指令
    raw_message = event.raw_message
    self_id = str(event.self_id)

    # 检查是否艾特了机器人
    if f"[CQ:at,qq={self_id}]" in raw_message:
        match = re.search(r"\[CQ:at,qq=\d+\]\s*(.*)", raw_message)
        if match:
            content = match.group(1).strip()
            return content
    return None

def execute_qq_command(server: PluginServerInterface, event: MessageEvent, content: str,
                       event_type: EventType):
    if content.startswith('/'):
        func, args = commands.get(content)
        if func is not None:
            func(server, event, args, event_type)

def check_command(event: MessageEvent | None, command: str) -> bool:
    if command not in config.commands: return False
    if config.commands[command] is False:
        if event is not None:
            reply(
                event,
                f"[CQ:at,qq={event.user_id}] 未开启 \"{command}\" 命令！"
            )
        return False
    return True

def execute(server: PluginServerInterface, event: MessageEvent, command: str):
    if server.is_rcon_running():
        result = server.rcon_query(command)
        if result == "":
            result = "这条命令没有返回值哦~"
    else:
        server.execute(command)
        result = "没开 RCON 所以我也不知道结果~"
    reply(event, result)

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

def add_to_whitelist(server: PluginServerInterface, event: MessageEvent, player: str):
    server.execute(config.whitelist["commands"]["add"].format(player))
    reply(
        event,
        f"[CQ:at,qq={event.user_id}] 把 \"{player}\" 添加到服务器白名单里头去了~"
    )

def remove_from_whitelist(server: PluginServerInterface, event: MessageEvent, player: str):
    server.execute(config.whitelist["commands"]["remove"].format(player))
    reply(
        event,
        f"[CQ:at,qq={event.user_id}] 把 \"{player}\" 从服务器白名单里头删掉了~"
    )

def send_to_groups(msg: str):
    for i in config.groups:
        event_loop.create_task(
            bot.send_group_msg(group_id=i, message=msg)
        )

def reply(event: Event | CommandSource, message: str):
    if isinstance(event, Event):
        event_loop.create_task(bot.send(event, message))
    elif isinstance(event, CommandSource):
        event.reply(message)
        

def parse_event_type(event: MessageEvent) -> EventType:
    # 私聊
    # if event.detail_type == "private":
    #     if event.user_id in config.admins:
    #         return EventType.PRIVATE_ADMIN
    #     else:
    #         return EventType.PRIVATE_USER
    # elif event.detail_type == "group":
    #     if event.group_id in config.groups:
    #         if event.user_id in config.admins:
    #             return EventType.GROUP_ADMIN
    #         else:
    #             return EventType.GROUP_USER
    #     else:
    #         return EventType.NONE
    qq = str(event.user_id)
    if event.detail_type == "private":
        return EventType.PRIVATE_ADMIN if qq in config.admins else EventType.PRIVATE_USER
    elif event.detail_type == "group" and event.group_id in config.groups:
        return EventType.GROUP_ADMIN if qq in config.admins else EventType.GROUP_USER
    return EventType.NONE

def register_commands():
    global commands
    commands = CommandBuilder()
    # /mc
    commands.add_command(re.compile(r'/mc (.*)'), [str], qq_command_mc)

    # /list
    commands.add_command("/list", None, qq_command_list)

    #/bind
    commands.add_command("/bind", None, lambda srv, evt, cmd, typ: reply(evt, Help.bind))
    commands.add_command(re.compile(r'/bind unbind (\d*)'), [str], qq_command_bind_unbind)
    commands.add_command(re.compile(r'/bind query (QQ|ID) (\w*)'), [str, str], qq_command_bind_query)
    commands.add_command(re.compile(r'/bind (\d*) (\w*)'), [str, str], qq_command_bind_admin)
    commands.add_command(re.compile(r'/bind (\w*)'), [str], qq_command_bind_user)

    # /whitelist
    commands.add_command("/whitelist", None, lambda srv, evt, cmd, typ: reply(evt, Help.whitelist) if typ != EventType.PRIVATE_USER else None)
    commands.add_command("/whitelist list", None, lambda srv, evt, cmd, typ: execute(srv, evt, "whitelist list"))
    commands.add_command("/whitelist reload", None, lambda srv, evt, cmd, typ: execute(srv, evt, "whitelist reload"))
    commands.add_command("/whitelist on", None, lambda srv, evt, cmd, typ: execute(srv, evt, "whitelist on"))
    commands.add_command("/whitelist off", None, lambda srv, evt, cmd, typ: execute(srv, evt, "whitelist off"))
    commands.add_command(re.compile(r'/whitelist add (\w*)'), [str], qq_command_whitelist_add)
    commands.add_command(re.compile(r'/whitelist remove (\w*)'), [str], qq_command_whitelist_remove)

    # mcdr
    commands.add_command(re.compile(r'/mcdr (.*)'), [str], qq_command_mcdr)

    # command
    commands.add_command(re.compile(r'/command (.*)'), [str], qq_command_command)

    # /help
    commands.add_command("/help", None, lambda srv, evt, cmd, typ:
        reply(evt, Help.admin) if typ in ADMIN else (
            reply(evt, Help.user) if typ != EventType.PRIVATE_USER else None
        )
    )
    
    # /ping
    commands.add_command("/ping", None, qq_command_ping)
    
    # /start /stop /restart 
    commands.add_command("/start", None, lambda srv, evt, cmd, typ: srv.start() if typ in ADMIN else None)
    commands.add_command("/stop", None, lambda srv, evt, cmd, typ: srv.stop() if typ in ADMIN else None)
    commands.add_command("/restart", None, lambda srv, evt, cmd, typ: srv.restart() if typ in ADMIN else None)
    
    # /info
    commands.add_command("/info", None, qq_command_info)
    
    # /reload
    commands.add_command("/reload", None, qq_command_reload)
    
    # /ban /pardon
    commands.add_command(re.compile(r'/ban (\d*)'), [int], qq_command_ban)
    commands.add_command(re.compile(r'/pardon (\d*)'), [int], qq_command_pardon)
    
    # /bot-
    commands.add_command(re.compile(r'/bot-ban (\d*)'), [int], qq_command_bot_ban)
    commands.add_command(re.compile(r'/bot-pardon (\d*)'), [int], qq_command_bot_pardon)

# MCDR 事件处理函数
def on_load(server: PluginServerInterface, old):
    global config, bindings, ban_list, bot, event_loop

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

    qq_api = server.get_plugin_instance("qq_api")
    if qq_api is None:
        raise Exception("QQ API 插件未加载")

    bot = qq_api.get_bot()
    event_loop = qq_api.get_event_loop()

    server.register_help_message("!!qq", "向 QQ 群发送聊天信息")
    server.register_command(
        Literal("!!qq").then(GreedyText("message").runs(mc_command_qq))
    )
    server.register_command(
        Literal("!!command").then(GreedyText("command").runs(mc_command_command))
    )
    server.register_event_listener("qq_api.on_message", on_message)
    server.register_event_listener("qq_api.on_notice", on_notice)

    register_commands()

    if old is not None and old.VERSION < VERSION:
        tip: str = f"SALTWO∅Dの自制伯特已从 ver.{old.VERSION_STR} 更新到 ver.{VERSION_STR}"
        send_to_groups(tip)
        server.say(f"§7{tip}")

def on_user_info(server: PluginServerInterface, info: Info):
    if config.forwardings["mc_to_qq"]:
        user = info.player
        user = user if user is not None else "Console"
        send_to_groups(f"<{user}> {info.content}")

def on_message(server: PluginServerInterface, bot: CQHttp,
               event: MessageEvent):
    content = event.content
    event_type = parse_event_type(event)
    
    # 普通信息
    if event.group_id in config.groups and config.forwardings["qq_to_mc"] is True:
        qq: str = str(event.user_id)
        name: str = f"§a<{bindings[qq]}>§7" if qq in bindings else f"§4<{event.sender['nickname']} ({qq})>§7"
        server.say(f"§7[QQ{f':{event.group_id}' if len(config.groups) > 1 else ''}] {name} {event.content if '[CQ:image' not in event.content else '<含有图片内容，已省略>'}")
    
    # 检查范围，范围外就不干了
    if (not event.group_id in config.groups) and (not str(event.user_id) in config.admins):
        return

    # 封禁列表，不作应答
    if int(event.user_id) in ban_list:
        return
    
    if config.need_at and event_type in GROUP:
        extracted = extract_command(event)
        if extracted is None:
            return
        content = extracted
        if not content.startswith('/'): # 艾特就不要斜杠了，应答带斜杠的信息可能会被腾讯夹
            content = f"/{content}"     # 比如，@Bot /help，这样的和官方的机器人很像，可能会被夹
        else: return                    # 所以就选择不应答
        
    execute_qq_command(server, event, content, event_type)

def on_notice(server: PluginServerInterface, bot: CQHttp,
              event: Event):
    # 只看主群的成员
    if not event.group_id in config.groups:
        return

    if event.detail_type == "group_decrease" and config.whitelist["remove_when_leave_group"]:
        qq = str(event.user_id)
        if qq in bindings.keys():
            server.execute(config.whitelist["commands"]["remove"].format(bindings[qq]))
            reply(
                event,
                f"{bindings[qq]} 跑了，把 TA 从服务器的白名单里头删掉了哦~"
            )
            del bindings[qq]
            save_data(server)

# MC 命令处理器
def mc_command_qq(src: CommandSource, ctx: CommandContext):
    if not check_command(None, "qq"): return
    player = src.player if src.is_player else "Console"
    if player not in bindings.values():
        src.reply("你还没有绑定，请先在 QQ 群内绑定一下~")
    elif (not str(next((key for key, value in bindings.items() if value == player), 0)) in config.admins and not src.has_permission(2)) and (player != "Console"):
        src.reply("你莫得权限哦~")
        return
    msg = f"<{player}> {ctx['message']}"
    send_to_groups(msg)

def mc_command_command(src: CommandSource, ctx: CommandContext):
    if not check_command(None, "command"): return
    player = src.player if src.is_player else "Console"
    if player not in bindings.values():
        src.reply("你还没有绑定，请先在 QQ 群内绑定一下~")
    elif (not str(next((key for key, value in bindings.items() if value == player), 0)) in config.admins and not src.has_permission(4)) and (player != "Console"):
        src.reply("你莫得权限哦~")
        return
    
    server = src.get_server()
    command = ctx["command"]
    command = command if command.startswith('/') else f"/{command}"
    execute_qq_command(server, src, command, EventType.PRIVATE_ADMIN)

# QQ 命令处理器
def qq_command_list(server: PluginServerInterface, event: MessageEvent, *args):
    if not check_command(event, "list"): return
    online_player_api = server.get_plugin_instance("online_player_api")
    players = online_player_api.get_player_list()

    # generate message
    players_count = len(players)
    message = f"服务器目前有 {players_count} 个玩家在线~\n"
    if players_count:
        message += f"========== 玩家列表 ==========\n"
        for player in players:
            message += f"{player}\n"

    reply(event, message)

def qq_command_mc(
        server: PluginServerInterface,
        event: MessageEvent,
        command: List[str],
        event_type: EventType
):
    if (not check_command(event, "mc")) or (event_type == EventType.NONE): return

    qq = str(event.user_id)
    if event_type != EventType.PRIVATE_USER:
        if qq in bindings.keys() and qq in config.admins:
            server.say(f"§7[QQ] §a<{bindings[qq]}>§7 {command[0]}")

def qq_command_bind_user(server: PluginServerInterface, event: MessageEvent, command: List[str],
                    event_type: EventType):
    if not check_command(event, "bind"): return
    if event_type != EventType.PRIVATE_USER:
        player = command[0]
        qq = str(event.user_id)

        if config.whitelist["verify_player"] is True:
            # 检查玩家档案是否存在
            response = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player}")
            if not response.ok:
                reply(
                    event,
                    f"[CQ:at,qq={event.user_id}] 没办法获取玩家 \"{player}\" 的资料信息，你是不是输入了一个离线玩家名或者不存在的玩家名？\n详细错误信息：{response.json().get('errorMessage')}"
                )
                return

        if qq in bindings.keys():
            value = bindings[qq]
            reply(
                event,
                f"[CQ:at,qq={event.user_id}] 你已经绑定了 \"{value}\"，请找管理员修改！"
            )
            return
        else:
            bindings[qq] = player
            reply(
                event,
                f"[CQ:at,qq={event.user_id}] 成功绑定到 \"{player}\""
            )
            save_data(server)
            if config.whitelist["add_when_bind"] is True:
                add_to_whitelist(server, event, player)

def qq_command_bind_admin(server: PluginServerInterface, event: MessageEvent, command: List[str],
                          event_type: EventType):
    if not check_command(event, "bind"): return
    if event_type in ADMIN:
        qq: str = command[0]
        player: str = command[1]

        if qq in bindings:
            qq_command_bind_unbind(server, event, [qq], event_type)
        bindings[qq] = player
        reply(
            event,
            f"[CQ:at,qq={event.user_id}] 成功将 QQ: {qq} 绑定到 \"{player}\""
        )
        save_data(server)
        if config.whitelist["add_when_bind"] is True:
            add_to_whitelist(server, event, player)

def qq_command_bind_unbind(server: PluginServerInterface, event: MessageEvent, command: List[str],
                           event_type: EventType):
    if not check_command(event, "bind"): return
    if event_type in ADMIN:
        qq: str = command[0]
        if qq in bindings:
            player: str = bindings[qq]
            del bindings[qq]
            save_data(server)
            reply(
                event,
                f"[CQ:at,qq={event.user_id}] 成功解除 QQ: {qq} 对 \"{player}\" 的绑定！"
            )
            if config.whitelist["add_when_bind"] is True:
                remove_from_whitelist(server, event, player)

def qq_command_bind_query(server: PluginServerInterface, event: MessageEvent, command: List[str],
                          event_type: EventType):
    if not check_command(event, "bind"): return
    if event_type in ADMIN:
        typ: str = command[0]
        value: str = command[1]
        match typ:
            case "QQ":
                result = None
                if value in bindings:
                    result = bindings[value]

                if result is not None:
                    reply(
                        event,
                        f"[CQ:at,qq={event.user_id}] 查询到如下结果：\nQQ: {value} 绑定的是 \"{result}\""
                    )
                else:
                    reply(
                        event,
                        f"[CQ:at,qq={event.user_id}] 没有查询到结果！"
                    )
            case "ID":
                result = None
                if value in bindings.values():
                    result = [k for k, v in bindings if v == value]

                if isinstance(result, List[str]):
                    reply(
                        event,
                        f"[CQ:at,qq={event.user_id}] 查询到如下结果：\n{'\n'.join(map(str, [f'QQ: {key} 绑定的是 \"{value}\"' for key in result]))}"
                    )
                else:
                    reply(
                        event,
                        f"[CQ:at,qq={event.user_id}] 没有查询到结果！"
                    )
            case _:
                ...

def qq_command_whitelist_add(server: PluginServerInterface, event: MessageEvent, command: List[str],
                             event_type: EventType):
    if not check_command(event, "whitelist"): return
    if event_type in ADMIN:
        add_to_whitelist(server, event, command[0])

def qq_command_whitelist_remove(server: PluginServerInterface, event: MessageEvent, command: List[str],
                             event_type: EventType):
    if not check_command(event, "whitelist"): return
    if event_type in ADMIN:
        remove_from_whitelist(server, event, command[0])

def qq_command_mcdr(server: PluginServerInterface, event: MessageEvent, command: List[str],
                    event_type: EventType):
    if not check_command(event, "mcdr"): return
    if event_type in ADMIN:
        cmd = command[0]
        cmd = (cmd[2:] if cmd.startswith('!!') else cmd).strip()
        server.execute_command(cmd)
        reply(
            event,
            f"[CQ:at,qq={event.user_id}] 已执行 MCDR 命令！"
        )

def qq_command_command(server: PluginServerInterface, event: MessageEvent, command: List[str],
                    event_type: EventType):
    if not check_command(event, "command"): return
    cmd = command[0]
    if event_type in ADMIN:
        execute(server, event, cmd)

def qq_command_info(server: PluginServerInterface, event: MessageEvent, command: List[str],
                    event_type: EventType):
    if event_type in PRIVATE and event_type in ADMIN and check_command(event, "info"):
        reply(
            event,
            get_system_info()
        )

@new_thread("SaltyQQChat_reload")
def qq_command_reload(server: PluginServerInterface, event: MessageEvent, command: List[str],
                      event_type: EventType):
    if event_type in ADMIN:
        reply(
            event,
            f"[CQ:at,qq={event.user_id}] 收到，在 5 秒后重载……"
        )
        time.sleep(5)
        server.reload_plugin("salty_qq_chat")

def qq_command_ping(server: PluginServerInterface, event: MessageEvent, command: List[str],
                    event_type: EventType):
    delay = (time.time() - event.time) * 1000
    reply(
        event,
        f"[CQ:at,qq={event.user_id}] Pong！服务在线，延迟 {delay:.2f}ms。"
    )

def qq_command_bot_ban(server: PluginServerInterface, event: MessageEvent, command: List[str],
                       event_type: EventType):
    qq = command[0]
    if qq not in ban_list and event_type in ADMIN:
        ban_list.append(qq)
        reply(
            event,
            f"[CQ:at,qq={event.user_id}] 成功封禁 QQ: {qq}"
        )
        save_data(server)

def qq_command_bot_pardon(server: PluginServerInterface, event: MessageEvent, command: List[str],
                          event_type: EventType):
    qq = command[0]
    if qq in ban_list and event_type in ADMIN:
        ban_list.remove(qq)
        reply(
            event,
            f"[CQ:at,qq={event.user_id}] 成功解封 QQ: {qq}"
        )
        save_data(server)

def qq_command_ban(server: PluginServerInterface, event: MessageEvent, command: List[str],
                          event_type: EventType): execute(server, event, f"ban {command[0]}") if event_type in ADMIN else None

def qq_command_pardon(server: PluginServerInterface, event: MessageEvent, command: List[str],
                          event_type: EventType): execute(server, event, f"pardon {command[0]}") if event_type in ADMIN else None