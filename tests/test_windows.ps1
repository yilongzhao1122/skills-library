# 在临时目录运行测试脚本，模拟电脑网站与远端响应。
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot
$work=Join-Path ([IO.Path]::GetTempPath()) ('skills-library-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work | Out-Null
Copy-Item -LiteralPath (Join-Path $repo 'skills\autodl-pc-veepn-codex\assets\windows\Test-AutoDL.ps1') -Destination $work
$pc=Join-Path $work 'fixture-pc.ps1'
@'
param([string[]]$Targets,[switch]$NoAuth)
foreach($target in $Targets){
 $record=@{target=$target;curlExit=0;metrics=@{http=200;connect=200;tlsVerify=0};body='198.51.100.20'}
 if($NoAuth){$record.curlExit=56;$record.metrics.connect=407}
 $record | ConvertTo-Json -Compress
}
'@ | Set-Content -LiteralPath $pc -Encoding UTF8
$python=Join-Path $work 'fixture-python.ps1'
@'
$file=$args[-1]
$r=@{liveChecksPassed=$true;network=@(@{target='https://api.ipify.org';body=$env:SKILLS_TEST_REMOTE_IP})}
if($file -like '*test-codex.py'){$r=@{inferenceExit=0;turnCompleted=$true;finalMessage='PCVPN_AUTODL_OK'}}
if($file -like '*test-codex-tui.py'){$r=@{modelAnswerObserved=$true}}
if($file -like '*test-update.py'){$r=@{exit=0;wrapperUnchanged=$true;protectedConfigurationUnchanged=$true}}
$r | ConvertTo-Json -Compress -Depth 10
$global:LASTEXITCODE=0
'@ | Set-Content -LiteralPath $python -Encoding UTF8
@{alias='fixture';remotePort=17893;python=$python;remotePython='/fixture/python';supportPath=$work;pcProxyTestScript=$pc} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'instance.json') -Encoding UTF8
$previous=$env:SKILLS_TEST_REMOTE_IP
try {
 $env:SKILLS_TEST_REMOTE_IP='198.51.100.20'
 try { & (Join-Path $work 'Test-AutoDL.ps1') -ModelTest -UpdateTest } catch {
  Get-Content -LiteralPath (Join-Path $work 'acceptance-report.json') -Raw -Encoding UTF8 | Write-Output
  throw
 }
 $r=Get-Content -LiteralPath (Join-Path $work 'acceptance-report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 if(-not $r.allPassed -or -not $r.modelExecutedThisRun -or -not $r.updateExecutedThisRun){throw '请核对成功路径中的执行记录'}
 $env:SKILLS_TEST_REMOTE_IP='198.51.100.21'
 $caught=$false
 try { & (Join-Path $work 'Test-AutoDL.ps1') } catch { $caught=$true }
 $r=Get-Content -LiteralPath (Join-Path $work 'acceptance-report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 if(-not $caught -or $r.allPassed -or $r.modelExecutedThisRun -or $r.updateExecutedThisRun){throw '请核对出口变化的检查结果'}
 Write-Output '两项电脑脚本隔离检查通过：本轮执行标记、出口变化识别。'
} finally {
 $env:SKILLS_TEST_REMOTE_IP=$previous
 $resolved=[IO.Path]::GetFullPath($work)
 $temp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
 if(-not $resolved.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'skills-library-*'){throw '请核对临时测试目录'}
 Remove-Item -LiteralPath $resolved -Recurse -Force
}
