#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha50.py'),str(repo)],check=True)

src50=repo/'.printcheck-alpha50'
src51=repo/'.printcheck-alpha51'
if src51.exists():
    shutil.rmtree(src51)
shutil.copytree(src50,src51)

parts=sorted((pb/'alpha51_patch').glob('part*.b64'))
if len(parts)!=2:
    raise RuntimeError('alpha51 patch chunks missing')
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='3e62110b7c1c9b84fff0d8908ebaad64e1468dd79c2a220ab9f288013ac07276':
    raise RuntimeError('alpha51 patch sha mismatch')

pp=repo/'.alpha51.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src51,check=True)
finally:
    pp.unlink(missing_ok=True)

if list(src51.rglob('*.rej')):
    raise RuntimeError('alpha51 patch rejects')

b=(src51/'app/build.gradle').read_text(encoding='utf-8')
main=(src51/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
reg=(src51/'app/src/main/java/ru/printcheck/android/RegistrationLogic.java').read_text(encoding='utf-8')
checks={
    'version':"versionCode 340051" in b and "versionName '3.4.0-alpha51'" in b,
    'app':"applicationId 'ru.printcheck.android'" in b,
    'visible field recovery':'recoverAlignmentFromVisibleLayoutField' in main,
    'visible field method':'selected-field-anchor-visible-color-raster' in main,
    'visible field policy':'visibleFieldAnchorAllowed' in reg,
    'nonblocking color':'check("constructor_color",cok?"ok":"info"' in main,
    'legacy app sync':'application_code' in main and 'application_label' in main and 'application_name' in main,
}
bad=[k for k,v in checks.items() if not v]
if bad:
    raise RuntimeError('alpha51 invariant failure: '+', '.join(bad))

signing=src51/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1':
        raise RuntimeError('alpha51 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha51 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha51 source')
