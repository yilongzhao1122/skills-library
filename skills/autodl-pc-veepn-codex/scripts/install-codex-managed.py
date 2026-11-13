"""使用本次审阅的官方安装器安装完整包，并保留个人代理入口。"""
import datetime,hashlib,json,os,pathlib,shlex,shutil,signal,subprocess,sys
home=pathlib.Path.home().resolve();os.umask(0o077)
codex_home=pathlib.Path(PAYLOAD.get('codex_home',str(home/'.codex'))).expanduser().resolve()
if os.path.commonpath([str(home),str(codex_home)])!=str(home):raise RuntimeError('CODEX_HOME must be in the audited private HOME')
state=home/'.local/state/pcvpn';backup=state/'backups'/('codex-managed-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True,mode=0o700)
cli=home/'.local/bin/codex';bindir=home/'.local/share/pcvpn/codex-standalone-bin'
if cli.is_symlink():raise RuntimeError('Existing Codex is a symlink; inspect and back it up before replacing it')
for path in [cli,bindir,codex_home]:
    if os.path.commonpath([str(home),str(path.resolve())])!=str(home):raise RuntimeError('Installation path escaped private HOME')
cfg=json.loads((home/'.config/pcvpn/config.json').read_text())
protected=[home/'.bashrc',home/'.profile',home/'.config/pcvpn/config.json',codex_home/'config.toml']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
before={str(p):digest(p) for p in protected}
auth_before=(codex_home/'auth.json').exists()
if cli.exists():shutil.copy2(cli,backup/'codex-launcher')
record=state/'codex-install.json'
if record.exists():shutil.copy2(record,backup/'codex-install.json')
installer=backup/'official-install.sh';installer.write_text(PAYLOAD['codex_installer']);installer.chmod(0o700)
bindir.mkdir(parents=True,exist_ok=True,mode=0o700);codex_home.mkdir(parents=True,exist_ok=True,mode=0o700);codex_home.chmod(0o700)
# The proxy runner module is the same module installed by install-user-environment.
sys.path.insert(0,str(home/'.local/lib/pcvpn'));import pcvpn
env=pcvpn.environment(cfg)
if PAYLOAD.get('download_direct'):
    for key in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(key,None)
env.update(CODEX_HOME=str(codex_home),CODEX_INSTALL_DIR=str(bindir),CODEX_NON_INTERACTIVE='1',PATH=str(bindir)+':'+str(pathlib.Path(sys.executable).parent)+':'+env.get('PATH','/usr/bin:/bin'))
log=backup/'install.log'
with log.open('w') as output:
    proc=subprocess.Popen(['/bin/sh',str(installer),'--release',PAYLOAD.get('release','latest')],env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    try:proc.wait(timeout=900)
    except subprocess.TimeoutExpired:
        # Only the new installer process group, never unrelated Codex or SSH.
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait()
        raise RuntimeError('Official installer timed out; its own process group was stopped. Inspect the private install log before retrying.')
if proc.returncode:
    print(json.dumps(dict(installerExit=proc.returncode,log=str(log))))
    raise SystemExit(1)
target=bindir/'codex'
if not target.exists():raise RuntimeError('Official command missing; old outer wrapper was not overwritten')
package_root=target.resolve().parent.parent
if not (package_root/'codex-package.json').is_file():raise RuntimeError('Expected complete official package; inspect current installer before adapting')
body='#!/bin/bash\n# Managed official Codex, with a separate personal proxy wrapper.\n'
body+='export CODEX_HOME='+shlex.quote(str(codex_home))+'\nexport CODEX_INSTALL_DIR='+shlex.quote(str(bindir))+'\n'
body+='export PATH="$HOME/.local/bin:$PATH:$CODEX_INSTALL_DIR":'+shlex.quote(str(pathlib.Path(sys.executable).parent))+'\n'
body+='if [[ ${PCVPN_DISABLE:-0} == 1 ]]; then exec '+shlex.quote(str(target))+' "$@"; fi\n'
body+='exec "$HOME/.local/bin/pcvpn-run" '+shlex.quote(str(target))+' "$@"\n'
cli.parent.mkdir(parents=True,exist_ok=True,mode=0o700);cli.write_text(body);cli.chmod(0o700)
if not all(digest(p)==before[str(p)] for p in protected):raise RuntimeError('Existing configuration changed unexpectedly; inspect backup and installer log')
if auth_before and not (codex_home/'auth.json').exists():raise RuntimeError('Existing auth file unexpectedly disappeared')
version=subprocess.run([str(cli),'--version'],capture_output=True,text=True,timeout=25)
doctor=subprocess.run([str(cli),'doctor','--json'],capture_output=True,text=True,timeout=60)
health=json.loads(doctor.stdout);installation=health['checks']['installation']
(state/'codex-doctor.json').write_text(json.dumps(health,indent=2))
failed_checks=[key for key,value in health.get('checks',{}).items() if value.get('status')=='fail']
pending_login=failed_checks==['auth.credentials'] and not auth_before
installation_ok=version.returncode==0 and installation.get('status')=='ok' and 'standalone' in str(installation).lower()
result=dict(pendingLogin=pending_login,installationPassed=installation_ok,time=datetime.datetime.now().astimezone().isoformat(),version=version.stdout.strip(),binary=str(target.resolve()),packageRoot=str(package_root),managedCommand=str(target),codexHome=str(codex_home),managedBy='official-standalone',completePackage=True,backup=str(backup),installerSHA256=digest(installer),doctorStatus=health.get('overallStatus'),installation=installation.get('details',{}),protectedConfigurationUnchanged=True,existingAuthPreserved=not auth_before or (codex_home/'auth.json').exists())
record.write_text(json.dumps(result,indent=2));record.chmod(0o600)
print(json.dumps(result))
raise SystemExit(0 if installation_ok and (doctor.returncode==0 or pending_login) else 1)
