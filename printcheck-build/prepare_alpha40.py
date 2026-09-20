#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha39.py'),str(repo)],check=True)
src39=repo/'.printcheck-alpha39'; src40=repo/'.printcheck-alpha40'
if src40.exists(): shutil.rmtree(src40)
shutil.copytree(src39,src40)
enc=(pb/'pc340a40.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='5c679c604bb0b83b627012079933279f05690ddf0102bc36d046293b8dee3449':
    raise RuntimeError('alpha40 patch sha mismatch')
pp=repo/'.alpha40.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src40,check=True)
finally: pp.unlink(missing_ok=True)
if list(src40.rglob('*.rej')): raise RuntimeError('alpha40 patch rejects')
shutil.copy2(pb/'audit_alpha40.py',src40/'tests/audit_alpha40.py')
b=(src40/'app/build.gradle').read_text(); p=(src40/'app/src/main/java/ru/printcheck/android/ColorModelPolicy.java').read_text(); i=(src40/'app/src/main/java/ru/printcheck/android/ColorModelInspector.java').read_text()
checks={
 'version':"versionCode 340040" in b and "versionName '3.4.0-alpha40'" in b,
 'neutral fields':'cmykBlack' in p and 'cmykWhite' in p and 'ordinaryCmyk()' in p,
 'black rule':'C0 M0 Y0 K100' in p,
 'white rule':'C0 M0 Y0 K0' in p,
 'component inspect':'isPureCmykBlack' in i and 'isPureCmykWhite' in i,
 'json':'cmyk_black' in i and 'cmyk_white' in i,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha40 invariant failure: '+', '.join(bad))
signing=src40/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha40 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha40 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha40 source')
