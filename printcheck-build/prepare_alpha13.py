#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha12.py'), str(repo)], check=True)
src12 = repo / '.printcheck-alpha12'
src13 = repo / '.printcheck-alpha13'
if src13.exists():
    shutil.rmtree(src13)
shutil.copytree(src12, src13)

parts = sorted(pb.glob('pc340a13.b64.part*'))
if not parts:
    raise RuntimeError('alpha13 patch chunks missing')
encoded = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
raw = base64.b64decode(encoded)
digest = hashlib.sha256(raw).hexdigest()
expected = '89f445f1610edc5303c7272b44e9c602bb11ac095bd2827aac768cfecf378c06'
if digest != expected:
    raise RuntimeError(f'alpha13 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src13, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha13 patch failed')
rejects = list(src13.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha13 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src13 / 'app/build.gradle').read_text(encoding='utf-8')
if "versionName '3.4.0-alpha13'" not in gradle or 'versionCode 340013' not in gradle:
    raise RuntimeError('alpha13 version verification failed')
main = (src13 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
view = (src13 / 'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
for token in ['compact_controls_v1','diagnostics_export_name_v1','Сохранить диагностику','PrintCheck_diagnostics_']:
    if token not in main:
        raise RuntimeError('alpha13 main verification missing: ' + token)
for forbidden in ['Проверить вход','Сохранить ZIP','resultButton','readButton']:
    if forbidden in main:
        raise RuntimeError('alpha13 obsolete UI remains: ' + forbidden)
if 'Технический отчёт' in view:
    raise RuntimeError('alpha13 obsolete technical-report button remains')

print('Prepared', src13)
