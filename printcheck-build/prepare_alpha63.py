#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha62.py'),str(repo)],check=True)
src62=repo/'.printcheck-alpha62';src63=repo/'.printcheck-alpha63'
if src63.exists(): shutil.rmtree(src63)
shutil.copytree(src62,src63)
parts=[pb/f'alpha63_patch_{i:02d}.b64' for i in range(14)]
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
expected='b07daad1742c9ac1ba17f7e700876e88df7309633002a48bb0f71c46adfc4b79'
actual=hashlib.sha256(patch).hexdigest()
if actual!=expected: raise RuntimeError(f'alpha63 patch sha mismatch: {actual}')
pp=repo/'.alpha63.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src63,check=True)
finally: pp.unlink(missing_ok=True)
rejects=list(src63.rglob('*.rej'))
if rejects: raise RuntimeError('alpha63 patch rejects: '+', '.join(str(x.relative_to(src63)) for x in rejects))
subprocess.run([sys.executable,str(src63/'tests/audit_alpha63.py')],check=True)
signing=src63/'signing/printcheck-alpha-test.p12';keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
 if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha63 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha: raise RuntimeError('alpha63 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha63 source')
