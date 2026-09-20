#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha36.py'),str(repo)],check=True)
src36=repo/'.printcheck-alpha36'; src37=repo/'.printcheck-alpha37'
if src37.exists(): shutil.rmtree(src37)
shutil.copytree(src36,src37)
enc=(pb/'pc340a37.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='a070e94c5727c3176a7003480e0ea382c942d59840a7c046d78b4225b007d359': raise RuntimeError('alpha37 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='95a2532d93752204a82d10eff6ff668142045ed5365541c0259d40b9e73c38ae': raise RuntimeError('alpha37 patch sha mismatch')
pp=repo/'.alpha37.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src37,check=True)
finally: pp.unlink(missing_ok=True)
if list(src37.rglob('*.rej')): raise RuntimeError('alpha37 patch rejects')
shutil.copy2(pb/'audit_alpha37.py',src37/'tests/audit_alpha37.py')
b=(src37/'app/build.gradle').read_text(); s=(src37/'app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java').read_text(); g=(src37/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(); m=(src37/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
checks={
 'version':"versionCode 340037" in b and "versionName '3.4.0-alpha37'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'mode':'per-color-medial-gap-v4-persistent-width' in s,
 'positive persistence':'positive-persistent-narrow-run' in s,
 'different component persistence':'negative-different-component-persistent-channel' in s,
 'open persistence':'negative-open-same-component-channel' in s,
 'physical run':'Math.max(3.0,rule*pxPerMm)' in s and 'Math.max(3.0,limit)' in s,
 'core persistence':'coreBandMm=Math.max(.02,rule*.25)' in s and 'minCorePx=Math.max(2.0,minPathPx*.55)' in s,
 'same colour':'la<=0||lb<=0||la==lb' in s and 'la<=0||la!=lb' in s,
 'cross colour barrier':'owner[i]>0&&owner[i]!=layerId' in s,
 'diagnostics':'persistent-component-pair+persistent-open-channel-v2' in g,
 'technical':'small_elements_per_color_medial_v5_persistent_width' in m,
 'alpha36 source retained':'constructor_product_color_v1+quick_check_window_v1' in m,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha37 invariant failure: '+', '.join(bad))
signing=src37/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha37 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha37 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha37 source')
