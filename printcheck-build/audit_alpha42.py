#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');rv=r('app/src/main/java/ru/printcheck/android/ResultView.java')
checks={
 'version code':'versionCode 340042' in b,
 'version name':"versionName '3.4.0-alpha42'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'brief top block':'briefKeyFactsCard' in rv,
 'block caption':'ПАРАМЕТРЫ НАНЕСЕНИЯ' in rv,
 'print type label':'Вид печати' in rv,
 'field headline':'ПОЛЕ ПО КОНСТРУКТОРУ' in rv,
 'artwork headline':'НАЙДЕННОЕ НАНЕСЕНИЕ' in rv,
 'field physical size':'field.optDouble("width_mm")' in rv and 'field.optDouble("height_mm")' in rv,
 'artwork physical size':'art.optDouble("width_mm")' in rv and 'art.optDouble("height_mm")' in rv,
 'sizes use mm':'%.2f × %.2f мм' in rv,
 'two-column sizes':'briefFactParams' in rv,
 'method is prominent':'TextView method=text(a,mt,15)' in rv,
 'old crowded line removed':'String brief=methodText.trim()' not in rv,
 'secondary status remains':'alignmentBrief(pf)' in rv and 'guardBrief(pf)' in rv and 'smallBrief(pf)' in rv,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
