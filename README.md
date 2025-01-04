<div align="center">

![SaltyQQChat](https://socialify.git.ci/SALTWOOD/SaltyQQChat/image?description=1&font=Inter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

# SaltyQQChat
✨🎉 **基于 QQAPI 的、可拓展的 QQ 机器人插件！** 🎉✨
</div>

# 简介
这是一个使用 [QQAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_api) 的 QQ 机器人插件，可以说相当于重写了 [QQChat](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_chat)，砍掉了很多个人认为没必要的功能，优化了代码结构。

同时，它还支持通过**插件套插件**的方式，简单地扩展机器人，添加属于你的命令！

目前相比 QQChat 新增功能：
- [x] 支持通过 `/bot-ban` `/bot-pardon` 拒绝响应某用户
- [x] 支持通过机器人执行更多原版命令而不使用 `/command`（如 `/ban` `/pardon`）
- [x] 支持通过机器人启停服务器
- [x] 支持艾特机器人进行答复，而不是发一句什么命令就答复
- [x] 支持 MC 内执行 QQ 机器人命令
- [x] 通过 `/ping` 命令、`/info` 命令检查机器人状态
- [x] **[开发特性]** 通过 `/reload` 远程重载插件
- [x] 可自定义的单向/双向 MC <==> QQ 群转发
- [x] 基于正则表达式的易扩展命令树

同时，还去除/修改了以下功能：
- [x] 没有“管理群”、“主群”、“消息同步群”的功能，改为多群同步（不过一般就一个群而已）
- [x] 没有“MultiServer”特性，因为会导致难以预料的 bug 且应用面小
- [x] 对 `!!qq` 命令做了权限限制，因为没有对 CQ 码进行转义，可能会导致机器人账号被用于发布违规信息
- [x] 中文和数字、英文之间做了间隔，且语气更加诙谐

# 使用
## 通过 MCDR 安装
在 MCDR 控制台使用 `!!MCDR plugin install salty_qq_chat`，然后 `!!MCDR confirm`。

## 通过 Release 安装
在 [Releases 页面](https://github.com/SALTWOOD/SaltyQQChat/releases) 下载对应版本的 `.mcdr` 文件，放入 `plugins` 文件夹重载。

## 通过源代码
在 `plugins` 下执行 `git clone https://github.com/SALTWOOD/SaltyQQChat` 或者 `git clone git@github.com:SALTWOOD/SaltyQQChat`，然后重载插件。

# 插件套插件
这是这个插件最有意思的功能之一，有意思到我还没琢磨出来
简单来说就是通过一个单文件插件，获取到 SaltyQQChat 的插件实例，然后
```Python
import re

commands.add_command(re.compile(r'/你的命令 <你的参数>'), [int, str, float], handler)
```
就可以添加命令了。稍迟些我会将代码放出来，直接改就可以用。

# 特别鸣谢
- [QQAPI](https://github.com/AnzhiZhang/MCDReforgedPlugins/tree/master/src/qq_api) - 提供正向 WebSocket 接入到 CQHttp 的接口
- [AnzhiZhang](https://github.com/AnzhiZhang) - 特例为我提供 LGPL 协议授权，但是我还是用了 GPL（
- **SALTWO∅D 服务器的各位** - 帮我测试机器人，还赶在发布 Release 之前帮我发现了越权漏洞（

# 碎碎念
- 其实这个项目也不是照抄 QQChat 的啦，只是因为能找到适合我的环境的现成的 API 只有 QQAPI 一个，又只有一个 QQChat 是这个 API 的下游使用，所以有些部分比较像是无法避免的（）