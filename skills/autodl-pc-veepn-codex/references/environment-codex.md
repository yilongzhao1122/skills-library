# 个人环境与 Codex 安装

## 按需启用代理

先阅读 `scripts/send-remote.py`（通过已验证连接传送辅助程序）、`scripts/install-user-environment.py`（安装个人环境的程序）和 `assets/linux/`（服务器侧辅助文件目录）。使用已调查的私人 HOME（个人主目录）、Python 路径与本实例回环端口。

电脑执行示例：

```powershell
& '<电脑Python绝对路径>' -I -B '<技能目录>\scripts\send-remote.py' `
  --ssh-config '<本实例目录>\ssh-config' --alias pcvpn-autodl `
  --remote-python '<远端Python绝对路径>' `
  --script '<技能目录>\scripts\install-user-environment.py' `
  --proxy-password-file '<现有GOST口令文件绝对路径>' `
  --remote-port <已核对的远端端口> `
  --support-dir '<技能目录>\assets\linux'
```

SSH（安全远程连接协议）的主机校验和已有认证通过后，脚本经标准输入传递程序与凭据。服务器部署：

| 路径或命令 | 用途 |
|---|---|
| `~/.config/pcvpn/config.json`、`environment.sh` | 个人代理配置，文件权限 600 |
| `~/.config/pcvpn/shell.sh` | Bash（命令解释器）中的启停和恢复函数 |
| `~/.local/lib/pcvpn/pcvpn.py` | 子进程代理环境与脱敏联网测试 |
| `~/.local/bin/pcvpn-run`、`pcvpn-test` | 非交互连接也可使用的命令入口 |
| `~/.local/state/pcvpn/backups/` | 变更前备份和文件清单 |

代理变量兼顾大小写，直连例外包含回环、实际内网和 AutoDL（云计算平台）目标。按所用程序的语法确认例外规则。

`.bashrc`（Bash 的交互启动配置）追加有标记的区块，加载命令路径和函数，完整保留原 Conda（Python 环境管理工具）初始化。默认维持原代理状态。已打开的会话可执行：

```bash
export PATH="$HOME/.local/bin:$PATH"
source "$HOME/.config/pcvpn/shell.sh"
pcvpn-run python your_script.py
pcvpn-on
pcvpn-off
pcvpn-test
```

`PATH`（命令搜索路径）决定入口选择。`pcvpn-run`（为一个子进程开启代理）、`pcvpn-on`（为当前命令解释器开启代理）、`pcvpn-off`（恢复原代理环境）分别按各自范围生效。旧终端和已有服务的环境各自保留，按需要重新加载。

项目依赖沿用用户已有环境；用户另行指定项目依赖时，先调查项目要求，再使用独立环境安装。

## 安装官方完整程序包

盘点已有 Codex（编程助手）的入口、真实程序、版本、登录方式，以及 `CODEX_HOME`（Codex 状态与配置目录）。服务商配置和接口密钥变量记录是否设置，现有有效 ChatGPT 登录保持原样。接口配置需要调整时，先备份，再只调整 Codex 的对应范围。

依据执行时的[官方命令行说明](https://learn.chatgpt.com/docs/cli)核对安装方式。下载 `https://chatgpt.com/codex/install.sh`（官方独立安装脚本）到本次工作目录，审阅后记录来源和 SHA-256（文件摘要算法）摘要，保留 TLS（传输层安全协议）校验与官方程序包完整性检查。

通过上述传送程序执行 `scripts/install-codex-managed.py`（官方安装与代理入口配置程序），传入 `--installer-file <已审阅安装器>`（指定安装脚本）。默认解析官方最新版本，指定版本时使用 `--release <版本>`（选择发行版）。

该阶段验证程序包与安装结构，单独记录 `pendingLogin`（等待用户登录）状态。新实例登录前，健康检查的认证项会提示登录；完成官方授权后，重新执行整体健康检查和模型验收。

官方布局：

```text
~/.codex/packages/standalone/releases/<版本>-<平台>/
~/.codex/packages/standalone/current -> 当前完整发行版
~/.local/share/pcvpn/codex-standalone-bin/codex -> 官方当前命令
~/.local/bin/codex -> 个人代理入口 -> 官方管理命令
```

外层入口显式设置同一状态目录和 `CODEX_INSTALL_DIR`（官方命令入口目录），命令路径优先保留外层入口，内部入口跟随当前完整包。`codex update`（升级命令）据此识别官方安装结构，并继续保留代理配置。

下载大文件需要改走 AutoDL 直连时，先对实际文件路径验证访问，再使用 `--download-direct`（仅让本次安装下载直连）。安装进程超时，仅终止本次创建的安装器进程组。已有用户会话继续运行，升级后退出并重开 Codex 即使用新版本。

## ChatGPT 授权和终端体验

先执行 `codex login status`（检查登录状态）。已有有效 ChatGPT 登录继续使用；需要登录时，在用户可见终端执行 `codex login --device-auth`（设备授权登录），由用户在官方页面完成账号和 2FA（二次身份验证）。设备码保留在用户终端，等待用户确认后继续依赖认证的测试。

`Login-Codex.ps1`（电脑侧交互登录脚本）提供严格主机校验下的可见终端。核对当前帮助确认参数，参考[官方认证说明](https://learn.chatgpt.com/docs/auth?surface=cli)。

日常使用 `codex` 启动默认交互。需要终端回滚时，可使用 `codex --no-alt-screen`（在普通屏幕中显示并保留终端滚动历史）。tmux（终端会话管理工具）中的滚动方式按当前终端配置单独确认。
