#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha17.py'), str(repo)], check=True)
src17 = repo / '.printcheck-alpha17'
src18 = repo / '.printcheck-alpha18'
if src18.exists():
    shutil.rmtree(src18)
shutil.copytree(src17, src18)

part_names = [f'pc340a18.b64.part{i:02d}' for i in range(9)]
parts = [pb / name for name in part_names]
missing = [p.name for p in parts if not p.is_file()]
if missing:
    raise RuntimeError('alpha18 base64 parts missing: ' + ', '.join(missing))
encoded = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
if len(encoded) != 52556:
    raise RuntimeError(f'alpha18 base64 length mismatch: {len(encoded)}')
raw = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(raw).hexdigest()
expected = 'c135057f0027a3679fd4b89b2241f02ccfd046ba0cda813b71d61958db093ae6'
if digest != expected:
    raise RuntimeError(f'alpha18 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch', '--batch', '-p1'], cwd=src18, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha18 patch failed')
rejects = list(src18.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha18 rejects: ' + ', '.join(map(str, rejects)))

# Hard source invariants before running tests/build.
gradle = (src18 / 'app/build.gradle').read_text(encoding='utf-8')
main = (src18 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
geo = (src18 / 'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(encoding='utf-8')
logic = (src18 / 'app/src/main/java/ru/printcheck/android/ConstructorFieldLogic.java')
inspector = (src18 / 'app/src/main/java/ru/printcheck/android/ConstructorVectorInspector.java')
mapper = (src18 / 'app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java')
partial = (src18 / 'app/src/main/java/ru/printcheck/android/PartialTemplateLogic.java').read_text(encoding='utf-8')
http = (src18 / 'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java').read_text(encoding='utf-8')

checks = {
    'version': "versionName '3.4.0-alpha18'" in gradle and 'versionCode 340018' in gradle,
    'pdfbox': 'com.tom-roush:pdfbox-android:2.0.27.0' in gradle and 'PDFBoxResourceLoader.init' in main,
    'constructor field logic': logic.is_file() and 'constructor_pdf_vector' in logic.read_text(encoding='utf-8'),
    'vector inspector': inspector.is_file() and 'PDFGraphicsStreamEngine' in inspector.read_text(encoding='utf-8'),
    'no field mapper': not mapper.exists() and 'ApplicationFieldMapper' not in main,
    'order size parser only': 'parseApplicationSizeMm' in partial and 'class Mapping' not in partial and 'static Mapping map' not in partial,
    'no mapped geometry': 'analyzeMappedField' not in geo and 'mapped_from_selected_application' not in geo,
    'constructor geometry': 'analyzeConstructorField' in geo and 'constructor-vector-subtraction-v1' in geo,
    'manual fallback': 'no_confident_constructor_vector_field' in main,
    'cdr relation': 'constructorSources' in http and 'saved_not_parsed' in http,
}
failed = [k for k, v in checks.items() if not v]
for k, v in checks.items():
    print(('PASS ' if v else 'FAIL ') + k)
if failed:
    raise RuntimeError('alpha18 verification failed: ' + ', '.join(failed))

subprocess.run(['bash', 'tests/run_core.sh'], cwd=src18, check=True)
subprocess.run([sys.executable, 'tests/audit_alpha18.py'], cwd=src18, check=True)
print('Prepared', src18)
print('alpha18 patch sha256', digest)
