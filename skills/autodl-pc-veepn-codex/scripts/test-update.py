"""实际执行官方升级，核对外层代理入口和既有配置。"""
import datetime,hashlib,json,os,pathlib,signal,subprocess

os.umask(0o077)
home=pathlib.Path.home();state=home/'.local/state/pcvpn';cli=home/'.local/bin/codex'
cfg=json.loads((home/'.config/pcvpn/config.json').read_text())
installation=json.loads((state/'codex-install.json').read_text())
codex_home=pathlib.Path(installation['codexHome'])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
protected=[cli,home/'.bashrc',home/'.profile',home/'.config/pcvpn/config.json',codex_home/'config.toml']
before={str(p):digest(p) for p in protected}
def version():return subprocess.run([str(cli),'--version'],capture_output=True,text=True,timeout=20).stdout.strip()
version_before=version();env=os.environ.copy();env['CODEX_NON_INTERACTIVE']='1'
proc=subprocess.Popen([str(cli),'update'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env,start_new_session=True)
timed_out=False
try:output=proc.communicate(input='',timeout=360)[0]
except subprocess.TimeoutExpired:
    timed_out=True;os.killpg(proc.pid,signal.SIGTERM)
    try:output=proc.communicate(timeout=5)[0]
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);output=proc.communicate()[0]
result=dict(time=datetime.datetime.now().astimezone().isoformat(),exit=proc.returncode,timedOut=timed_out,
            output=output.replace(cfg['password'],'<REDACTED>'),versionBefore=version_before,versionAfter=version(),
            wrapperUnchanged=digest(cli)==before[str(cli)],protectedConfigurationUnchanged=all(digest(p)==before[str(p)] for p in protected))
path=state/'codex-update-result.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2));path.chmod(0o600)
print(json.dumps(result,ensure_ascii=True))
raise SystemExit(0 if result['exit']==0 and result['wrapperUnchanged'] and result['protectedConfigurationUnchanged'] and not timed_out else 1)
