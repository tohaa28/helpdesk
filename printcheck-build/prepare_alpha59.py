#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, os, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

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

# CI correction 1: preserve the frozen integer alpha49/alpha51 measurement API
# while conservatively including fractional white PDF geometry.
fix2_enc = (pb / 'alpha59_ci_fix2.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
fix2_patch = gzip.decompress(base64.b64decode(fix2_enc, validate=True))
fix2_expected = '49a574280495e8ae38a2ddb0f5bfe6dc931be20a2f05f9da23439c5073cf0746'
fix2_actual = hashlib.sha256(fix2_patch).hexdigest()
if fix2_actual != fix2_expected:
    raise RuntimeError(f'alpha59 ci fix2 sha mismatch: {fix2_actual}')
fix2_pp = repo / '.alpha59-ci-fix2.patch'
fix2_pp.write_bytes(fix2_patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(fix2_pp)], cwd=src59, check=True)
finally:
    fix2_pp.unlink(missing_ok=True)

# CI correction 2: a white fill has no stroke expansion; only an actually
# painted white stroke contributes half its line width to the physical bbox.
fix3_enc = (pb / 'alpha59_ci_fix3.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b'')
fix3_patch = gzip.decompress(base64.b64decode(fix3_enc, validate=True))
fix3_expected = '9d86288ce38cb48066b67420bb6223e3a80228cf4763fdcdb824eaee54d44590'
fix3_actual = hashlib.sha256(fix3_patch).hexdigest()
if fix3_actual != fix3_expected:
    raise RuntimeError(f'alpha59 ci fix3 sha mismatch: {fix3_actual}')
fix3_pp = repo / '.alpha59-ci-fix3.patch'
fix3_pp.write_bytes(fix3_patch)
try:
    subprocess.run(['patch', '-p1', '--batch', '--forward', '-i', str(fix3_pp)], cwd=src59, check=True)
finally:
    fix3_pp.unlink(missing_ok=True)

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
