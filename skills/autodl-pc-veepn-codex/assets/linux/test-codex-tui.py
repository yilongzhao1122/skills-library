"""在独立工作区分配伪终端，验证默认交互界面中的模型回答。"""
import datetime,fcntl,json,os,pathlib,pty,re,select,signal,struct,subprocess,termios,time
def normalize_terminal_text(text):
    # 先清理终端控制与标题序列，再合并分段绘制产生的空白。
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    text=re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', '', text)
    return re.sub(r'\s+', '', text)

home=pathlib.Path.home();state=home/'.local/state/pcvpn';work=state/'tui-validation'
work.mkdir(parents=True,exist_ok=True,mode=0o700)
cli=home/'.local/bin/codex'
prompt='Reply with the string formed by joining PCVPN, TUI, OK using underscores. Do not use tools or read project files.'
trust='projects.'+json.dumps(str(work))+'.trust_level="trusted"'
command=[str(cli),'--sandbox','read-only','--ask-for-approval','on-request','-C',str(work),'-c',trust,prompt]
pid,fd=pty.fork()
if pid==0:
    os.environ['TERM']='xterm-256color';os.environ['COLUMNS']='140';os.environ['LINES']='40'
    os.chdir(work);os.execv(str(cli),command)
fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',40,140,0,0))
os.set_blocking(fd,False)
raw=bytearray();started=time.monotonic();answered=False;exited=False;child_status=None
try:
    while time.monotonic()-started<85:
        ready,_,_=select.select([fd],[],[],.2)
        if ready:
            try:data=os.read(fd,65536)
            except (OSError,BlockingIOError):data=b''
            if data:
                raw.extend(data)
                if b'\x1b[6n' in data:os.write(fd,b'\x1b[1;1R')
                if b'\x1b[c' in data:os.write(fd,b'\x1b[?1;2c')
                if b'\x1b[>c' in data:os.write(fd,b'\x1b[>0;136;0c')
                text=raw.decode('utf-8',errors='replace')
                stripped=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
                if 'PCVPN_TUI_OK' in normalize_terminal_text(text):
                    answered=True;break
                if 'no complete local package' in stripped or 'local Codex package is missing' in stripped:break
        finished,status=os.waitpid(pid,os.WNOHANG)
        if finished:
            exited=True;child_status=status;break
finally:
    if not exited:
        try:
            os.write(fd,b'\x03');time.sleep(.3);os.write(fd,b'\x03');time.sleep(.3)
            finished,status=os.waitpid(pid,os.WNOHANG)
            if finished:exited=True;child_status=status
        except (OSError,ChildProcessError):pass
    if not exited:
        try:os.kill(pid,signal.SIGTERM);os.waitpid(pid,0)
        except (ProcessLookupError,ChildProcessError):pass
    os.close(fd)
text=raw.decode('utf-8',errors='replace');screen=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
log=state/'codex-tui-validation.log';log.write_text(screen);os.chmod(log,0o600)
result=dict(time=datetime.datetime.now().astimezone().isoformat(),normalInteractiveCommand=True,defaultAlternateScreen=True,
            noDaemonFlagUsed=False,terminalAllocated=True,packageError='no complete local package' in screen,
            tuiVisible=any(word in screen for word in ['OpenAI Codex','>_ Codex','Welcome to Codex']),
            modelAnswerObserved=answered,expectedAnswer='PCVPN_TUI_OK',seconds=round(time.monotonic()-started,2),
            log=str(log),workspace=str(work),terminalMatch='ANSI stripped, whitespace normalized')
path=state/'codex-tui-test-result.json';path.write_text(json.dumps(result,indent=2));os.chmod(path,0o600)
print(json.dumps(result),flush=True)
if not answered:
    # Test-owned screen only; never print auth.json, process environment, or arbitrary project content.
    print(json.dumps(dict(screenTail=screen[-1800:]),ensure_ascii=True),flush=True)
raise SystemExit(0 if answered and not result['packageError'] else 1)
