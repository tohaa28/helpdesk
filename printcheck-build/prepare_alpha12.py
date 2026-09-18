#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha11.py'), str(repo)], check=True)
src11 = repo / '.printcheck-alpha11'
src12 = repo / '.printcheck-alpha12'
if src12.exists():
    shutil.rmtree(src12)
shutil.copytree(src11, src12)

raw = base64.b64decode((pb / 'pc340a12.patch.gz.b64').read_bytes().replace(b'\n', b'').replace(b'\r', b''))
digest = hashlib.sha256(raw).hexdigest()
expected = 'a4bde6f1427f0ff73ce154307ab1312839d8f306fc50c1acf0d2609ecdaedafc'
if digest != expected:
    raise RuntimeError(f'alpha12 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src12, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha12 patch failed')
rejects = list(src12.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha12 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src12 / 'app/build.gradle').read_text(encoding='utf-8')
if "versionName '3.4.0-alpha12'" not in gradle or 'versionCode 340012' not in gradle:
    raise RuntimeError('alpha12 version verification failed')
main = (src12 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
view = (src12 / 'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
for token in ['compact_article_results_v1','batch_results_screen_v1','Preflight 3.4 alpha12']:
    if token not in main:
        raise RuntimeError('alpha12 main verification missing: ' + token)
for token in ['Подробнее  ▾','Свернуть  ▴','renderBatch(','Ошибки ','BatchEntry']:
    if token not in view:
        raise RuntimeError('alpha12 ResultView verification missing: ' + token)

print('Prepared', src12)
