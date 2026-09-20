#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha32.py'),str(repo)],check=True)
src32=repo/'.printcheck-alpha32'; src33=repo/'.printcheck-alpha33'
if src33.exists(): shutil.rmtree(src33)
shutil.copytree(src32,src33)
enc=(pb/'pc340a33.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='7ffa6fa2f13c3a279cba00b62afd02157965008e41dcbea297fbdea9a1853cae': raise RuntimeError('alpha33 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='80325c396e08e78051914c3fccfa68793496f9d39dcbfce52e6ea3d2ee3d5020': raise RuntimeError('alpha33 patch sha mismatch')
pp=repo/'.alpha33.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src33,check=True)
finally: pp.unlink(missing_ok=True)
if list(src33.rglob('*.rej')): raise RuntimeError('alpha33 patch rejects')
shutil.copy2(pb/'audit_alpha33.py',src33/'tests/audit_alpha33.py')
b=(src33/'app/build.gradle').read_text(); rv=(src33/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(); m=(src33/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(); pr=(src33/'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text()
checks={
 'version':"versionCode 340033" in b and "versionName '3.4.0-alpha33'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'short bad':'label="макет не по тт"' in rv,
 'short ok':'label="макет ок"' in rv,
 'single line':'t.setSingleLine(true)' in rv,
 'json labels':'?"макет не по тт":("ok".equals(overall)?"макет ок"' in m,
 'pdf labels':'return "макет не по тт"' in pr and 'return "макет ок"' in pr,
 'alpha32 matrix':'TechnologyCheckMatrix.add(checks,effective)' in m,
 'alpha31 hints':'cell.setOnClickListener(v->showCheckHint(a,c))' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha33 invariant failure: '+', '.join(bad))
signing=src33/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha33 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha33 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha33 source')
