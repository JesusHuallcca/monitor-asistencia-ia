from pathlib import Path
import os,socket,subprocess,sys,time,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT)+os.pathsep+str(ROOT/'backend')
    cache=ROOT/'red_neuronal/.cache/integracion';cache.mkdir(parents=True,exist_ok=True)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env['PARTE6_TEST_URL']=f'http://127.0.0.1:{port}'
    with open(cache/'fixture-out.log','wb') as out,open(cache/'fixture-error.log','wb') as err:
        fixture=subprocess.Popen([sys.executable,'-m','uvicorn','red_neuronal.tests.system_fixture_app:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            for _ in range(120):
                if fixture.poll() is not None:raise RuntimeError('Fixture failed; see ignored fixture-error.log')
                try:
                    with urllib.request.urlopen(env['PARTE6_TEST_URL']+'/api/parte6/mode',timeout=2) as response:assert response.status==200
                    break
                except OSError:time.sleep(.5)
            return subprocess.run([sys.executable,'-m','red_neuronal.browser_system_check'],cwd=ROOT,env=env).returncode
        finally:
            if fixture.poll() is None:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(fixture.pid),'/T','/F'],capture_output=True)
                else:fixture.terminate()
                fixture.wait(timeout=15)
if __name__=='__main__':raise SystemExit(main())
