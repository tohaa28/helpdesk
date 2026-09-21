#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha53.py'),str(repo)],check=True)
src53=repo/'.printcheck-alpha53'; src54=repo/'.printcheck-alpha54'
if src54.exists(): shutil.rmtree(src54)
shutil.copytree(src53,src54)
enc=(pb/'alpha54_patch.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
expected='58cf98b73489d5805ff4d27d91256ba08ef3a16c3d04d50b2ac11b6e25826a3b'
if hashlib.sha256(patch).hexdigest()!=expected: raise RuntimeError('alpha54 patch sha mismatch')
pp=repo/'.alpha54.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src54,check=True)
finally: pp.unlink(missing_ok=True)
if list(src54.rglob('*.rej')): raise RuntimeError('alpha54 patch rejects')
subprocess.run([sys.executable,str(src54/'tests/audit_alpha54.py')],check=True)
signing=src54/'signing/printcheck-alpha-test.p12'
keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha54 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha: raise RuntimeError('alpha54 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha54 source')
