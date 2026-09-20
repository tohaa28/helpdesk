#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha29.py'),str(repo)],check=True)
src29=repo/'.printcheck-alpha29';src30=repo/'.printcheck-alpha30'
if src30.exists(): shutil.rmtree(src30)
shutil.copytree(src29,src30)
enc=(pb/'pc340a30.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='22cf5c49a516c2ae63bb8d1376b649d505190a0b06d74359dcf9e5b52e6f024a': raise RuntimeError('alpha30 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='025c069bb4b7fb20fb06ec852ed9cb21b601deb330e5232704a51b01890a5a54': raise RuntimeError('alpha30 patch sha mismatch')
pp=repo/'.alpha30.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src30,check=True)
finally: pp.unlink(missing_ok=True)
rej=list(src30.rglob('*.rej'))
if rej: raise RuntimeError('alpha30 patch rejects: '+','.join(str(x) for x in rej))
shutil.copy2(pb/'audit_alpha30.py',src30/'tests/audit_alpha30.py')
b=(src30/'app/build.gradle').read_text();g=(src30/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text();m=(src30/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text();rv=(src30/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text();gl=(src30/'app/src/main/java/ru/printcheck/android/GuardFieldLogic.java').read_text()
checks={
 'version':"versionCode 340030" in b and "versionName '3.4.0-alpha30'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b and 'printcheck-alpha-test.p12' in b,
 'guard logic':'significant-artwork-to-real-field-edge-v1' in gl and 'm>=rule' in gl,
 'four sides':'right_in_field_mm' in g and 'bottom_in_field_mm' in g,
 'guard json':'strict_no_tolerance' in g and 'guard_field' in g,
 'automatic check':'Охранное поле соблюдено' in m and 'Охранное поле нарушено' in m and '"error"' in m,
 'bleed separate':'Автоматическая проверка вылета выполняется отдельно от охранного поля' in m,
 'ui measurement':'Охранное поле' in rv and 'guardBrief' in rv,
 'alpha29 tree':'for(int i=0;i<checks.length();i+=2)' in rv,
 'alpha27 markers':'rule_diameter_circles_v7_no_center_dot_reference_ruler' in g,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha30 invariant failure: '+', '.join(bad))
signing=src30/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha30 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha30 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha30 source')
