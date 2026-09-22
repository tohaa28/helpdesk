#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

# Reconstruct exact canonical alpha59 first.
subprocess.run([sys.executable, str(pb / 'prepare_alpha59.py'), str(repo)], check=True)
src59 = repo / '.printcheck-alpha59'
src60 = repo / '.printcheck-alpha60'
if src60.exists():
    shutil.rmtree(src60)
shutil.copytree(src59, src60)

parts = [pb / f'alpha60_patch_{i:02d}.b64' for i in range(4)]
enc = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = '03badc3215fac3cd7bd0b1b17e0cdbb65ed8b7b50b661bfbae245998aec76f15'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha60 patch sha mismatch: {actual}')

pp = repo / '.alpha60.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)], cwd=src60, check=True)
finally:
    pp.unlink(missing_ok=True)

rejects=list(src60.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha60 patch rejects: ' + ', '.join(str(p.relative_to(src60)) for p in rejects))

subprocess.run([sys.executable, str(src60/'tests/audit_alpha60.py')], check=True)

signing=src60/'signing/printcheck-alpha-test.p12'
keysha='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1':
        raise RuntimeError('alpha60 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=keysha:
    raise RuntimeError('alpha60 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha60 source')
