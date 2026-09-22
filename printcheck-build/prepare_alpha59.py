#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

# Reconstruct exact canonical alpha58 first.
subprocess.run([sys.executable, str(pb / 'prepare_alpha58.py'), str(repo)], check=True)
src58 = repo / '.printcheck-alpha58'
src59 = repo / '.printcheck-alpha59'
if src59.exists():
    shutil.rmtree(src59)
shutil.copytree(src58, src59)

parts = [pb / f'alpha59_patch_{i:02d}.b64' for i in range(6)]
enc = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
patch = gzip.decompress(base64.b64decode(enc, validate=True))
expected = 'd5c2e643a4770396e978451f358606b6e3c970adf009d32b243fe2d8f3f3a6e3'
actual = hashlib.sha256(patch).hexdigest()
if actual != expected:
    raise RuntimeError(f'alpha59 patch sha mismatch: {actual}')

pp = repo / '.alpha59.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(pp)], cwd=src59, check=True)
finally:
    pp.unlink(missing_ok=True)

# CI compile correction: preserve integer alpha49/51 measurement API while
# conservatively including fractional PDF white-object geometry.
fix_enc = (pb / 'alpha59_ci_fix.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
fix_patch = gzip.decompress(base64.b64decode(fix_enc, validate=True))
fix_expected = '35eadff2e7c527a1203c6e824fcf22b96dc46d4206d83dabc4e9289d4a40241e'
fix_actual = hashlib.sha256(fix_patch).hexdigest()
if fix_actual != fix_expected:
    raise RuntimeError(f'alpha59 ci fix sha mismatch: {fix_actual}')
fix_pp = repo / '.alpha59-ci-fix.patch'
fix_pp.write_bytes(fix_patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(fix_pp)], cwd=src59, check=True)
finally:
    fix_pp.unlink(missing_ok=True)

rejects = list(src59.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha59 patch rejects: ' + ', '.join(str(p.relative_to(src59)) for p in rejects))

subprocess.run([sys.executable, str(src59 / 'tests/audit_alpha59.py')], check=True)

signing = src59 / 'signing/printcheck-alpha-test.p12'
keysha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK') != '1':
        raise RuntimeError('alpha59 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest() != keysha:
    raise RuntimeError('alpha59 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha59 source')
