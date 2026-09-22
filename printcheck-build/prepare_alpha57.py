#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

# Reconstruct the exact signed alpha56 first.
subprocess.run([sys.executable, str(pb / 'prepare_alpha56.py'), str(repo)], check=True)
src56 = repo / '.printcheck-alpha56'
src57 = repo / '.printcheck-alpha57'
if src57.exists():
    shutil.rmtree(src57)
shutil.copytree(src56, src57)

enc = (pb / 'alpha57_patch.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = '343e01c163a15091c58e1dd97ccac9d2767d41966ac1d4f586addd7227c930cf'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha57 patch sha mismatch: {actual}')

pp = repo / '.alpha57.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(pp)], cwd=src57, check=True)
finally:
    pp.unlink(missing_ok=True)

rejects = list(src57.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha57 patch rejects: ' + ', '.join(str(p.relative_to(src57)) for p in rejects))

subprocess.run([sys.executable, str(src57 / 'tests/audit_alpha57.py')], check=True)

signing = src57 / 'signing/printcheck-alpha-test.p12'
keysha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK') != '1':
        raise RuntimeError('alpha57 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest() != keysha:
    raise RuntimeError('alpha57 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha57 source')
