#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'

subprocess.run([sys.executable,str(pb/'prepare_alpha44.py'),str(repo)],check=True)

src44=repo/'.printcheck-alpha44'
src45=repo/'.printcheck-alpha45'
if src45.exists(): shutil.rmtree(src45)
shutil.copytree(src44,src45)

enc=(pb/'pc340a45.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='fe1b7ff0f866ce77a6abd4af58a4800af5562ca7bc581c5b3f54aae1e7b2b26a':
    raise RuntimeError('alpha45 patch sha mismatch')

pp=repo/'.alpha45.patch';pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src45,check=True)
finally:
    pp.unlink(missing_ok=True)
if list(src45.rglob('*.rej')): raise RuntimeError('alpha45 patch rejects')

shutil.copy2(pb/'audit_alpha45.py',src45/'tests/audit_alpha45.py')

b=(src45/'app/build.gradle').read_text()
rv=(src45/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()
checks={
 'version':"versionCode 340045" in b and "versionName '3.4.0-alpha45'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'status size constant':'STATUS_TEXT_SP=8' in rv,
 'badge width constant':'STATUS_BADGE_WIDTH_DP=116' in rv,
 'badge height constant':'STATUS_BADGE_HEIGHT_DP=27' in rv,
 'inline height constant':'STATUS_INLINE_HEIGHT_DP=18' in rv,
 'brief fixed text':'shortStatus(st),STATUS_TEXT_SP' in rv,
 'brief fixed height':'new LinearLayout.LayoutParams(-1,dp(a,STATUS_INLINE_HEIGHT_DP))' in rv,
 'badge fixed text':'text(a,label,STATUS_TEXT_SP)' in rv,
 'badge fixed geometry':'dp(a,STATUS_BADGE_WIDTH_DP),dp(a,STATUS_BADGE_HEIGHT_DP)' in rv,
 'no brief status autosize':'status.setAutoSizeTextTypeUniformWithConfiguration' not in rv,
 'no badge autosize':'t.setAutoSizeTextTypeUniformWithConfiguration(7,9' not in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha45 invariant failure: '+', '.join(bad))

signing=src45/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha45 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha45 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha45 source')
