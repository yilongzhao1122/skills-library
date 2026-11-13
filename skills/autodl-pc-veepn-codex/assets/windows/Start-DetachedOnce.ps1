$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'Start-AutoDL.ps1'
$log=Join-Path $PSScriptRoot ('detached-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'.log')
# 将启动指令编码，保留空格、引号和中文路径。
$task='try { & '''+$script.Replace("'","''")+''' *> '''+$log.Replace("'","''")+''' } catch { $_ | Out-File -LiteralPath '''+$log.Replace("'","''")+''' -Append; exit 1 }'
$encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($task))
$shell=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$startup=New-CimInstance -CimClass (Get-CimClass -ClassName Win32_ProcessStartup) -ClientOnly -Property @{ShowWindow=[uint16]0}
$result=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=('"'+$shell+'" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -EncodedCommand '+$encoded);CurrentDirectory=$PSScriptRoot;ProcessStartupInformation=$startup}
if($result.ReturnValue -ne 0) {throw ('请检查 WMI（Windows 管理接口）返回码：'+$result.ReturnValue)}
Write-Output ('一次性后台启动器已创建，请查看 '+$log+'，再运行本实例测试脚本。日常连接由用户按需启动。')
