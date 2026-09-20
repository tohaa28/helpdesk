#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');mf=r('app/src/main/AndroidManifest.xml');m=r('app/src/main/java/ru/printcheck/android/MainActivity.java');q=r('app/src/main/java/ru/printcheck/android/QuickCheckActivity.java');qe=r('app/src/main/java/ru/printcheck/android/QuickCheckEngine.java');pr=r('app/src/main/java/ru/printcheck/android/PdfReportWriter.java');pc=r('app/src/main/java/ru/printcheck/android/ProductColorLogic.java');pp=r('app/src/main/java/ru/printcheck/android/ProductColorPolicy.java');rv=r('app/src/main/java/ru/printcheck/android/ResultView.java');t=r('tests/CoreTests.java');sh=r('tests/run_core.sh')
checks={
 'version code':'versionCode 340035' in b,
 'version name':"versionName '3.4.0-alpha35'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'second activity manifest':'.QuickCheckActivity' in mf,
 'second activity private':'android:name=".QuickCheckActivity"' in mf and 'android:exported="false"' in mf,
 'quick button':'Быстрая проверка PDF' in m,
 'quick controls':'quickButton.setEnabled(!value)' in m,
 'article entry':'Артикул' in q,
 'method spinner':'Вид нанесения' in q and 'OfficialRequirements.codes()' in q,
 'real gifts generator':'Получить конструктор на Gifts' in q and 'Добавить нанесение' in q,
 'gifts host only':'host.equals("gifts.ru")||host.equals("files.gifts.ru")' in q,
 'pdf interception':'setDownloadListener' in q and 'captureTemplate(url)' in q,
 'selected field validation':'detectSelectedApplicationField' in q,
 'multi page selected field':'ConstructorVectorInspector.inspectAll' in q,
 'user pdf picker':'ACTION_OPEN_DOCUMENT' in q and 'application/pdf' in q,
 'quick engine':'class QuickCheckEngine' in qe,
 'same geometry engine':'GeometryAnalyzer.analyzeApplicationField' in qe,
 'same tech matrix':'TechnologyCheckMatrix.add(checks,rules)' in qe,
 'quick pdf report':'PdfReportWriter.write(pdf,runDir,result,null)' in q,
 'quick result view':'ResultView.renderQuick' in q,
 'product color check':'constructor_product_color' in m and 'constructor_color' in m,
 'product color uses order item':'ProductColorLogic.inspect(layout.file,colorPage,itemName(root,item))' in m,
 'unknown color no guess':'Цвет изделия не удалось однозначно извлечь' in pc,
 'color policy black':'иссиня-чер' in pp and '"black"' in pp,
 'color policy silver':'серебр' in pp and '"gray"' in pp,
 'pdf technical heading removed':'Техническая информация' not in pr,
 'pdf algorithm version removed':'Версия алгоритма' not in pr,
 'alpha34 evidence retained':'Визуальное доказательство' in rv,
 'alpha33 compact labels':'макет не по тт' in rv and 'макет ок' in rv,
 'color tests':'alpha35 extracts black product colour' in t and 'alpha35 does not invent unspecified product colour' in t,
 'core compiles color policy':'ProductColorPolicy' in sh,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
