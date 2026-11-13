$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$settings=Get-Content -LiteralPath (Join-Path $root 'instance.json') -Raw | ConvertFrom-Json
if ([int]$settings.remotePort -lt 1 -or [int]$settings.remotePort -gt 65535 -or [int]$settings.localProxyPort -lt 1 -or [int]$settings.localProxyPort -gt 65535) {throw '请核对实例参数中的 TCP（传输控制协议）端口。'}
$alias=[string]$settings.alias
if($alias -notmatch '^[a-zA-Z0-9_.-]+$' -or $alias.StartsWith('-')) {throw '请核对 SSH（安全远程连接协议）连接别名。'}
$exe=Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$config=Join-Path $root 'ssh-config'
$forward='127.0.0.1:'+([int]$settings.remotePort)+':127.0.0.1:'+([int]$settings.localProxyPort)
$binding=[regex]::Match((Get-Content -LiteralPath $config -Raw),'(?mi)^\s*BindAddress\s+(\S+)')
if($binding.Success -and $binding.Groups[1].Value -notin @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress)) {throw '请根据电脑当前地址更新本实例源地址绑定。'}
if(-not (Test-Path -LiteralPath $settings.gostStartScript -PathType Leaf)) {throw '请先核对共享代理启动脚本的实际路径。'}
& $settings.gostStartScript
$existing=@(Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" | Where-Object {$_.ExecutablePath -eq $exe -and $_.CommandLine -like "*$config*" -and $_.CommandLine -like "*$forward*"})
if($existing.Count -eq 1) {Write-Output ('本实例隧道已运行，进程号 '+$existing[0].ProcessId+'，请继续运行远端验收。');return}
if($existing.Count -gt 1) {throw '请核对多条匹配记录；当前进程保持原状。'}
$logs=Join-Path $root 'logs';New-Item -ItemType Directory -Path $logs -Force | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$arguments=@('-F',('"'+$config+'"'),'-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=30','-o','ServerAliveCountMax=3','-N','-T','-R',$forward,$alias)
$process=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -WorkingDirectory $root -RedirectStandardOutput (Join-Path $logs ('ssh-'+$stamp+'.out.log')) -RedirectStandardError (Join-Path $logs ('ssh-'+$stamp+'.err.log')) -PassThru
@{pid=$process.Id;executable=$exe;config=$config;forward=$forward;startTime=$process.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'tunnel-process.json') -Encoding UTF8
Start-Sleep -Seconds 2
$process.Refresh()
if($process.HasExited) {throw ('请检查本实例错误日志 logs/ssh-'+$stamp+'.err.log')}
Write-Output ('本实例隧道已启动，进程号 '+$process.Id+'，请继续执行端到端验收。')
