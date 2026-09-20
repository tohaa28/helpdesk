#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha31.py'),str(repo)],check=True)
src31=repo/'.printcheck-alpha31';src32=repo/'.printcheck-alpha32'
if src32.exists(): shutil.rmtree(src32)
shutil.copytree(src31,src32)
enc=(pb/'pc340a32.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
if hashlib.sha256(enc).hexdigest()!='12d4e8ffca2ad61a1ea8e70c7c5d6ecdc245e3868b615eb04e640b87157e5ba6': raise RuntimeError('alpha32 transport sha mismatch')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='8eac5a75b80a8331be45519c0259809f60c71d21b58e883c678100c8dd769276': raise RuntimeError('alpha32 patch sha mismatch')
pp=repo/'.alpha32.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src32,check=True)
finally: pp.unlink(missing_ok=True)
if list(src32.rglob('*.rej')): raise RuntimeError('alpha32 patch rejects')
shutil.copy2(pb/'audit_alpha32.py',src32/'tests/audit_alpha32.py')
b=(src32/'app/build.gradle').read_text();o=(src32/'app/src/main/java/ru/printcheck/android/OfficialRequirements.java').read_text();m=(src32/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text();rv=(src32/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text();tm=(src32/'app/src/main/java/ru/printcheck/android/TechnologyCheckMatrix.java').read_text()
checks={
 'version':"versionCode 340032" in b and "versionName '3.4.0-alpha32'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'd transfer':'.codes("D1","D2","D3","D4").pos(.4).neg(.3)' in o,
 'fs':'.codes("FS").elem(1.5).neg(1.1).letter(5)' in o,
 'shield':'codes("LSM").pos(.1).neg(.2).guard(2)' in o and 'codes("LSP","LSC").pos(.1).neg(.2).letter(2).guard(2)' in o,
 'T3':'codes("T3").texture(2,.5,.3,.3)' in o,
 'RP':'directionalGuard(2,20)' in o,
 'matrix call':'TechnologyCheckMatrix.add(checks,effective)' in m,
 'unified':'Не соответствует техтребованиям для нанесения' in rv and 'compliance_label' in m,
 'no forced small':'"min_positive","Мелкие позитивные элементы"' not in m[m.find('private static void ensureCoreChecklist'):],
 'hints':'case "micro_emboss_texture"' in rv and 'case "directional_guard"' in rv,
 'alpha31 ui':'setAutoSizeTextTypeUniformWithConfiguration(7,9,1' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha32 invariant failure: '+', '.join(bad))
signing=src32/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha32 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha32 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha32 source')
