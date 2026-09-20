#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha38.py'),str(repo)],check=True)
src38=repo/'.printcheck-alpha38'; src39=repo/'.printcheck-alpha39'
if src39.exists(): shutil.rmtree(src39)
shutil.copytree(src38,src39)

parts=sorted((pb/'alpha39_patch').glob('part*.b64'))
if not parts: raise RuntimeError('alpha39 patch chunks missing')
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='632a32624782012a5425d1d4f4e0833121c5888b39fdac794ff2afdcf257bd13':
    raise RuntimeError('alpha39 patch sha mismatch')
pp=repo/'.alpha39.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p4','--batch','--forward','-i',str(pp)],cwd=src39,check=True)
finally: pp.unlink(missing_ok=True)
if list(src39.rglob('*.rej')): raise RuntimeError('alpha39 patch rejects')
shutil.copy2(pb/'audit_alpha39.py',src39/'tests/audit_alpha39.py')

b=(src39/'app/build.gradle').read_text()
m=(src39/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
q=(src39/'app/src/main/java/ru/printcheck/android/QuickCheckEngine.java').read_text()
p=(src39/'app/src/main/java/ru/printcheck/android/ColorModelPolicy.java').read_text()
ci=(src39/'app/src/main/java/ru/printcheck/android/ColorModelInspector.java').read_text()
tm=(src39/'app/src/main/java/ru/printcheck/android/TechnologyCheckMatrix.java').read_text()
rv=(src39/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()
checks={
 'version':"versionCode 340039" in b and "versionName '3.4.0-alpha39'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'policy classes':'PANTONE_OR_CMYK_WHITE' in p and 'CMYK_WHITE' in p and 'PANTONE_OR_HERAEUS' in p,
 'official methods':'B[1-4]|D[1-4]' in p and 'UV-DTF[12]' in p and 'AR[12]' in p,
 'object inspector':'class ColorModelInspector' in ci and 'PDFGraphicsStreamEngine' in ci,
 'artwork scope':'ignoredLargeObjects' in ci and 'ax0' in ci and 'artArea' in ci,
 'main integration':'color_model_scope' in m and 'addColorModelCheck' in m,
 'quick integration':'ColorModelInspector.inspect(layoutFile' in q,
 'no duplicate manual':'!ColorModelPolicy.ruleFor(code).automatic()' in tm,
 'help':'case "color_model"' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha39 invariant failure: '+', '.join(bad))

signing=src39/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha39 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha39 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha39 source')
