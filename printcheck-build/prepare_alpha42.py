#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha41.py'),str(repo)],check=True)
src41=repo/'.printcheck-alpha41'; src42=repo/'.printcheck-alpha42'
if src42.exists(): shutil.rmtree(src42)
shutil.copytree(src41,src42)
enc=(pb/'pc340a42.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='f15e55c56d7b19d267784c34086d732cc9d7355bd2918f8e5172b4aed5c6d9f7':
    raise RuntimeError('alpha42 patch sha mismatch')
pp=repo/'.alpha42.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src42,check=True)
finally: pp.unlink(missing_ok=True)
if list(src42.rglob('*.rej')): raise RuntimeError('alpha42 patch rejects')
shutil.copy2(pb/'audit_alpha42.py',src42/'tests/audit_alpha42.py')
b=(src42/'app/build.gradle').read_text()
rv=(src42/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()
checks={
 'version':"versionCode 340042" in b and "versionName '3.4.0-alpha42'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'prominent block':'ПАРАМЕТРЫ НАНЕСЕНИЯ' in rv,
 'print type':'Вид печати' in rv,
 'constructor field':'ПОЛЕ ПО КОНСТРУКТОРУ' in rv,
 'detected artwork':'НАЙДЕННОЕ НАНЕСЕНИЕ' in rv,
 'large values':'briefSizeCell' in rv,
 'old method removed':'String brief=methodText.trim()' not in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha42 invariant failure: '+', '.join(bad))
signing=src42/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha42 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha42 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha42 source')
