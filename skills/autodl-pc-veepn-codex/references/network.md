# 网络部署

## 先验证电脑出口

确认用户已连接 VeePN（虚拟专用网络软件），记录实际使用的 WireGuard（虚拟专用网络协议）连接和应用分流方式。调查现有 GOST（网络代理转发工具）的程序、配置、启动脚本、口令文件，以及 DNS（域名解析服务）辅助程序。

已有工程可沿用 `D:\GOST\veepn-bridge` 这样的路径；以实际调查结果填写路径。读取 `Start-Gost.ps1`（共享代理启动脚本）和 `Test-Proxy.ps1`（电脑侧代理测试脚本），确认调用范围。共享代理继续保留原配置，本实例在工程的 `autodl-instances/<实例简称>/`（实例运行目录）保存独立文件。

电脑代理采用回环地址、HTTP Basic（网页传输协议的基本认证方式）认证和私密口令文件。已有名称解析辅助程序继续复用。首次建立电脑工程时，参照 [GOST 官方文档](https://gost.run/)完成这些配置，记录程序来源和实际路径，再验证以下项目：

- 通过认证的出口查询与 Google、GitHub、ChatGPT 请求，记录 HTTP（网页传输协议）状态、CONNECT（建立代理隧道的方法）状态、TLS（传输层安全协议）证书校验及耗时。
- 使用省略代理认证的请求确认返回 407（要求提供代理认证）。
- 核对代理进程、配置路径和回环监听。口令通过 `curl --config -`（从标准输入读取请求配置）传递，输出保留脱敏数据。

Windows PowerShell 5.1（Windows 命令行工具）调用 `curl.exe` 时使用 `--noproxy "no-match.invalid"`（确保测试请求经过代理）。

## 核验主机和已有认证

使用 AutoDL（云计算平台）当前控制台提供的 SSH（安全远程连接协议）命令。调查现有 OpenSSH（SSH 的常用实现）配置、已有私钥路径和可信主机记录，保持严格公钥校验。

首次连接或实例重建后，从可信控制台终端执行 `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`（显示主机公钥指纹的命令），或由用户通过可信渠道核验指纹，再写入本实例的 `known_hosts`（可信主机公钥记录）。`ssh-keyscan`（收集主机公钥的命令）提供待核验公钥。

已有公钥认证可用时直接复用。需要密码时安排用户在交互终端输入；新增公钥或更换认证方式，在说明影响并获得授权后执行。

独立 `ssh-config`（SSH 配置文件）示例，所有尖括号参数通过调查填写：

```sshconfig
Host pcvpn-autodl
    HostName <控制台当前主机名>
    User <实例用户>
    Port <控制台当前端口>
    IdentityFile <已授权复用的私钥绝对路径>
    IdentitiesOnly yes
    StrictHostKeyChecking yes
    UserKnownHostsFile <本实例目录的正斜杠路径>/known_hosts
    BatchMode yes
    ConnectTimeout 15
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
```

`BatchMode yes`（使用已有认证的批处理模式）用于免密验证通过后的后台隧道。所有命令显式指定 `-F <本实例配置>`（选择独立连接配置）。

## 盘点远端和建立隧道

登录后只读调查用户身份、私人主目录、系统版本、处理器架构、磁盘、已有 Python/Conda（Python 环境管理工具）和命令路径。敏感环境变量记录名称与是否设置。非交互连接的命令路径精简时，检查实际的 `~/miniconda3/bin/python3` 等已有路径。

候选远端端口可从 17893 开始，用 `ss`（查看套接字的命令）或 `/proc/net/tcp`、`/proc/net/tcp6`（内核网络连接表）检查占用。已有可用隧道经过验证后复用，其他占用先识别所有者，再选择合适端口。

将本包 `assets/windows/`（电脑侧脚本模板目录）复制到本实例目录，将 `scripts/`（辅助程序目录）和 `assets/linux/`（服务器侧辅助文件目录）分别复制成实例的 `support/scripts/` 与 `support/linux/`。生成 `instance.json`（实例参数文件）：

```json
{
  "alias": "pcvpn-autodl",
  "remotePort": 17893,
  "localProxyPort": 18080,
  "gostStartScript": "D:\\GOST\\veepn-bridge\\Start-Gost.ps1",
  "pcProxyTestScript": "D:\\GOST\\veepn-bridge\\Test-Proxy.ps1",
  "python": "<电脑Python绝对路径>",
  "remotePython": "<远端已有Python绝对路径>",
  "supportPath": "<本实例目录>\\support"
}
```

示例端口由本次盘点确认后填写，代理监听和反向隧道保持一致。电脑发起：

```powershell
ssh.exe -F '<本实例目录>\ssh-config' -N -T -R 127.0.0.1:<远端端口>:127.0.0.1:<电脑代理端口> pcvpn-autodl
```

`Start-AutoDL.ps1`（启动脚本）保存 PID（进程标识号）及创建时间；`Stop-AutoDL.ps1`（停止脚本）逐项核对后仅结束本实例进程。建立后重新查询远端实际监听地址，确认是 `127.0.0.1`，再进行端到端代理测试。

自动化工具结束时会回收子进程的环境，可使用 `Start-DetachedOnce.ps1`（一次性独立后台启动脚本）。该脚本通过 WMI（Windows 管理接口）创建隐藏启动器；日常连接仍由用户按需启动和测试。

## 路径诊断

分开测电脑到 SSH 主机、电脑代理、远端隧道和网站请求。若默认 SSH 路径较慢，调查实际物理网卡和路由，用本实例配置单独验证 `BindAddress`（连接源地址）和 `IPQoS none`（采用普通服务质量标记）。实测改善后再保存到本实例配置。

电脑地址变化后重新核对绑定。停止隧道后的远端端口释放可能需要短暂等待；确认本实例旧连接已释放后再启动。已有其他服务保持原状。
