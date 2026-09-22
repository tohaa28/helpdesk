#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'

subprocess.run([sys.executable,str(pb/'prepare_alpha60.py'),str(repo)],check=True)
src60=repo/'.printcheck-alpha60'
src61=repo/'.printcheck-alpha61'
if src61.exists():
    shutil.rmtree(src61)
shutil.copytree(src60,src61)

parts=[pb/f'alpha61_patch_{i:02d}.b64' for i in range(4)]
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
expected='c1ef5e0e0fb36a47abb0f734256a0b63604ba54109591921965fda4d275794c9'
actual=hashlib.sha256(patch).hexdigest()
if actual!=expected:
    raise RuntimeError(f'alpha61 patch sha mismatch: {actual}')
pp=repo/'.alpha61.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src61,check=True)
finally:
    pp.unlink(missing_ok=True)

rejects=list(src61.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha61 patch rejects: '+', '.join(str(p.relative_to(src61)) for p in rejects))

subprocess.run([sys.executable,str(src61/'tests/audit_alpha61.py')],check=True)

signing=src61/'signing/printcheck-alpha-test.p12'
keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1':
        raise RuntimeError('alpha61 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha:
    raise RuntimeError('alpha61 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha61 source')
