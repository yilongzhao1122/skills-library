$ErrorActionPreference='Stop'
$settings=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'instance.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$config=Join-Path $PSScriptRoot 'ssh-config'
Write-Host '请在终端提示的官方页面完成 ChatGPT 设备授权，设备码保留在此终端。'
& "$env:WINDIR\System32\OpenSSH\ssh.exe" -tt -F $config -o StrictHostKeyChecking=yes $settings.alias '/bin/bash -lc ''"$HOME/.local/bin/codex" login --device-auth'''
if($LASTEXITCODE -ne 0){throw '请根据终端信息处理登录状态，再继续验收。'}
Write-Host '授权流程已完成，可关闭此窗口。'
Read-Host '按回车关闭'
