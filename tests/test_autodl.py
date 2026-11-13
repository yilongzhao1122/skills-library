"""在临时主目录中检查凭据传递、环境恢复和安装阶段，使用模拟程序响应。"""
import ast,json,os,pathlib,socket,subprocess,sys,tempfile,unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]/'skills/autodl-pc-veepn-codex'
class AutoDLTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='skills-library-')
        self.home=pathlib.Path(self.tmp.name)
        self.env=os.environ.copy();self.env.update(HOME=str(self.home),CODEX_HOME=str(self.home/'.codex'),PATH='/usr/bin:/bin')
        (self.home/'.bashrc').write_text('# preserved user setup\n')
        (self.home/'.profile').write_text('# preserved profile\n')
        self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen()
        self.port=self.listener.getsockname()[1]
        self.payload=dict(port=self.port,username='pcvpn',proxy_password='fixture-password',no_proxy='localhost,127.0.0.1',
                          support_files={n:(ROOT/'assets/linux'/n).read_text() for n in ['pcvpn.py','shell.sh']})
    def tearDown(self):
        self.listener.close();self.tmp.cleanup()
    def remote(self,file,payload=None,env=None):
        code='PAYLOAD='+repr(payload or self.payload)+'\n'+(ROOT/file).read_text()
        return subprocess.run([sys.executable,'-'],input=code,text=True,capture_output=True,env=env or self.env,cwd=self.home,timeout=30)
    def install_environment(self):
        p=self.remote('scripts/install-user-environment.py');self.assertEqual(p.returncode,0,p.stderr)
    def test_proxy_roundtrip_and_permissions(self):
        self.install_environment()
        command=r'''
set -e
source "$HOME/.config/pcvpn/shell.sh"
export HTTP_PROXY=original_value
unset HTTPS_PROXY
pcvpn-on >/dev/null
pcvpn-on >/dev/null
[[ -v HTTPS_PROXY ]]
pcvpn-off >/dev/null
[[ $HTTP_PROXY == original_value && ! -v HTTPS_PROXY ]]
pcvpn-run /usr/bin/python3 -c 'import os; assert "127.0.0.1" in os.environ["HTTPS_PROXY"]'
[[ $HTTP_PROXY == original_value && ! -v HTTPS_PROXY ]]
'''
        p=subprocess.run(['/bin/bash','--noprofile','--norc','-c',command],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual((self.home/'.config/pcvpn/config.json').stat().st_mode&0o777,0o600)
        self.assertEqual((self.home/'.config/pcvpn').stat().st_mode&0o777,0o700)
        self.assertTrue((self.home/'.bashrc').read_text().startswith('# preserved user setup\n'))
        before=(self.home/'.bashrc').read_text();self.install_environment()
        self.assertEqual((self.home/'.bashrc').read_text(),before)
    def test_exposed_listener_preserves_existing_files(self):
        self.listener.close();self.listener=socket.socket();self.listener.bind(('0.0.0.0',0));self.listener.listen()
        self.payload['port']=self.listener.getsockname()[1]
        p=self.remote('scripts/install-user-environment.py')
        self.assertNotEqual(p.returncode,0)
        self.assertFalse((self.home/'.config/pcvpn/config.json').exists())
        self.assertEqual((self.home/'.bashrc').read_text(),'# preserved user setup\n')
    def fake_installer(self):
        fake=r'''#!/usr/bin/python3
import json,os,sys
if '--version' in sys.argv:print('codex-cli 1.0.0');raise SystemExit(0)
if sys.argv[1:]==['login','status']:print('Logged in using ChatGPT');raise SystemExit(0)
if sys.argv[1:]==['update']:print('fixture update completed');raise SystemExit(0)
if sys.argv[1:]==['doctor','--json']:
 checks={'installation':{'status':'ok','details':{'context':'standalone'}}}
 if os.environ.get('CASE') in ['pending','existing']:checks['auth.credentials']={'status':'fail'}
 if os.environ.get('CASE')=='broken':checks['config.load']={'status':'fail'}
 failed=any(v['status']=='fail' for v in checks.values())
 print(json.dumps({'overallStatus':'fail' if failed else 'ok','checks':checks}));raise SystemExit(1 if failed else 0)
'''
        return """#!/bin/sh
set -eu
package="$CODEX_HOME/packages/standalone/releases/1.0.0-linux"
mkdir -p "$package/bin" "$CODEX_INSTALL_DIR"
cat > "$package/bin/codex" <<'FIXTURE'
"""+fake+"""FIXTURE
chmod 700 "$package/bin/codex"
printf '{}' > "$package/codex-package.json"
ln -s "$package/bin/codex" "$CODEX_INSTALL_DIR/codex"
"""
    def installer_case(self,case):
        self.install_environment();env=self.env.copy();env['CASE']=case
        if case=='existing':
            p=self.home/'.codex';p.mkdir();(p/'auth.json').write_text('{}')
        return self.remote('scripts/install-codex-managed.py',dict(codex_installer=self.fake_installer(),release='latest'),env)
    def test_new_install_reports_pending_login(self):
        p=self.installer_case('pending');self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout);self.assertTrue(r['pendingLogin']);self.assertTrue(r['installationPassed'])
    def test_authenticated_install_passes(self):
        p=self.installer_case('healthy');self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['doctorStatus'],'ok')
    def test_configuration_failure_remains_actionable(self):
        p=self.installer_case('broken');self.assertEqual(p.returncode,1,p.stderr)
        self.assertFalse(json.loads(p.stdout)['pendingLogin'])
    def test_existing_auth_is_preserved(self):
        p=self.installer_case('existing');self.assertEqual(p.returncode,1,p.stderr)
        self.assertFalse(json.loads(p.stdout)['pendingLogin'])
        self.assertEqual((self.home/'.codex/auth.json').read_text(),'{}')
    def test_terminal_control_sequences(self):
        source=ast.parse((ROOT/'assets/linux/test-codex-tui.py').read_text())
        function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_terminal_text')
        import re
        scope={'re':re};exec(compile(ast.Module(body=[function],type_ignores=[]),'<terminal>','exec'),scope)
        normalize=scope['normalize_terminal_text']
        self.assertIn('PCVPN_TUI_OK',normalize('\x1b[32mPC VPN_\x1b]0;task\x07TUI_OK\x1b[0m'))
        self.assertNotIn('PCVPN_TUI_OK',normalize('joining PCVPN, TUI, OK using underscores'))
    def test_model_request_requires_chatgpt_login(self):
        cli=self.home/'.local/bin/codex';cli.parent.mkdir(parents=True)
        cli.write_text('#!/usr/bin/python3\nprint("Logged in using API key")\n');cli.chmod(0o700)
        p=self.remote('assets/linux/test-codex.py');self.assertEqual(p.returncode,1,p.stderr)
        self.assertFalse(json.loads(p.stdout)['modelRequestAttempted'])
    def test_update_preserves_wrapper(self):
        p=self.installer_case('healthy');self.assertEqual(p.returncode,0,p.stderr)
        before=(self.home/'.local/bin/codex').read_text()
        p=self.remote('scripts/test-update.py');self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout);self.assertTrue(r['wrapperUnchanged']);self.assertTrue(r['protectedConfigurationUnchanged'])
        self.assertEqual((self.home/'.local/bin/codex').read_text(),before)
    def test_deployment_checks_and_recorded_results(self):
        p=self.installer_case('healthy');self.assertEqual(p.returncode,0,p.stderr)
        rows=[dict(target=url,exit=0,metrics=dict(http=200,connect=200,tls=0,seconds=0.01),body='198.51.100.20') for url in ['https://api.ipify.org','https://www.google.com','https://github.com','https://chatgpt.com']]
        rows.append(dict(target='https://api.ipify.org',exit=56,metrics=dict(http=0,connect=407,tls=0,seconds=0.01)))
        cli=self.home/'.local/bin/pcvpn-test';cli.write_text('#!/usr/bin/python3\nimport json\nfor row in '+repr(rows)+':print(json.dumps(row))\n');cli.chmod(0o700)
        p=self.remote('scripts/test-deployment.py');self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout);self.assertTrue(r['liveChecksPassed']);self.assertIsNone(r['recordedChecks']['codex-test-result.json'])
        payload=dict(self.payload);payload['port']=1
        p=self.remote('scripts/test-deployment.py',payload);self.assertEqual(p.returncode,1,p.stderr)
    def test_default_interactive_pty(self):
        cli=self.home/'.local/bin/codex';cli.parent.mkdir(parents=True)
        cli.write_text('#!/usr/bin/python3\nimport sys,time\nprint("OpenAI Codex\\n\\x1b[32mPC VPN_\\x1b]0;task\\x07TUI_OK",flush=True)\ntime.sleep(3)\n');cli.chmod(0o700)
        p=self.remote('assets/linux/test-codex-tui.py');self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout);self.assertTrue(r['terminalAllocated']);self.assertTrue(r['defaultAlternateScreen']);self.assertTrue(r['modelAnswerObserved']);self.assertFalse(r['noDaemonFlagUsed'])
    def test_secret_travels_only_on_stdin(self):
        password=self.home/'fixture.txt';password.write_text('fixture-password')
        ssh=self.home/'fake-ssh';capture=self.home/'capture.json'
        ssh.write_text('#!/usr/bin/python3\nimport sys,json,pathlib\npathlib.Path('+repr(str(capture))+').write_text(json.dumps({"argv":sys.argv,"stdin":sys.stdin.read()}))\n');ssh.chmod(0o700)
        script=self.home/'remote.py';script.write_text('print("fixture")\n')
        config=self.home/'config';config.write_text('Host fixture\n')
        p=subprocess.run([sys.executable,str(ROOT/'scripts/send-remote.py'),'--ssh-config',str(config),'--alias','fixture','--ssh-executable',str(ssh),'--remote-python','/usr/bin/python3','--script',str(script),'--proxy-password-file',str(password)],capture_output=True,text=True,env=self.env)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(capture.read_text());self.assertNotIn('fixture-password',' '.join(r['argv']))
        self.assertIn('StrictHostKeyChecking=yes',r['argv'])
        namespace={};exec(r['stdin'].split('print("fixture")')[0],namespace)
        self.assertEqual(namespace['PAYLOAD']['proxy_password'],'fixture-password')

if __name__=='__main__':unittest.main(verbosity=2)
