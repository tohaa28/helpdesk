#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha52.py'),str(repo)],check=True)
src52=repo/'.printcheck-alpha52'; src53=repo/'.printcheck-alpha53'
if src53.exists(): shutil.rmtree(src53)
shutil.copytree(src52,src53)
enc=(pb/'alpha53_patch.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
expected='b0bb1cda40c8708a289a0f6aac4258d47b3e1189fe1cb671d4c0b02a2730cd22'
if hashlib.sha256(patch).hexdigest()!=expected: raise RuntimeError('alpha53 patch sha mismatch')
pp=repo/'.alpha53.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src53,check=True)
finally: pp.unlink(missing_ok=True)
if list(src53.rglob('*.rej')): raise RuntimeError('alpha53 patch rejects')
subprocess.run([sys.executable,str(src53/'tests/audit_alpha53.py')],check=True)
signing=src53/'signing/printcheck-alpha-test.p12'
keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha53 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha: raise RuntimeError('alpha53 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha53 source')
