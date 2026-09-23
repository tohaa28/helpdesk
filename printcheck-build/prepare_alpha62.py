#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha61.py'),str(repo)],check=True)
src61=repo/'.printcheck-alpha61'
src62=repo/'.printcheck-alpha62'
if src62.exists(): shutil.rmtree(src62)
shutil.copytree(src61,src62)

parts=[pb/f'alpha62_exact_{i:02d}.b64' for i in range(12)]
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
expected='1e68d4af050000eed0e1dd4f8b4762f2a310b78c079dab7f81115b7a1e9843bc'
actual=hashlib.sha256(patch).hexdigest()
if actual!=expected: raise RuntimeError(f'alpha62 patch sha mismatch: {actual}')
pp=repo/'.alpha62.patch';pp.write_bytes(patch)
try:
 subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src62,check=True)
finally:
 pp.unlink(missing_ok=True)
rejects=list(src62.rglob('*.rej'))
if rejects: raise RuntimeError('alpha62 patch rejects: '+', '.join(str(x.relative_to(src62)) for x in rejects))
subprocess.run([sys.executable,str(src62/'tests/audit_alpha62.py')],check=True)

signing=src62/'signing/printcheck-alpha-test.p12'
keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
 if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha62 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha:
 raise RuntimeError('alpha62 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha62 source')
