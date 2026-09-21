#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');rv=r('app/src/main/java/ru/printcheck/android/ResultView.java');q=r('app/src/main/java/ru/printcheck/android/QuickCheckActivity.java')
checks={
 'version code':'versionCode 340047' in b,
 'version name':"versionName '3.4.0-alpha47'" in b,
 'brief file block':'ИСПОЛЬЗУЕМЫЕ ФАЙЛЫ' in rv,
 'downloaded local filename':'Скачан / сохранён как:' in rv,
 'layout filename':'addBriefFileRow(rows,"МАКЕТ"' in rv,
 'selected application filename':'PDF ВЫБРАННОГО НАНЕСЕНИЯ' in rv,
 'constructor/reference filename':'КОНСТРУКТОР / ЭТАЛОН' in rv or 'КОНСТРУКТОР"' in rv,
 'file manifest fallback':'displayNameByFile' in rv,
 'quick source names persisted':'quick_editor_sources' in q,
 'quick template shown':'ШАБЛОН QUICK CHECK' in rv,
 'quick artwork shown':'ИСХОДНОЕ НАНЕСЕНИЕ' in rv,
 'quick ready svg shown':'ГОТОВЫЙ МАКЕТ' in rv,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
