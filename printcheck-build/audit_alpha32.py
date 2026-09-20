#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');o=r('app/src/main/java/ru/printcheck/android/OfficialRequirements.java');p=r('app/src/main/java/ru/printcheck/android/PreflightRules.java');m=r('app/src/main/java/ru/printcheck/android/MainActivity.java');rv=r('app/src/main/java/ru/printcheck/android/ResultView.java');tm=r('app/src/main/java/ru/printcheck/android/TechnologyCheckMatrix.java');t=r('tests/CoreTests.java')
checks={
'version code':'versionCode 340032' in b,
'version name':"versionName '3.4.0-alpha32'" in b,
'app id':"applicationId 'ru.printcheck.android'" in b,
'persistent signer':'alphaPersistent' in b,
'snapshot 2026-09-20':'SNAPSHOT_DATE = "2026-09-20"' in o,
'D positive 0.4':'.codes("D1","D2","D3","D4").pos(.4).neg(.3)' in o,
'FS 1.5/1.1':'.codes("FS").elem(1.5).neg(1.1).letter(5)' in o,
'shield guard':'codes("LSM").pos(.1).neg(.2).guard(2)' in o and 'codes("LSP","LSC").pos(.1).neg(.2).letter(2).guard(2)' in o,
'AR ink 15-85':'codes("AR1","AR2").pos(.4).neg(.4).dpi(160).ink(15).inkMax(85)' in o,
'T1/T2 contours':'.guard(18).contours()' in o,
'T3 texture':'.codes("T3").texture(2,.5,.3,.3)' in o,
'RP directional':'.directionalGuard(2,20)' in o,
'embroidery round':'.round(2)' in o and '.round(4.5)' in o,
'DTF-F outline':'.foilOutline(4)' in o,
'MS connectors':'.connector(3,.1)' in o,
'T3 generic disabled':'if("T3".equals(code))' in p and 'standardSmallRules=false' in p,
'AR alternative colors':'if("AR1".equals(code)||"AR2".equals(code))r.maxColors=-1' in p,
'RP uniform guard disabled':'if(code.matches("RP[1-3]"))r.guardMm=-1' in p,
'matrix attached':'TechnologyCheckMatrix.add(checks,effective)' in m,
'irrelevant positive omitted':'Порог позитивных элементов не задан' not in m,
'irrelevant negative omitted':'Порог негативных элементов не задан' not in m,
'unified result JSON':'compliance_label' in m and 'Не соответствует техтребованиям для нанесения' in m,
'unified UI badge':'label="Не соответствует техтребованиям для нанесения"' in rv,
'new hints':'case "round_element"' in rv and 'case "directional_guard"' in rv and 'case "micro_emboss_texture"' in rv,
'alpha31 clickable hints':'cell.setOnClickListener(v->showCheckHint(a,c))' in rv,
'alpha30 guard retained':'case "guard_field"' in rv,
'alpha27 marker behavior': 'rule_diameter_circles_v7_no_center_dot_reference_ruler' in r('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'),
'97 tests declared':'alpha32 embroidery round element profiles' in t,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
