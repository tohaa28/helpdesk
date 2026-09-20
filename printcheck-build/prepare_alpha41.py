#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'

subprocess.run([sys.executable,str(pb/'prepare_alpha40.py'),str(repo)],check=True)

src40=repo/'.printcheck-alpha40'
src41=repo/'.printcheck-alpha41'
if src41.exists():
    shutil.rmtree(src41)
shutil.copytree(src40,src41)

enc=(pb/'pc340a41.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='329f2d60275775ffb15a609121223a9a92e2c5eebb10eac4d7a31e6c5b61ac4c':
    raise RuntimeError('alpha41 patch sha mismatch')

pp=repo/'.alpha41.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src41,check=True)
finally:
    pp.unlink(missing_ok=True)

if list(src41.rglob('*.rej')):
    raise RuntimeError('alpha41 patch rejects')

shutil.copy2(pb/'audit_alpha41.py',src41/'tests/audit_alpha41.py')

b=(src41/'app/build.gradle').read_text()
m=(src41/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
q=(src41/'app/src/main/java/ru/printcheck/android/QuickCheckEngine.java').read_text()
rv=(src41/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()
pr=(src41/'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text()

checks={
 'version':"versionCode 340041" in b and "versionName '3.4.0-alpha41'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'main field size':'Поле нанесения по шаблону-конструктору' in m,
 'main artwork size':'Найденное нанесение в макете' in m,
 'main compare':'Поле по конструктору' in m and 'Лимит технологии' in m,
 'quick field size':'Поле нанесения по шаблону-конструктору' in q,
 'quick artwork size':'Найденное нанесение в макете' in q,
 'brief measurements':'measurementBrief' in rv and 'нанесение "+as+" · поле "+fs' in rv,
 'selected card sizes':'Поле по конструктору' in rv and 'Найденное нанесение' in rv,
 'detail labels':'Поле нанесения по конструктору' in rv and 'Найденное нанесение в макете' in rv,
 'pdf labels':'Поле нанесения по конструктору' in pr and 'Найденное нанесение в макете' in pr,
}
bad=[k for k,v in checks.items() if not v]
if bad:
    raise RuntimeError('alpha41 invariant failure: '+', '.join(bad))

signing=src41/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1':
        raise RuntimeError('alpha41 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha41 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha41 source')
