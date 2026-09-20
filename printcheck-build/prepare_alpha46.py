#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha45.py'),str(repo)],check=True)

src45=repo/'.printcheck-alpha45'; src46=repo/'.printcheck-alpha46'
if src46.exists(): shutil.rmtree(src46)
shutil.copytree(src45,src46)

parts=sorted((pb/'alpha46_patch').glob('part*.b64'))
if len(parts)!=9:
    raise RuntimeError('alpha46 patch chunks missing: expected 9, got '+str(len(parts)))
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='4f55dfa20824652e13446439e8c2f7fa31cea8392700338b2d3ce3997e7347c4':
    raise RuntimeError('alpha46 patch sha mismatch')

pp=repo/'.alpha46.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src46,check=True)
finally: pp.unlink(missing_ok=True)
if list(src46.rglob('*.rej')): raise RuntimeError('alpha46 patch rejects')

# Android's PrintDocumentAdapter callback constructors are package-private.
# Use PdfDocument + WebView.draw for the normalized analysis PDF.
shutil.copy2(pb/'alpha46_SvgPdfExporter.java',src46/'app/src/main/java/ru/printcheck/android/SvgPdfExporter.java')

shutil.copy2(pb/'audit_alpha46.py',src46/'tests/audit_alpha46.py')

b=(src46/'app/build.gradle').read_text()
q=(src46/'app/src/main/java/ru/printcheck/android/QuickCheckActivity.java').read_text()
s=(src46/'app/src/main/java/ru/printcheck/android/SvgEditorSupport.java').read_text()
p=(src46/'app/src/main/java/ru/printcheck/android/SvgPdfExporter.java').read_text()
qe=(src46/'app/src/main/java/ru/printcheck/android/QuickCheckEngine.java').read_text()

checks={
 'version':"versionCode 340046" in b and "versionName '3.4.0-alpha46'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'template picker':'PICK_TEMPLATE=301' in q and 'Загрузить шаблон' in q,
 'artwork picker':'PICK_ARTWORK=302' in q and 'Загрузить нанесение' in q,
 'no gifts browser':'gifts.ru' not in q and 'Получить конструктор на Gifts' not in q,
 'editor bridge':'class EditorBridge' in q and 'JavascriptInterface' in q,
 'save svg':'saveDownloads' in q and 'ready_layout.svg' in q,
 'svg editor support':'class SvgEditorSupport' in s,
 'pdf template':'pdfTemplate' in s and 'PDFRenderer' in s,
 'svg template':'svgTemplate' in s and 'parseSvg' in s,
 'multiple fields':'FIELD_CANDIDATES' in s and 'prevField()' in s and 'nextField()' in s,
 'mm metrics':'art_width_mm' in s and 'art_x_in_field_mm' in s,
 'fit center':'fitArt()' in s and 'centerArt()' in s,
 'manual field':'Править поле' in s and 'manual-required' in s,
 'pdf exporter':'class SvgPdfExporter' in p and 'PdfDocument' in p and 'web.draw(canvas)' in p,
 'normalized check':'exportBoth' in q and 'QuickCheckEngine.run' in q,
 'engine wording':'выбранное поле шаблона' in qe and 'Gifts' not in qe,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha46 invariant failure: '+', '.join(bad))

signing=src46/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha46 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha46 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha46 source')
