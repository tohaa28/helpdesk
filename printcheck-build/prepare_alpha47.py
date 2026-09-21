#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'

subprocess.run([sys.executable,str(pb/'prepare_alpha46.py'),str(repo)],check=True)

src46=repo/'.printcheck-alpha46'
src47=repo/'.printcheck-alpha47'
if src47.exists(): shutil.rmtree(src47)
shutil.copytree(src46,src47)

enc=(pb/'pc340a47.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='8d88684423e566f81a969cb9d6ca830c201bf461fa0a98e2e69379130047b82d':
    raise RuntimeError('alpha47 patch sha mismatch')

pp=repo/'.alpha47.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src47,check=True)
finally:
    pp.unlink(missing_ok=True)

if list(src47.rglob('*.rej')): raise RuntimeError('alpha47 patch rejects')

b=(src47/'app/build.gradle').read_text()
rv=(src47/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()
m=(src47/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
q=(src47/'app/src/main/java/ru/printcheck/android/QuickCheckActivity.java').read_text()
p=(src47/'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text()

checks={
 'version':"versionCode 340047" in b and "versionName '3.4.0-alpha47'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'brief files':'ИСПОЛЬЗОВАННЫЕ ФАЙЛЫ' in rv,
 'brief layout':'briefFileRow(a,"Макет",layout)' in rv,
 'brief selected template':'briefFileRow(a,"Шаблон выбранного поля",selected)' in rv,
 'brief geometry file':'briefFileRow(a,"Использован для геометрии",geo)' in rv,
 'geometry metadata':'geometry_reference_name' in m and 'geometry_reference_type' in m,
 'quick input artwork':'input_artwork_name' in q,
 'quick input template':'input_template_name' in q,
 'quick ready layout':'ready_layout_name' in q,
 'pdf filenames':'Файл макета' in p and 'Файл шаблона' in p and 'Готовый SVG-макет' in p,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha47 invariant failure: '+', '.join(bad))

signing=src47/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha47 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha47 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha47 source')
