"""通过已验证主机身份的连接，以标准输入传送程序与私密参数。"""
import argparse,base64,json,pathlib,shlex,subprocess

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ssh-config',required=True,type=pathlib.Path)
    p.add_argument('--alias',default='pcvpn-autodl')
    p.add_argument('--ssh-executable',default='ssh.exe')
    p.add_argument('--remote-python',required=True)
    p.add_argument('--script',required=True,type=pathlib.Path)
    p.add_argument('--proxy-password-file',type=pathlib.Path)
    p.add_argument('--remote-port',default=17893,type=int)
    p.add_argument('--proxy-user',default='pcvpn')
    p.add_argument('--no-proxy',default='localhost,127.0.0.1,::1,.local,.autodl.pro,autodl.pro')
    p.add_argument('--support-dir',type=pathlib.Path)
    p.add_argument('--installer-file',type=pathlib.Path)
    p.add_argument('--release',default='latest')
    p.add_argument('--codex-home')
    p.add_argument('--download-direct',action='store_true')
    a=p.parse_args()
    if not 1<=a.remote_port<=65535:p.error('remote-port must be a valid TCP port')
    if not a.remote_python.startswith('/'):p.error('remote-python must be an absolute Linux path')
    if a.alias.startswith('-') or not a.alias:p.error('invalid SSH alias')
    data=dict(port=a.remote_port,username=a.proxy_user,no_proxy=a.no_proxy,release=a.release,download_direct=a.download_direct)
    if a.codex_home:data['codex_home']=a.codex_home
    if a.proxy_password_file:
        secret=a.proxy_password_file.read_text(encoding='utf-8-sig').strip()
        if not secret:p.error('empty proxy password file')
        data['proxy_password']=secret
    if a.support_dir:data['support_files']={n:(a.support_dir/n).read_text(encoding='utf-8-sig') for n in ['pcvpn.py','shell.sh']}
    if a.installer_file:data['codex_installer']=a.installer_file.read_text(encoding='utf-8-sig')
    prefix='import json,base64\nPAYLOAD=json.loads(base64.b64decode('+repr(base64.b64encode(json.dumps(data).encode()).decode())+'))\n'
    program=prefix+a.script.read_text(encoding='utf-8-sig')
    command=[a.ssh_executable,'-F',str(a.ssh_config.resolve()),'-o','StrictHostKeyChecking=yes','-o','BatchMode=yes',a.alias,shlex.quote(a.remote_python)+' -']
    return subprocess.run(command,input=program.encode('utf-8')).returncode

if __name__=='__main__':raise SystemExit(main())
