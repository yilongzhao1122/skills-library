"""盘点私人主目录、已有 Python 和回环隧道后，部署个人代理环境。"""
import datetime,json,os,pathlib,shlex,stat,sys
from urllib.parse import quote

home=pathlib.Path.home().resolve();os.umask(0o077)
port=int(PAYLOAD['port']);password=PAYLOAD['proxy_password'];username=PAYLOAD['username']
if not 1<=port<=65535 or not password:raise RuntimeError('Invalid port or empty proxy credential')
# Refuse a listener exposed by sshd GatewayPorts, before writing any secret.
listeners=[]
for filename in ['/proc/net/tcp','/proc/net/tcp6']:
    for line in pathlib.Path(filename).read_text().splitlines()[1:]:
        row=line.split()
        if row[3]=='0A' and int(row[1].split(':')[1],16)==port:listeners.append(row[1].split(':')[0])
if listeners!=['0100007F']:raise RuntimeError('Expected exactly one IPv4 loopback listener on the chosen remote port')
def checked(path):
    if os.path.commonpath([str(home),str(path.resolve())])!=str(home):raise RuntimeError('Refusing paths outside the private HOME')
    if path.is_symlink():raise RuntimeError('Inspect existing symlink before replacement: '+str(path))
    return path
state=checked(home/'.local/state/pcvpn');state.mkdir(parents=True,exist_ok=True,mode=0o700);state.chmod(0o700)
backup=state/'backups'/('environment-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True,mode=0o700)
files=[]
def install(path,content,mode):
    checked(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.exists():
        old=backup/path.relative_to(home);old.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        old.write_bytes(path.read_bytes());old.chmod(0o600)
    path.write_text(content,encoding='utf-8');path.chmod(mode);files.append(str(path))
private=checked(home/'.config/pcvpn');private.mkdir(parents=True,exist_ok=True,mode=0o700);private.chmod(0o700)
config=dict(host='127.0.0.1',port=port,username=username,password=password,no_proxy=PAYLOAD['no_proxy'])
install(private/'config.json',json.dumps(config,indent=2)+'\n',0o600)
url='http://'+quote(username,safe='')+':'+quote(password,safe='')+'@127.0.0.1:'+str(port)
env='\n'.join('export '+k+'='+shlex.quote(url) for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy','ALL_PROXY','all_proxy'])+'\n'
env+='\n'.join('export '+k+'='+shlex.quote(config['no_proxy']) for k in ['NO_PROXY','no_proxy'])+'\n'
install(private/'environment.sh',env,0o600)
install(private/'shell.sh',PAYLOAD['support_files']['shell.sh'],0o600)
tool=home/'.local/lib/pcvpn/pcvpn.py';install(tool,PAYLOAD['support_files']['pcvpn.py'],0o600)
for name in ['pcvpn-run','pcvpn-test']:
    code='import sys;sys.argv[0]='+repr(name)+';exec(compile(open('+repr(str(tool))+').read(),'+repr(str(tool))+',"exec"))'
    install(home/'.local/bin'/name,'#!/bin/bash\nexec '+shlex.quote(sys.executable)+' -c '+shlex.quote(code)+' "$@"\n',0o700)
bashrc=home/'.bashrc';original=bashrc.read_text() if bashrc.exists() else ''
marker='# >>> PCVPN user commands (no automatic proxy) >>>'
if marker not in original:
    block='\n'+marker+'\nexport PATH="$HOME/.local/bin:$PATH"\n[ ! -f "$HOME/.config/pcvpn/shell.sh" ] || . "$HOME/.config/pcvpn/shell.sh"\n# <<< PCVPN user commands <<<\n'
    install(bashrc,original+block,stat.S_IMODE(bashrc.stat().st_mode) if bashrc.exists() else 0o600)
result=dict(time=datetime.datetime.now().astimezone().isoformat(),files=files,backup=str(backup),remotePort=port,python=sys.executable,automaticProxyEnabled=False)
(state/'install-manifest.json').write_text(json.dumps(result,indent=2));(state/'install-manifest.json').chmod(0o600)
print(json.dumps(result))
