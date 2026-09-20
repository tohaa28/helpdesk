#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(rel): return (root/rel).read_text(encoding='utf-8')
b=read('app/build.gradle');rv=read('app/src/main/java/ru/printcheck/android/ResultView.java');g=read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java')
checks={
 'version code':'versionCode 340031' in b,
 'version name':"versionName '3.4.0-alpha31'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'title 9sp':'TextView title=text(a,c.optString("title"),9)' in rv,
 'title autosize':'setAutoSizeTextTypeUniformWithConfiguration(7,9,1' in rv,
 'title max 3 lines':'title.setMaxLines(3)' in rv,
 'status 7sp':'TextView status=text(a,shortStatus(st),7)' in rv,
 'status autosize':'setAutoSizeTextTypeUniformWithConfiguration(6,7,1' in rv,
 'status single line':'status.setSingleLine(true)' in rv,
 'cell clickable':'cell.setClickable(true)' in rv,
 'click opens hint':'cell.setOnClickListener(v->showCheckHint(a,c))' in rv,
 'hint title':'new AlertDialog.Builder(a).setTitle(title)' in rv,
 'hint explains check':'Что проверяется' in rv,
 'hint shows result':'Результат' in rv,
 'guard explanation':'Охранное поле — минимальное расстояние' in rv,
 'positive explanation':'Пересечения разных цветов не считаются мелкими элементами' in rv,
 'negative explanation':'Расстояния между разными цветами игнорируются' in rv,
 'accessibility hint':'Нажмите для пояснения' in rv,
 'two column retained':'for(int i=0;i<checks.length();i+=2)' in rv,
 'alpha30 guard retained':'strict_no_tolerance' in g,
 'alpha27 markers retained':'rule_diameter_circles_v7_no_center_dot_reference_ruler' in g,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
