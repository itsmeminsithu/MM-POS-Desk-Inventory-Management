#!/usr/bin/env python3
"""MM POS Desk launcher. Copyright (c) 2026 Min SiThu (itsmeminsithu). MIT."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
ROOT=Path(__file__).resolve().parent

def main():
    if sys.version_info<(3,11):
        print('Please install Python 3.11 or newer from https://www.python.org/downloads/');return 1
    os.chdir(ROOT)
    env=ROOT/'.venv';python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():
        print('Preparing your Python environment…',flush=True);venv.EnvBuilder(with_pip=True).create(env)
    def run(*args):subprocess.run([str(python),*args],check=True)
    fingerprint=hashlib.sha256((ROOT/'requirements.txt').read_bytes()).hexdigest()
    marker=env/'requirements.sha256'
    if not marker.exists() or marker.read_text()!=fingerprint:
        print('Installing dependencies. Internet is needed for this first step.',flush=True)
        run('-m','pip','install','-r','requirements.txt');marker.write_text(fingerprint)
    run('manage.py','migrate','--noinput');run('manage.py','check')
    if '--check' in sys.argv:return 0
    port=int(os.environ.get('POS_PORT','8001'))
    if not 1024<=port<=65535:raise ValueError('POS_PORT must be between 1024 and 65535.')
    url=f'http://127.0.0.1:{port}/'
    print(f'\nMM POS Desk Inventory Management\nOpen {url}\nFirst visit: choose Create business and register in your browser.\nKeep this Terminal open. Press Control+C to stop.\n',flush=True)
    # Open only after the server answers; no terminal account-creation prompt.
    def open_browser():
        for _ in range(40):
            try:
                with urllib.request.urlopen(url,timeout=1) as response:
                    if response.status==200:webbrowser.open(url);return
            except Exception:time.sleep(.5)
    if '--no-browser' not in sys.argv:threading.Thread(target=open_browser,daemon=True).start()
    run('manage.py','runserver',f'127.0.0.1:{port}','--noreload')
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('\nMM POS Desk stopped.')
    except (subprocess.CalledProcessError,ValueError,OSError) as error:
        print(f'Could not start: {error}\nCheck the message above. If port 8001 is occupied, use POS_PORT=8002 python3 start.py.');sys.exit(1)
