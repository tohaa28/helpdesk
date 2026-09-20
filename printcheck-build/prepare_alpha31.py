#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha30.py'),str(repo)],check=True)
src30=repo/'.printcheck-alpha30';src31=repo/'.printcheck-alpha31'
if src31.exists(): shutil.rmtree(src31)
shutil.copytree(src30,src31)
enc=(pb/'pc340a31.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='7a79b3fd9d7a8848c97e8936441fa5a326bc5c536850a53478234cc9d2424e70': raise RuntimeError('alpha31 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='3f2b8265c4ec0d4914568ac6a5d75f9c3f6f1c134dad23357b801e169846061a': raise RuntimeError('alpha31 patch sha mismatch')
pp=repo/'.alpha31.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src31,check=True)
finally: pp.unlink(missing_ok=True)
rej=list(src31.rglob('*.rej'))
if rej: raise RuntimeError('alpha31 patch rejects: '+','.join(str(x) for x in rej))
shutil.copy2(pb/'audit_alpha31.py',src31/'tests/audit_alpha31.py')
b=(src31/'app/build.gradle').read_text();rv=(src31/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text();g=(src31/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text()
checks={
 'version':"versionCode 340031" in b and "versionName '3.4.0-alpha31'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b and 'printcheck-alpha-test.p12' in b,
 'autosize title':'setAutoSizeTextTypeUniformWithConfiguration(7,9,1' in rv,
 'autosize status':'setAutoSizeTextTypeUniformWithConfiguration(6,7,1' in rv,
 'three lines':'title.setMaxLines(3)' in rv,
 'clickable':'cell.setOnClickListener(v->showCheckHint(a,c))' in rv,
 'hint dialog':'Что проверяется' in rv and 'Результат' in rv,
 'guard hint':'Охранное поле — минимальное расстояние' in rv,
 'alpha30 guard':'strict_no_tolerance' in g,
 'alpha29 grid':'for(int i=0;i<checks.length();i+=2)' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha31 invariant failure: '+', '.join(bad))
signing=src31/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha31 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha31 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha31 source')
