#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

# Reconstruct the exact canonical alpha55 first.
subprocess.run([sys.executable, str(pb / 'prepare_alpha55.py'), str(repo)], check=True)
src55 = repo / '.printcheck-alpha55'
src56 = repo / '.printcheck-alpha56'
if src56.exists():
    shutil.rmtree(src56)
shutil.copytree(src55, src56)

enc = (pb / 'alpha56_patch.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = '1cc9eefc8903368b8fb40daed7c1da1a5eb7719b19dff5cc5d6b0360b3f4a251'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha56 patch sha mismatch: {actual}')

pp = repo / '.alpha56.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(pp)], cwd=src56, check=True)
finally:
    pp.unlink(missing_ok=True)

rejects = list(src56.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha56 patch rejects: ' + ', '.join(str(p.relative_to(src56)) for p in rejects))

subprocess.run([sys.executable, str(src56 / 'tests/audit_alpha56.py')], check=True)

signing = src56 / 'signing/printcheck-alpha-test.p12'
keysha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK') != '1':
        raise RuntimeError('alpha56 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest() != keysha:
    raise RuntimeError('alpha56 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha56 source')
