#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha54.py'), str(repo)], check=True)
src54 = repo / '.printcheck-alpha54'
src55 = repo / '.printcheck-alpha55'
if src55.exists():
    shutil.rmtree(src55)
shutil.copytree(src54, src55)

# Main alpha55 modular-geometry patch.
parts = [pb / f'alpha55_patch_{i:02d}.b64' for i in range(4)]
enc = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = 'a5f1e56d4059826426725a9c96857d1ed95c2bb7143c8bfe7108a28a06aa92c6'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha55 patch sha mismatch: {actual}')

pp = repo / '.alpha55.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(pp)], cwd=src55, check=True)
finally:
    pp.unlink(missing_ok=True)

# CI-discovered compatibility correction:
# - preserve fail-closed ApplicationFieldBinding behavior from alpha54;
# - restore the legacy strict detectProductionField facade for regression tests;
# - keep alpha49/alpha51 field measurement in the new geometry modules.
fix_enc = (pb / 'alpha55_ci_fix.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
fix_patch = gzip.decompress(base64.b64decode(fix_enc, validate=True))
fix_pp = repo / '.alpha55-ci-fix.patch'
fix_pp.write_bytes(fix_patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(fix_pp)], cwd=src55, check=True)
finally:
    fix_pp.unlink(missing_ok=True)

if list(src55.rglob('*.rej')):
    raise RuntimeError('alpha55 patch rejects')

subprocess.run([sys.executable, str(src55 / 'tests/audit_alpha55.py')], check=True)

signing = src55 / 'signing/printcheck-alpha-test.p12'
keysha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK') != '1':
        raise RuntimeError('alpha55 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest() != keysha:
    raise RuntimeError('alpha55 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha55 source')
