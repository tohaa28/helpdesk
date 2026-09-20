#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'

subprocess.run([sys.executable,str(pb/'prepare_alpha43.py'),str(repo)],check=True)

src43=repo/'.printcheck-alpha43'
src44=repo/'.printcheck-alpha44'
if src44.exists():
    shutil.rmtree(src44)
shutil.copytree(src43,src44)

parts=sorted((pb/'alpha44_patch').glob('part*.b64'))
if not parts:
    raise RuntimeError('alpha44 patch chunks missing')
enc=b''.join(p.read_bytes().replace(b'\n',b'').replace(b'\r',b'') for p in parts)
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='acbfb501a122f046b214e59cd36f4582e261f71f5bfc9ddc5a07ba4d8e9bad2f':
    raise RuntimeError('alpha44 patch sha mismatch')

pp=repo/'.alpha44.patch'
pp.write_bytes(patch)
try:
    subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src44,check=True)
finally:
    pp.unlink(missing_ok=True)

if list(src44.rglob('*.rej')):
    raise RuntimeError('alpha44 patch rejects')

# Normalize Java newline escapes. The source patch is transported through a generated
# text diff; keep escaped newlines as Java string literals rather than literal LF
# characters inside quoted strings.
ui_file=src44/'app/src/main/java/ru/printcheck/android/UiMessage.java'
ui=ui_file.read_text()
ui=ui.replace('ss.append("\n\n");','ss.append("\\n\\n");')
ui=ui.replace('ss.append("\n").append(x);','ss.append("\\n").append(x);')
ui=ui.replace('s=s.replace("; ",";\n");','s=s.replace("; ",";\\n");')
ui_file.write_text(ui)

shutil.copy2(pb/'audit_alpha44.py',src44/'tests/audit_alpha44.py')

b=(src44/'app/build.gradle').read_text()
u=(src44/'app/src/main/java/ru/printcheck/android/UiMessage.java').read_text()
m=(src44/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text()
q=(src44/'app/src/main/java/ru/printcheck/android/QuickCheckActivity.java').read_text()
rv=(src44/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text()

checks={
 'version':"versionCode 340044" in b and "versionName '3.4.0-alpha44'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'ui component':'class UiMessage' in u,
 'tones':'SUCCESS' in u and 'WARNING' in u and 'ERROR' in u and 'MANUAL' in u and 'INFO' in u,
 'auto tone':'toneForStatus' in u and 'applyAuto' in u,
 'toast':'static void toast' in u,
 'sections':'static TextView section' in u,
 'main progress':'showStatus(UiMessage.INFO,"Выполняется · "+fp+"%"' in m,
 'main dialogs':'UiMessage.dialogBody' in m,
 'main no raw status':'status.setText(' not in m,
 'quick auto':'UiMessage.applyAuto(this,status,s)' in q,
 'quick no raw status':'status.setText(' not in q,
 'quick inline':'UiMessage.inline(templateInfo' in q and 'UiMessage.inline(layoutInfo' in q,
 'result status section':'UiMessage.section(a,"Статус"' in rv,
 'result what section':'UiMessage.section(a,"Что проверяется"' in rv,
 'result detail section':'UiMessage.section(a,"Результат"' in rv,
 'result evidence section':'UiMessage.section(a,"Визуальное доказательство"' in rv,
 'warning card':'UiMessage.card' in rv and 'Требуется проверка' in rv,
}
bad=[k for k,v in checks.items() if not v]
if bad:
    raise RuntimeError('alpha44 invariant failure: '+', '.join(bad))

signing=src44/'signing/printcheck-alpha-test.p12'
expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1':
        raise RuntimeError('alpha44 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected:
    raise RuntimeError('alpha44 signing identity changed')

print('Prepared canonical PrintCheck 3.4.0-alpha44 source')
