#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha9.py'), str(repo)], check=True)
src9 = repo / '.printcheck-alpha9'
src10 = repo / '.printcheck-alpha10'
if src10.exists():
    shutil.rmtree(src10)
shutil.copytree(src9, src10)

raw = base64.b64decode((pb / 'pc340a10.patch.gz.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b''))
digest = hashlib.sha256(raw).hexdigest()
expected = 'a2b8d0d85ea21a5bdd4c6054b3fb4ad2eb70149bec3249797845a553a9f00843'
if digest != expected:
    raise RuntimeError(f'alpha10 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src10, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha10 patch failed')
rejects = list(src10.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha10 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src10 / 'app/build.gradle').read_text(encoding='utf-8')
if "versionName '3.4.0-alpha10'" not in gradle or 'versionCode 340010' not in gradle:
    raise RuntimeError('alpha10 version verification failed')
main = (src10 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
for token in ['Проверить все','runBatch(','publishPdf(','batch_pdf_reports_v1']:
    if token not in main:
        raise RuntimeError('alpha10 verification missing: ' + token)
if not (src10 / 'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').is_file():
    raise RuntimeError('PdfReportWriter missing')

print('Prepared', src10)
