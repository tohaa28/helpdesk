#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha15.py'), str(repo)], check=True)
src15 = repo / '.printcheck-alpha15'
src16 = repo / '.printcheck-alpha16'
if src16.exists():
    shutil.rmtree(src16)
shutil.copytree(src15, src16)

part_names = [f'pc340a16.chunk{i:02d}' for i in range(16)]
parts = [pb / n for n in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError('alpha16 patch chunks missing: ' + ', '.join(missing))
encoded = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
if len(encoded) != 44128:
    raise RuntimeError(f'alpha16 base64 length mismatch: {len(encoded)}')
raw = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(raw).hexdigest()
expected = 'f650f87ab6ff65568e0c26f5fcfcaf19099b2e013810cbfccc5e87114b5da1aa'
if digest != expected:
    raise RuntimeError(f'alpha16 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src16, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha16 patch failed')
rejects = list(src16.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha16 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src16 / 'app/build.gradle').read_text(encoding='utf-8')
main = (src16 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
view = (src16 / 'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
geo = (src16 / 'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(encoding='utf-8')
pdf = (src16 / 'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text(encoding='utf-8')
zoom = src16 / 'app/src/main/java/ru/printcheck/android/ZoomImageView.java'
audit = src16 / 'tests/audit_alpha16.py'

checks = {
    'version': "versionName '3.4.0-alpha16'" in gradle and 'versionCode 340016' in gradle,
    'item-first stage': 'item_first_application_preflight_v1' in main and 'enrichSelectedApplicationGeometry' in main,
    'direct application': 'direct-application' in main,
    'constructor bridge': 'constructor-bridge' in main,
    'requirements binding': 'selected_order_application' in main and 'tech_requirements_binding' in main,
    'designer errors': 'Что исправить' in view,
    'designer visual': 'Визуальная проверка' in view and 'Само нанесение крупно' in view and 'Расположение на изделии' in view,
    'requirements UI': 'Техтребования выбранного нанесения' in view,
    'focus evidence': 'focus_file' in geo and 'saveFocusOverlay' in geo,
    'small evidence': 'small_elements_positive_negative_v1' in main and 'saveSmallElementOverlay' in geo,
    'zoom': zoom.is_file() and 'ScaleGestureDetector' in zoom.read_text(encoding='utf-8'),
    'pdf problems first': 'Что исправить' in pdf and 'Что проверить вручную' in pdf,
    'audit': audit.is_file(),
}
failed = [k for k,v in checks.items() if not v]
if failed:
    raise RuntimeError('alpha16 verification failed: ' + ', '.join(failed))
print('Prepared', src16)
print('alpha16 patch sha256', digest)
