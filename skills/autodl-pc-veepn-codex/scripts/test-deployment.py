"""重新验证远端网络、环境和账号，同时列出历史模型与升级记录。"""
import datetime,json,os,pathlib,shlex,subprocess

os.umask(0o077)
home=pathlib.Path.home();state=home/'.local/state/pcvpn';cli=home/'.local/bin/codex'
cfg=json.loads((home/'.config/pcvpn/config.json').read_text())
port=int(PAYLOAD['port'])
def run(args,timeout=60):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    return p.returncode,(p.stdout+p.stderr).replace(cfg['password'],'<REDACTED>').strip()
network_exit,network_output=run([str(home/'.local/bin/pcvpn-test')],180)
network=[json.loads(line) for line in network_output.splitlines() if line.startswith('{')]
version_exit,version=run([str(cli),'--version'])
login_exit,login=run([str(cli),'login','status'])
doctor_exit,doctor_text=run([str(cli),'doctor','--json'])
try:doctor=json.loads(doctor_text)
except ValueError:doctor={}
listeners=[]
for table in ['/proc/net/tcp','/proc/net/tcp6']:
    for line in pathlib.Path(table).read_text().splitlines()[1:]:
        row=line.split()
        if row[3]=='0A' and int(row[1].split(':')[1],16)==port:listeners.append(row[1].split(':')[0])
shell=r'''set -e
source "$HOME/.config/pcvpn/shell.sh"
export HTTP_PROXY=pcvpn_restore_sentinel
unset HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
pcvpn-on >/dev/null
pcvpn-on >/dev/null
[[ $HTTP_PROXY == http://*@127.0.0.1:PORT ]]
pcvpn-off >/dev/null
[[ $HTTP_PROXY == pcvpn_restore_sentinel ]]
for key in HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy; do [[ ! -v $key ]]; done
pcvpn-run PYTHON -c 'import os; assert os.environ["HTTPS_PROXY"].endswith("@127.0.0.1:PORT")'
[[ $HTTP_PROXY == pcvpn_restore_sentinel && ! -v HTTPS_PROXY ]]
'''.replace('PORT',str(port)).replace('PYTHON',shlex.quote(os.sys.executable))
shell_exit,_=run(['/bin/bash','--noprofile','--norc','-c',shell])
startup_exit,_=run(['/bin/bash','-ic','command -v codex >/dev/null && command -v pcvpn-run >/dev/null && declare -F pcvpn-on pcvpn-off >/dev/null'])
install_path=state/'codex-install.json'
installation=json.loads(install_path.read_text()) if install_path.exists() else {}
codex_home=pathlib.Path(installation.get('codexHome',str(home/'.codex')))
directories=[home/'.config/pcvpn',state,codex_home]
sensitive=[home/'.config/pcvpn/config.json',home/'.config/pcvpn/environment.sh',home/'.config/pcvpn/shell.sh']
if (codex_home/'auth.json').exists():sensitive.append(codex_home/'auth.json')
permissions={str(path):oct(path.stat().st_mode&0o777) for path in directories+sensitive}
permissions_ok=all(path.stat().st_mode&0o777==0o700 for path in directories) and all(path.stat().st_mode&0o777==0o600 for path in sensitive)
recorded={}
for name in ['codex-test-result.json','codex-tui-test-result.json','codex-update-result.json']:
    path=state/name;recorded[name]=json.loads(path.read_text()) if path.exists() else None
result=dict(time=datetime.datetime.now().astimezone().isoformat(),network=network,networkExit=network_exit,
            version=version,versionExit=version_exit,login=login,loginExit=login_exit,doctorStatus=doctor.get('overallStatus'),doctorExit=doctor_exit,
            listeners=listeners,remotePort=port,shellRestoreExit=shell_exit,newBashExit=startup_exit,permissions=permissions,recordedChecks=recorded)
result['liveChecksPassed']=network_exit==version_exit==login_exit==doctor_exit==shell_exit==startup_exit==0 and 'chatgpt' in login.lower() and listeners==['0100007F'] and int(cfg['port'])==port and permissions_ok
path=state/'deployment-test.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2));path.chmod(0o600)
print(json.dumps(result,ensure_ascii=True))
raise SystemExit(0 if result['liveChecksPassed'] else 1)
