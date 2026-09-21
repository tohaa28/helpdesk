#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle'); rv=r('app/src/main/java/ru/printcheck/android/ResultView.java'); q=r('app/src/main/java/ru/printcheck/android/QuickCheckActivity.java'); p=r('app/src/main/java/ru/printcheck/android/PdfReportWriter.java')
checks={
 'version code':'versionCode 340047' in b,
 'version name':"versionName '3.4.0-alpha47'" in b,
 'brief used-files block':'ИСПОЛЬЗУЕМЫЕ ФАЙЛЫ' in rv,
 'brief layout name':'addBriefFileRow(rows,"МАКЕТ"' in rv,
 'brief selected-field template':'ШАБЛОН ВЫБРАННОГО ПОЛЯ' in rv,
 'brief constructor/reference':'КОНСТРУКТОР ИЗДЕЛИЯ' in rv and 'ФАЙЛ СОПОСТАВЛЕНИЯ' in rv,
 'brief actual downloaded filename':'скачан как:' in rv,
 'manifest source-name lookup':'displayNameForFile' in rv,
 'duplicate reference suppression':'!refFile.equals(appFile)' in rv,
 'Quick Check source template':'quick_input_template' in q,
 'Quick Check source artwork':'quick_input_artwork' in q,
 'Quick Check ready SVG':'quick_ready_svg' in q,
 'PDF source and downloaded names':'Скачан макет как' in p and 'Скачан шаблон как' in p,
 'PDF geometry filename':'Скачан файл геометрии как' in p,
 'PDF Quick Check filenames':'Шаблон Quick Check' in p and 'Нанесение Quick Check' in p and 'Готовый SVG-макет' in p,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
