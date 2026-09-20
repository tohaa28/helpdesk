#!/usr/bin/env python3
from pathlib import Path
import base64,gzip,hashlib,os,shutil,subprocess,sys
repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha34.py'),str(repo)],check=True)
src34=repo/'.printcheck-alpha34';src35=repo/'.printcheck-alpha35'
if src35.exists(): shutil.rmtree(src35)
shutil.copytree(src34,src35)
enc=(pb/'pc340a35.patch.gz.b64').read_bytes().replace(b'\n',b'').replace(b'\r',b'')
patch=gzip.decompress(base64.b64decode(enc,validate=True))
if hashlib.sha256(patch).hexdigest()!='c2595cdefe114eb580f33ebf546e8f59deff7e88b26f1e0bbb4d89f046949652': raise RuntimeError('alpha35 patch sha mismatch')
pp=repo/'.alpha35.patch';pp.write_bytes(patch)
try: subprocess.run(['patch','-p1','--batch','--forward','-i',str(pp)],cwd=src35,check=True)
finally: pp.unlink(missing_ok=True)
if list(src35.rglob('*.rej')): raise RuntimeError('alpha35 patch rejects')
shutil.copy2(pb/'audit_alpha35.py',src35/'tests/audit_alpha35.py')
b=(src35/'app/build.gradle').read_text();mf=(src35/'app/src/main/AndroidManifest.xml').read_text();m=(src35/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text();q=(src35/'app/src/main/java/ru/printcheck/android/QuickCheckActivity.java').read_text();qe=(src35/'app/src/main/java/ru/printcheck/android/QuickCheckEngine.java').read_text();pr=(src35/'app/src/main/java/ru/printcheck/android/PdfReportWriter.java').read_text();pc=(src35/'app/src/main/java/ru/printcheck/android/ProductColorLogic.java').read_text();ppol=(src35/'app/src/main/java/ru/printcheck/android/ProductColorPolicy.java').read_text()
checks={
 'version':"versionCode 340035" in b and "versionName '3.4.0-alpha35'" in b,
 'app':"applicationId 'ru.printcheck.android'" in b,
 'signer':'alphaPersistent' in b,
 'quick activity manifest':'.QuickCheckActivity' in mf and 'android:exported="false"' in mf,
 'quick button':'Быстрая проверка PDF' in m,
 'real gifts flow':'Получить конструктор на Gifts' in q and 'Добавить нанесение' in q,
 'generated template capture':'captureTemplate' in q and 'selected_application.pdf' in q,
 'multi page template':'ConstructorVectorInspector.inspectAll' in q,
 'quick engine':'TechnologyCheckMatrix.add(checks,rules)' in qe and 'GeometryAnalyzer.analyzeApplicationField' in qe,
 'product color':'constructor_product_color' in m and 'ProductColorLogic.inspect' in m,
 'order color source':'itemName(root,item)' in m,
 'no invented color':'Цвет изделия не удалось однозначно' in pc,
 'pure color policy':'class ProductColorPolicy' in ppol,
 'pdf tech removed':'w.heading("Техническая информация")' not in pr and 'Версия алгоритма' not in pr,
 'alpha34 evidence':'Визуальное доказательство' in (src35/'app/src/main/java/ru/printcheck/android/ResultView.java').read_text(),
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha35 invariant failure: '+', '.join(bad))
signing=src35/'signing/printcheck-alpha-test.p12';expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha35 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha35 signing identity changed')
print('Prepared canonical PrintCheck 3.4.0-alpha35 source')
