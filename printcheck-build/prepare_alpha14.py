#!/usr/bin/env python3
from pathlib import Path
import base64, gzip, hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'

subprocess.run([sys.executable, str(pb / 'prepare_alpha13.py'), str(repo)], check=True)
src13 = repo / '.printcheck-alpha13'
src14 = repo / '.printcheck-alpha14'
if src14.exists():
    shutil.rmtree(src14)
shutil.copytree(src13, src14)

parts = sorted(pb.glob('pc340a14.chunk*'))
if len(parts) != 10:
    raise RuntimeError(f'alpha14 patch chunks: expected 10, got {len(parts)}')
encoded = b''.join(p.read_bytes().replace(b'\n', b'').replace(b'\r', b'') for p in parts)
if len(encoded) != 28704:
    raise RuntimeError(f'alpha14 base64 length mismatch: {len(encoded)}')
raw = base64.b64decode(encoded, validate=True)
digest = hashlib.sha256(raw).hexdigest()
expected = 'bfb248127279d15a734550c49ed80dc486a5c17892af21d08630f5c2d1cc04b7'
if digest != expected:
    raise RuntimeError(f'alpha14 patch digest mismatch: {digest}')
patch_data = gzip.decompress(raw)
proc = subprocess.run(['patch','--batch','-p1'], cwd=src14, input=patch_data)
if proc.returncode != 0:
    raise RuntimeError('alpha14 patch failed')
rejects = list(src14.rglob('*.rej'))
if rejects:
    raise RuntimeError('alpha14 rejects: ' + ', '.join(map(str,rejects)))

gradle = (src14 / 'app/build.gradle').read_text(encoding='utf-8')
if "versionName '3.4.0-alpha14'" not in gradle or 'versionCode 340014' not in gradle:
    raise RuntimeError('alpha14 version verification failed')
main = (src14 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
view = (src14 / 'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
writer = (src14 / 'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text(encoding='utf-8')
for token in ['no_skipped_checks_v1','small_element_proof_v2','clickable_reports_v1','position_pdf_reports_v1','batch_card_integrity_v1','ensureCoreChecklist']:
    if token not in main:
        raise RuntimeError('alpha14 main verification missing: ' + token)
for token in ['Мелкие элементы','Открыть PDF-отчёт заказа','PDF позиции','reportLink(','smallBrief(']:
    if token not in view:
        raise RuntimeError('alpha14 ResultView verification missing: ' + token)
for token in ['writePosition(','smallPdfMetric(','image(File file']:
    if token not in writer:
        raise RuntimeError('alpha14 PdfReportWriter verification missing: ' + token)
if not (src14 / 'app/src/main/java/ru/printcheck/android/ReportProvider.java').is_file():
    raise RuntimeError('ReportProvider missing')
if not (src14 / 'tests/audit_alpha14.py').is_file():
    raise RuntimeError('alpha14 audit missing')

print('Prepared', src14)
