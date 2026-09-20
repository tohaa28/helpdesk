#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha35.py'),str(repo)],check=True)
src35=repo/'.printcheck-alpha35';src36=repo/'.printcheck-alpha36'
if src36.exists(): shutil.rmtree(src36)
shutil.copytree(src35,src36)
enc=(pb/'pc340a36.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='dde41031cfc96d6b0a950c44b86a56564007c4a85195a9cf58ffe72dc4e6fb27': raise RuntimeError('alpha36 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='f344af48bf7f929d084cbc92780c78c28f31123a81d34f628de1264c28a9c53c': raise RuntimeError('alpha36 patch sha mismatch')
pp=repo/'.alpha36.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src36,check=True)
finally: pp.unlink(missing_ok=True)
if list(src36.rglob('*.rej')): raise RuntimeError('alpha36 patch rejects')
shutil.copy2(pb/'audit_alpha36.py',src36/'tests/audit_alpha36.py')
b=(src36/'app/build.gradle').read_text();s=(src36/'app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java').read_text();g=(src36/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text();m=(src36/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
checks={
 'version':"versionCode 340036" in b and "versionName '3.4.0-alpha36'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'open channel mode':'per-color-medial-gap-v3-open-channel-ridge' in s,
 'open channel feature':'negative-open-same-component-channel' in s,
 'same component':'if(la<=0||la!=lb)continue' in s,
 'other colour barrier':'owner[i]>0&&owner[i]!=layerId' in s,
 'ridge':'ridgeAlong' in s and 'rayHit' in s,
 'stability':'limit*.70' in s,
 'diagnostics':'negative_gap_mode' in g and 'open-same-component-ridge-v1' in g,
 'technical string':'small_elements_per_color_medial_v4_open_channels' in m,
 'alpha35 quick':'quick_check_window_v1' in m,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha36 invariant failure: '+', '.join(bad))
signing=src36/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha36 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha36 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha36 source')
