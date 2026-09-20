#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha37.py'),str(repo)],check=True)
src37=repo/'.printcheck-alpha37'; src38=repo/'.printcheck-alpha38'
if src38.exists(): shutil.rmtree(src38)
shutil.copytree(src37,src38)
enc=(pb/'pc340a38.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='f35b9dd63847fb884fb74a000da25d7548c641d69cb1e2e5729fea01165c19f': raise RuntimeError('alpha38 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='b5f62bde9208899db3567423d1760c329b3b21b22580b668f40d1d4449e25ddf': raise RuntimeError('alpha38 patch sha mismatch')
pp=repo/'.alpha38.patch'; pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src38,check=True)
finally: pp.unlink(missing_ok=True)
if list(src38.rglob('*.rej')): raise RuntimeError('alpha38 patch rejects')
shutil.copy2(pb/'audit_alpha38.py',src38/'tests/audit_alpha38.py')
b=(src38/'app/build.gradle').read_text()
s=(src38/'app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java').read_text()
g=(src38/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text()
m=(src38/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
checks={
 'version':"versionCode 340038" in b and "versionName '3.4.0-alpha38'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'mode':'per-color-medial-gap-v5-stable-width-path' in s,
 'stable band':'stableBandMm=Math.max(.03,rule*.18)' in s,
 'geodesic':'bfsFarthest' in s,
 'one-sided taper':'widerSupportAhead' in s,
 'positive support':'rule*1.75+.05' in s,
 'negative support':'supportLimit=limit*1.75' in s,
 'diagnostics':'enclosed+stable-width-path-component-pair+open-channel-v3' in g,
 'technical':'small_elements_per_color_medial_v6_stable_width_path' in m,
 'alpha35 retained':'quick_check_window_v1' in m,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha38 invariant failure: '+', '.join(bad))
signing=src38/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha38 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha38 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha38 source')
