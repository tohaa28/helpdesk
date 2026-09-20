#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(rel): return (root/rel).read_text(encoding='utf-8')
b=read('app/build.gradle');g=read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java');m=read('app/src/main/java/ru/printcheck/android/MainActivity.java');rv=read('app/src/main/java/ru/printcheck/android/ResultView.java');gl=read('app/src/main/java/ru/printcheck/android/GuardFieldLogic.java');t=read('tests/CoreTests.java');sh=read('tests/run_core.sh')
checks={
 'version code':'versionCode 340030' in b,
 'version name':"versionName '3.4.0-alpha30'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'guard class':'significant-artwork-to-real-field-edge-v1' in gl,
 'strict threshold':'this.ok=available&&m>=rule' in gl,
 'negative outside':'this.outside=available&&m<0' in gl,
 'left distance':'left_in_field_mm' in g,
 'top distance':'top_in_field_mm' in g,
 'right distance':'right_in_field_mm' in g,
 'bottom distance':'bottom_in_field_mm' in g,
 'guard result':'out.put("guard_field",guard)' in g,
 'no hidden tolerance':'strict_no_tolerance' in g,
 'real-field definition':'minimum distance from confirmed significant artwork pixels to each edge of the real print field' in g,
 'automatic ok':'Охранное поле соблюдено' in m,
 'automatic error':'Охранное поле нарушено' in m,
 'outside error':'Нанесение выходит за край поля' in m,
 'bleed separated':'Автоматическая проверка вылета выполняется отдельно от охранного поля' in m,
 'result metric':'минимум %.2f мм · норма ≥ %.2f мм' in rv,
 'brief guard':'guardBrief' in rv,
 'guard compiled':'GuardFieldLogic}' in sh,
 'threshold test':'alpha30 guard exact threshold passes' in t,
 'below test':'alpha30 guard below threshold fails' in t,
 'outside test':'alpha30 guard outside field is negative and fails' in t,
 'four edges test':'alpha30 guard uses nearest of all four field edges' in t,
 'alpha29 two columns':'for(int i=0;i<checks.length();i+=2)' in rv,
 'alpha27 markers':'rule_diameter_circles_v7_no_center_dot_reference_ruler' in g,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
