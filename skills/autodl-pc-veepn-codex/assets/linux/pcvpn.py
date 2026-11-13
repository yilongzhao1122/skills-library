"""按目标子进程启用个人代理，并输出脱敏的网页请求与证书校验结果。"""
import json,os,pathlib,subprocess,sys,urllib.parse
HOME=pathlib.Path.home()
CONFIG=HOME/'.config/pcvpn/config.json'
def settings():
    return json.loads(CONFIG.read_text())
def proxy_url(config):
    return 'http://'+urllib.parse.quote(config['username'],safe='')+':'+urllib.parse.quote(config['password'],safe='')+'@127.0.0.1:'+str(config['port'])
def environment(config):
    env=os.environ.copy(); url=proxy_url(config)
    for key in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy','ALL_PROXY','all_proxy']:env[key]=url
    for key in ['NO_PROXY','no_proxy']:env[key]=config['no_proxy']
    return env
def check(url,config,auth=True,direct=False,keep=False):
    lines=['silent','show-error','connect-timeout = 8','max-time = 25','url = '+json.dumps(url)]
    if direct:lines += ['noproxy = "*"','max-time = 8']
    else:
        lines += ['noproxy = "no-match.invalid"','proxy = "http://127.0.0.1:'+str(config['port'])+'"']
        if auth:lines += ['proxy-basic','proxy-user = '+json.dumps(config['username']+':'+config['password'])]
    if not keep:lines += ['output = "/dev/null"']
    # Quote curl's 000 status before strict JSON parsing on failed CONNECT.
    metrics='{"http":"%{http_code}","connect":"%{http_connect}","tls":"%{ssl_verify_result}","seconds":"%{time_total}"}'
    lines += ['write-out = '+json.dumps('\n'+metrics)]
    proc=subprocess.run(['curl','-q','--config','-'],input='\n'.join(lines)+'\n',text=True,capture_output=True,timeout=32)
    body,_,raw=proc.stdout.strip().rpartition('\n')
    try:
        parsed=json.loads(raw)
        details={key:(float(value) if key=='seconds' else int(value)) for key,value in parsed.items()}
    except ValueError:details={}
    error=proc.stderr.replace(config['password'],'<REDACTED>').strip()
    result=dict(target=url,direct=direct,authenticated=auth and not direct,exit=proc.returncode,metrics=details,error=error)
    if keep:result['body']=body.strip()[:250]
    return result
def main():
    config=settings(); name=pathlib.Path(sys.argv[0]).name
    if name=='pcvpn-run':
        command=sys.argv[1:]
        if command[:1]==['--']:command=command[1:]
        if not command:raise SystemExit('Usage: pcvpn-run COMMAND [ARG...]')
        os.execvpe(command[0],command,environment(config))
    records=[]
    for target in ['https://api.ipify.org','https://www.google.com','https://github.com','https://chatgpt.com']:
        row=check(target,config,keep=target.endswith('ipify.org'));records.append(row);print(json.dumps(row),flush=True)
    row=check('https://api.ipify.org',config,auth=False);records.append(row);print(json.dumps(row),flush=True)
    if '--direct' in sys.argv:
        row=check('https://api.ipify.org',config,direct=True,keep=True);records.append(row);print(json.dumps(row),flush=True)
    state=HOME/'.local/state/pcvpn';state.mkdir(parents=True,exist_ok=True,mode=0o700)
    (state/'last-test.json').write_text(json.dumps(records,indent=2));os.chmod(state/'last-test.json',0o600)
    good=all(r['exit']==0 and r['metrics'].get('http')==200 and r['metrics'].get('connect')==200 and r['metrics'].get('tls')==0 for r in records[:4])
    good=good and records[4]['metrics'].get('connect')==407
    raise SystemExit(0 if good else 1)
if __name__=='__main__':main()
