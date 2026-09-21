#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha48.py'),str(repo)],check=True)

src48=repo/'.printcheck-alpha48'
src49=repo/'.printcheck-alpha49'
if src49.exists(): shutil.rmtree(src49)
shutil.copytree(src48,src49)

parts=sorted((pb/'alpha49_patch').glob('part*.b64'))
if len(parts)!=2: raise RuntimeError('alpha49 patch chunks missing')
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='a1be822b24854d44e226004757b0f2839b1bb810a7320571ded42d9c42cf5d97':
    raise RuntimeError('alpha49 patch sha mismatch')

pp=repo/'.alpha49.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src49,check=True)
finally:
    pp.unlink(missing_ok=True)
if list(src49.rglob('*.rej')): raise RuntimeError('alpha49 patch rejects')

b=(src49/'app/build.gradle').read_text(encoding='utf-8')
h=(src49/'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java').read_text(encoding='utf-8')
rv=(src49/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(encoding='utf-8')
checks={
    'version':"versionCode 340049" in b and "versionName '3.4.0-alpha49'" in b,
    'app':"applicationId 'ru.printcheck.android'" in b,
    'semantic template filenames':'templatePdfFileName' in h and '"link_text"' in h,
    'brief template names':'templateNameByFile' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha49 invariant failure: '+', '.join(bad))

signing=src49/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha49 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha49 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha49 source')
