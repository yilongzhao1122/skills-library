param([switch]$ModelTest,[switch]$UpdateTest)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$s=Get-Content -LiteralPath (Join-Path $root 'instance.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$logs=Join-Path $root 'logs';New-Item -ItemType Directory -Path $logs -Force | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
function Read-Records($lines){@($lines | Where-Object {$_ -match '^\{'} | ForEach-Object {$_ | ConvertFrom-Json})}
$pc=@(Read-Records @(& $s.pcProxyTestScript -Targets @('https://api.ipify.org','https://www.google.com','https://github.com','https://chatgpt.com')))
$noAuth=@(Read-Records @(& $s.pcProxyTestScript -NoAuth -Targets 'https://www.google.com'))
function Send-Check([string]$file){
    $lines=@(& $s.python -I -B (Join-Path $s.supportPath 'scripts\send-remote.py') --ssh-config (Join-Path $root 'ssh-config') --alias $s.alias --remote-python $s.remotePython --remote-port $s.remotePort --script $file)
    if($LASTEXITCODE -ne 0){throw ('请核对远端检查：'+[IO.Path]::GetFileName($file)+"`n"+($lines -join "`n"))}
    return (($lines | Select-Object -Last 1) | ConvertFrom-Json)
}
$model=$null;$tui=$null;$update=$null
if($UpdateTest){$update=Send-Check (Join-Path $s.supportPath 'scripts\test-update.py')}
if($ModelTest){
    Write-Host '本轮将使用账号执行一次模型请求和一次默认交互测试。'
    $model=Send-Check (Join-Path $s.supportPath 'linux\test-codex.py')
    $tui=Send-Check (Join-Path $s.supportPath 'linux\test-codex-tui.py')
}
$remote=Send-Check (Join-Path $s.supportPath 'scripts\test-deployment.py')
$pcIP=($pc | Where-Object {$_.target -eq 'https://api.ipify.org'} | Select-Object -First 1).body
$remoteIP=($remote.network | Where-Object {$_.target -eq 'https://api.ipify.org'} | Select-Object -First 1).body
$pcPassed=$pc.Count -eq 4 -and @($pc | Where-Object {$_.curlExit -ne 0 -or $_.metrics.http -ne 200 -or $_.metrics.connect -ne 200 -or $_.metrics.tlsVerify -ne 0}).Count -eq 0
$passed=$pcPassed -and $noAuth.Count -eq 1 -and $noAuth[0].metrics.connect -eq 407 -and $pcIP -eq $remoteIP -and $remote.liveChecksPassed
if($ModelTest){$passed=$passed -and $model.inferenceExit -eq 0 -and $model.turnCompleted -and $model.finalMessage -eq 'PCVPN_AUTODL_OK' -and $tui.modelAnswerObserved}
if($UpdateTest){$passed=$passed -and $update.exit -eq 0 -and $update.wrapperUnchanged -and $update.protectedConfigurationUnchanged}
$r=[ordered]@{time=(Get-Date -Format o);allPassed=$passed;pcIP=$pcIP;remoteIP=$remoteIP;modelExecutedThisRun=[bool]$ModelTest;updateExecutedThisRun=[bool]$UpdateTest;pc=$pc;pcNoAuth=$noAuth;remote=$remote;currentModel=$model;currentTui=$tui;currentUpdate=$update}
$r | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $logs ('acceptance-'+$stamp+'.json')) -Encoding UTF8
$r | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath (Join-Path $root 'acceptance-report.json') -Encoding UTF8
if(-not $passed){throw '请按验收报告中的观察值处理对应检查项。'}
Write-Host ('本轮检查通过，两端出口：'+$pcIP+'。本轮执行项目与历史记录已分别保存在报告中。')
