#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha33.py'),str(repo)],check=True)
src33=repo/'.printcheck-alpha33'; src34=repo/'.printcheck-alpha34'
if src34.exists(): shutil.rmtree(src34)
shutil.copytree(src33,src34)
enc=(pb/'pc340a34.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='8fd353921b4b4571290c5f834b8f019e9ae74c3040913e3f636cbc887ef51641': raise RuntimeError('alpha34 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='58dd5599250514f845f13c2771d6c985e7fd963bee22905a7256af268ae6bea5': raise RuntimeError('alpha34 patch sha mismatch')
pp=repo/'.alpha34.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src34,check=True)
finally: pp.unlink(missing_ok=True)
if list(src34.rglob('*.rej')): raise RuntimeError('alpha34 patch rejects')
shutil.copy2(pb/'audit_alpha34.py',src34/'tests/audit_alpha34.py')
b=(src34/'app/build.gradle').read_text(); rv=(src34/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(); m=(src34/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
checks={
 'version':"versionCode 340034" in b and "versionName '3.4.0-alpha34'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'brief context':'addBriefChecks(a,briefNode.body,checks,runDir,pf)' in rv,
 'small evidence':'small.optString("overlay_file")' in rv,
 'guard evidence':'"guard_field".equals(id)' in rv and 'geo.optString("focus_file")' in rv,
 'alignment evidence':'"alignment".equals(id)' in rv and 'geo.optString("overlay_file")' in rv,
 'artwork evidence':'"artwork".equals(id)' in rv and 'geo.optString("artwork_file")' in rv,
 'problem only':'isProblemStatus(c.optString("status"))?evidenceForCheck' in rv,
 'visual label':'Визуальное доказательство' in rv,
 'circle explanation':'Кружки показывают найденные проблемные зоны' in rv,
 'fullscreen':'largeEvidence(a,evidence,380)' in rv,
 'alpha33 status':'label="макет не по тт"' in rv and 'label="макет ок"' in rv,
 'alpha32 matrix':'TechnologyCheckMatrix.add(checks,effective)' in m,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha34 invariant failure: '+', '.join(bad))
signing=src34/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha34 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha34 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha34 source')
