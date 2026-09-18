#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha10.py'), str(repo)], check=True)
src10 = repo / '.printcheck-alpha10'
src11 = repo / '.printcheck-alpha11'
if src11.exists():
    shutil.rmtree(src11)
shutil.copytree(src10, src11)

raw = base64.b64decode((pb / 'pc340a11.patch.gz.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b''))
digest = hashlib.sha256(raw).hexdigest()
expected = '3db9d6d392dc4f3022af7f544bfb03d712f9771c8c8b14d4c19b4f4a5011e6b9'
if digest != expected:
    raise RuntimeError(f'alpha11 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src11, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha11 patch failed')
rejects = list(src11.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha11 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src11 / 'app/build.gradle').read_text(encoding='utf-8')
if "versionName '3.4.0-alpha11'" not in gradle or 'versionCode 340011' not in gradle:
    raise RuntimeError('alpha11 version verification failed')
main = (src11 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
for token in ['same_page_mask_registration_v1','constructor_aux_filter_v1','conditional_rules_v1','Preflight 3.4 alpha11']:
    if token not in main:
        raise RuntimeError('alpha11 verification missing: ' + token)

print('Prepared', src11)
