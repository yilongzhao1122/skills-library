$ErrorActionPreference='Stop'
$recordPath=Join-Path $PSScriptRoot 'tunnel-process.json'
if(-not (Test-Path -LiteralPath $recordPath)) { Write-Output '本实例当前处于停止状态。'; return }
$record=Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$process=Get-Process -Id $record.pid -ErrorAction SilentlyContinue
if(-not $process) { Write-Output '本实例隧道已停止。'; return }
$details=Get-CimInstance Win32_Process -Filter ('ProcessId='+$record.pid)
if($record.config -ne (Join-Path $PSScriptRoot 'ssh-config') -or $details.ExecutablePath -ne $record.executable -or $details.CommandLine -notlike "*$($record.config)*" -or $details.CommandLine -notlike "*$($record.forward)*" -or $process.StartTime.ToUniversalTime().Ticks -ne ([datetime]$record.startTime).ToUniversalTime().Ticks) { throw '请核对本实例进程身份；当前进程保持原状。' }
Stop-Process -Id $record.pid
Write-Output '本实例隧道已停止，共享代理和其他通道继续运行。'
