#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha49.py'),str(repo)],check=True)

src49=repo/'.printcheck-alpha49'
src50=repo/'.printcheck-alpha50'
if src50.exists(): shutil.rmtree(src50)
shutil.copytree(src49,src50)

parts=sorted((pb/'alpha50_patch').glob('part*.b64'))
if len(parts)!=2: raise RuntimeError('alpha50 patch chunks missing')
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='b866eaa07af457761bb4063ec850161d9e4716ac6cc7398a6255f0495f738082':
    raise RuntimeError('alpha50 patch sha mismatch')

pp=repo/'.alpha50.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src50,check=True)
finally:
    pp.unlink(missing_ok=True)

if list(src50.rglob('*.rej')): raise RuntimeError('alpha50 patch rejects')

b=(src50/'app/build.gradle').read_text(encoding='utf-8')
main=(src50/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
http=(src50/'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java').read_text(encoding='utf-8')
reg=(src50/'app/src/main/java/ru/printcheck/android/RegistrationLogic.java').read_text(encoding='utf-8')
checks={
    'version':"versionCode 340050" in b and "versionName '3.4.0-alpha50'" in b,
    'app':"applicationId 'ru.printcheck.android'" in b,
    'physical field anchor':'selected-field-anchor-physical-identity' in main and 'applicationFieldAnchorAllowed' in reg,
    'multi application rows':'application_labels' in http and 'application_variant_index' in http,
    'geometry summary primary':'Результат определения нанесения:' in main,
    'product color nonblocking':'автоматическая вспомогательная оценка цвета' in main,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha50 invariant failure: '+', '.join(bad))

signing=src50/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha50 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha50 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha50 source')
