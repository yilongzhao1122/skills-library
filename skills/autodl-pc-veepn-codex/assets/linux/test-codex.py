import datetime,json,os,pathlib,subprocess
home=pathlib.Path.home();state=home/'.local/state/pcvpn';work=state/'empty-workspace'
work.mkdir(parents=True,exist_ok=True,mode=0o700)
cli=home/'.local/bin/codex'
status=subprocess.run([str(cli),'login','status'],capture_output=True,text=True,timeout=20)
auth=(status.stdout+status.stderr).strip()
if status.returncode!=0 or 'chatgpt' not in auth.lower():
    print(json.dumps(dict(authentication=auth,loginStatusExit=status.returncode,modelRequestAttempted=False)))
    raise SystemExit(1)
doctor_process=subprocess.run([str(cli),'doctor','--json'],capture_output=True,text=True,timeout=60)
try:doctor=json.loads(doctor_process.stdout)
except ValueError:doctor={}
if doctor:
    doctor_path=state/'codex-doctor.json';doctor_path.write_text(json.dumps(doctor,indent=2));os.chmod(doctor_path,0o600)
if doctor_process.returncode!=0:
    print(json.dumps(dict(authentication=auth,doctorExit=doctor_process.returncode,doctorStatus=doctor.get('overallStatus'),modelRequestAttempted=False,error='Codex local installation/runtime health check failed.')))
    raise SystemExit(1)
final=state/'codex-last-message.txt'
if final.exists():final.unlink()
prompt='Reply exactly PCVPN_AUTODL_OK. Do not use tools. Do not read or change project files.'
command=[str(cli),'exec','--skip-git-repo-check','--sandbox','read-only','--ephemeral','--json','--output-last-message',str(final),'-']
config=json.loads((home/'.config/pcvpn/config.json').read_text())
try:
    proc=subprocess.run(command,input=prompt,text=True,capture_output=True,cwd=work,timeout=150)
except subprocess.TimeoutExpired:
    print(json.dumps(dict(authentication=auth,modelRequestAttempted=True,error='Model request timed out after 150 seconds.')))
    raise SystemExit(1)
events=[];usage={};errors=[];tools=[]
for line in proc.stdout.splitlines():
    try:event=json.loads(line)
    except ValueError:continue
    events.append(event.get('type'))
    if event.get('type')=='turn.completed':usage=event.get('usage',{})
    if event.get('type') in ['error','turn.failed']:errors.append(event.get('message') or event.get('error'))
    item=event.get('item',{})
    if item.get('type') in ['command_execution','file_change','mcp_tool_call','web_search']:tools.append(item.get('type'))
message=final.read_text().strip() if final.exists() else ''
stderr=proc.stderr.replace(config['password'],'<REDACTED>')[-1200:]
result=dict(time=datetime.datetime.now().astimezone().isoformat(),authentication=auth,cliVersion=subprocess.run([str(cli),'--version'],capture_output=True,text=True).stdout.strip(),
            inferenceExit=proc.returncode,finalMessage=message,turnCompleted='turn.completed' in events,usage=usage,toolCalls=tools,errors=errors,
            stderr=stderr,proxyEndpoint='127.0.0.1:'+str(config['port']),workspace=str(work),doctorExit=doctor_process.returncode,doctorStatus=doctor.get('overallStatus'))
path=state/'codex-test-result.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2));os.chmod(path,0o600)
if final.exists():os.chmod(final,0o600)
print(json.dumps(result,ensure_ascii=True),flush=True)
raise SystemExit(0 if proc.returncode==0 and result['turnCompleted'] and message=='PCVPN_AUTODL_OK' and not tools else 1)
