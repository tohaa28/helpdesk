#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')

b=r('app/build.gradle')
m=r('app/src/main/java/ru/printcheck/android/MainActivity.java')
q=r('app/src/main/java/ru/printcheck/android/QuickCheckEngine.java')
rv=r('app/src/main/java/ru/printcheck/android/ResultView.java')
pr=r('app/src/main/java/ru/printcheck/android/PdfReportWriter.java')

checks={
 'version code':'versionCode 340041' in b,
 'version name':"versionName '3.4.0-alpha41'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'main field measurement':'Поле нанесения по шаблону-конструктору' in m,
 'main artwork measurement':'Найденное нанесение в макете' in m,
 'main size comparison':'Поле по конструктору' in m and 'Лимит технологии' in m,
 'quick field measurement':'Поле нанесения по шаблону-конструктору' in q,
 'quick artwork measurement':'Найденное нанесение в макете' in q,
 'brief measurement helper':'measurementBrief' in rv,
 'brief field value':'поле "+fs' in rv,
 'brief artwork value':'нанесение "+as' in rv,
 'brief combined value':'нанесение "+as+" · поле "+fs' in rv,
 'selected card field':'Поле по конструктору' in rv,
 'selected card artwork':'Найденное нанесение' in rv,
 'detail field label':'Поле нанесения по конструктору' in rv,
 'detail artwork label':'Найденное нанесение в макете' in rv,
 'pdf field label':'Поле нанесения по конструктору' in pr,
 'pdf artwork label':'Найденное нанесение в макете' in pr,
 'pdf multiplication sign':'" × "' in pr,
}
for k,v in checks.items():
    print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad:
    raise SystemExit(1)
