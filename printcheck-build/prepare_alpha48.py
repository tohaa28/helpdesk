#!/usr/bin/env python3
from pathlib import Path
import hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha47.py'),str(repo)],check=True)
src47=repo/'.printcheck-alpha47'; src48=repo/'.printcheck-alpha48'
if src48.exists(): shutil.rmtree(src48)
shutil.copytree(src47,src48)
patch=pb/'alpha48.patch'
if not patch.is_file() or patch.stat().st_size!=14413:
    raise RuntimeError('alpha48 patch missing or unexpected size')
subprocess.run(['patch','-p1','--batch','--forward','-i',str(patch)],cwd=src48,check=True)
if list(src48.rglob('*.rej')): raise RuntimeError('alpha48 patch rejects')
b=(src48/'app/build.gradle').read_text(encoding='utf-8')
state=(src48/'PRINTCHECK_CANONICAL_STATE.md').read_text(encoding='utf-8')
checks={
 'version':"versionCode 340048" in b and "versionName '3.4.0-alpha48'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'canonical state':'manual review instead of a false OK' in state and 'ready_layout.svg' in state,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha48 invariant failure: '+', '.join(bad))
signing=src48/'signing/printcheck-alpha-test.p12'; expected_sign='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha48 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected_sign: raise RuntimeError('alpha48 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha48 source')
