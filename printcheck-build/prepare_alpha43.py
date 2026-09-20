#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha42.py'),str(repo)],check=True)
src42=repo/'.printcheck-alpha42'; src43=repo/'.printcheck-alpha43'
if src43.exists(): shutil.rmtree(src43)
shutil.copytree(src42,src43)
enc=(pb/'pc340a43.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='bd6a4374d455cecaf81b14248a5cf0797bb4f30d03c5fc178e47a838e93a3885':
    raise RuntimeError('alpha43 patch sha mismatch')
pp=repo/'.alpha43.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p4','--batch','--forward','-i',str(pp)],cwd=src43,check=True)
finally: pp.unlink(missing_ok=True)
if list(src43.rglob('*.rej')): raise RuntimeError('alpha43 patch rejects')
shutil.copy2(pb/'audit_alpha43.py',src43/'tests/audit_alpha43.py')
b=(src43/'app/build.gradle').read_text()
g=(src43/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text()
checks={
 'version':"versionCode 340043" in b and "versionName '3.4.0-alpha43'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'dynamic helper':'overlayBoxStroke' in g,
 'relative field ratio':'artwork?.015f:.012f' in g,
 'field clamp':'max=artwork?5.00f:4.00f' in g,
 'dynamic dash':'overlayDash' in g,
 'art evidence':'overlayBoxStroke(art.x0,art.y0,art.x1,art.y1,scale,true)' in g,
 'field evidence':'overlayBoxStroke(field.x0,field.y0,field.x1,field.y1,scale,false)' in g,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha43 invariant failure: '+', '.join(bad))
signing=src43/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha43 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha43 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha43 source')
