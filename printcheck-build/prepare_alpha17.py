#!/usr/bin/env python3
from pathlib import Path
import gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha16.py'), str(repo)], check=True)
src16 = repo / '.printcheck-alpha16'
src17 = repo / '.printcheck-alpha17'
if src17.exists():
    shutil.rmtree(src17)
shutil.copytree(src16, src17)

part_names = [f'pc340a17.b64.part{i:02d}' for i in range(9)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError('alpha17 base64 parts missing: ' + ', '.join(missing))
encoded = b''.join(p.read_bytes().replace(b'\\n', b'').replace(b'\\r', b'') for p in parts)
if len(encoded) != 22460:
    raise RuntimeError(f'alpha17 base64 length mismatch: {len(encoded)}')
import base64
raw = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(raw).hexdigest()
expected = '3a56ae97e3dff170fa85a494562f4b6b66d2ad66a89fd80224528a702a8a4871'
if digest != expected:
    raise RuntimeError(f'alpha17 patch digest mismatch: {digest}')

patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src17, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha17 patch failed')
rejects = list(src17.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha17 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src17 / 'app/build.gradle').read_text(encoding='utf-8')
main = (src17 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
matcher = (src17 / 'app/src/main/java/ru/printcheck/android/RasterMatcher.java').read_text(encoding='utf-8')
logic = (src17 / 'app/src/main/java/ru/printcheck/android/PartialTemplateLogic.java')
mapper = (src17 / 'app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java')
geo = (src17 / 'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(encoding='utf-8')
view = (src17 / 'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
pdf = (src17 / 'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text(encoding='utf-8')
audit = src17 / 'tests/audit_alpha17.py'

checks = {
    'version': "versionName '3.4.0-alpha17'" in gradle and 'versionCode 340017' in gradle,
    'technical marker': 'partial_template_recovery_v1' in main,
    'partial logic': logic.is_file() and 'partial-template-field-map-v1' in logic.read_text(encoding='utf-8'),
    'field mapper': mapper.is_file() and 'PartialTemplateLogic' in mapper.read_text(encoding='utf-8'),
    'mapper call': 'ApplicationFieldMapper.map' in main,
    'authoritative application size': 'parseApplicationSizeMm(applicationSize)' in mapper.read_text(encoding='utf-8'),
    'partial matcher': 'same-page-partial-template' in matcher,
    'mapped field geometry': 'analyzeMappedField' in geo and 'mapped_from_selected_application' in geo,
    'constructor subtraction': 'template_fragment_mode' in geo,
    'positive negative retained': 'small_elements_positive_negative_v1' in main and 'SmallElementAnalyzer.analyze' in geo,
    'proof images retained': 'saveSmallElementOverlay' in geo and 'saveFocusOverlay' in geo,
    'font scope retained': 'fontsInArtwork' in main,
    'designer fragment label': 'удалённой частью конструктора' in view,
    'pdf fragment label': 'Фрагмент конструктора + нанесение' in pdf,
    'audit': audit.is_file(),
}
failed = [k for k,v in checks.items() if not v]
for k,v in checks.items():
    print(('PASS ' if v else 'FAIL ') + k)
if failed:
    raise RuntimeError('alpha17 verification failed: ' + ', '.join(failed))

print('Prepared', src17)
print('alpha17 patch sha256', digest)
