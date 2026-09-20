#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle'); rv=r('app/src/main/java/ru/printcheck/android/ResultView.java'); m=r('app/src/main/java/ru/printcheck/android/MainActivity.java'); pr=r('app/src/main/java/ru/printcheck/android/PdfReportWriter.java'); o=r('app/src/main/java/ru/printcheck/android/OfficialRequirements.java')
checks={
 'version code':'versionCode 340033' in b,
 'version name':"versionName '3.4.0-alpha33'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'bad badge short':'label="макет не по тт"' in rv,
 'ok badge short':'label="макет ок"' in rv,
 'badge one line':'t.setSingleLine(true)' in rv,
 'json bad short':'?"макет не по тт":' in m,
 'json ok short':'?"макет ок":"Требуется ручная проверка"' in m,
 'pdf bad short':'return "макет не по тт"' in pr,
 'pdf ok short':'return "макет ок"' in pr,
 'old long badge absent':'Не соответствует техтребованиям для нанесения' not in rv,
 'alpha32 matrix retained':'TechnologyCheckMatrix.add(checks,effective)' in m,
 'FS retained':'.codes("FS").elem(1.5).neg(1.1).letter(5)' in o,
 'alpha31 hints retained':'cell.setOnClickListener(v->showCheckHint(a,c))' in rv,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
