#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

# Reconstruct exact canonical alpha57 first.
subprocess.run([sys.executable, str(pb / 'prepare_alpha57.py'), str(repo)], check=True)
src57 = repo / '.printcheck-alpha57'
src58 = repo / '.printcheck-alpha58'
if src58.exists():
    shutil.rmtree(src58)
shutil.copytree(src57, src58)

# alpha58 patch is split only for transport. 02 is intentionally replaced by exact 02a/02b/02c.
parts = [
    pb / 'alpha58_patch_00.b64',
    pb / 'alpha58_patch_01.b64',
    pb / 'alpha58_patch_02a.b64',
    pb / 'alpha58_patch_02b.b64',
    pb / 'alpha58_patch_02c.b64',
    pb / 'alpha58_patch_03.b64',
    pb / 'alpha58_patch_04.b64',
    pb / 'alpha58_patch_05.b64',
]
enc = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = '71e6f3ce7cb6165a73a6340161642d717efdd68e9d3778b238a564980226f03a'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha58 patch sha mismatch: {actual}')

pp = repo / '.alpha58.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(pp)], cwd=src58, check=True)
finally:
    pp.unlink(missing_ok=True)

rejects = list(src58.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha58 patch rejects: ' + ', '.join(str(p.relative_to(src58)) for p in rejects))

subprocess.run([sys.executable, str(src58 / 'tests/audit_alpha58.py')], check=True)

signing = src58 / 'signing/printcheck-alpha-test.p12'
keysha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK') != '1':
        raise RuntimeError('alpha58 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest() != keysha:
    raise RuntimeError('alpha58 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha58 source')
