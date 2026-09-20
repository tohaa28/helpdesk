#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle'); s=r('app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java'); g=r('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'); m=r('app/src/main/java/ru/printcheck/android/MainActivity.java'); t=r('tests/CoreTests.java')
checks={
 'version code':'versionCode 340038' in b,
 'version name':"versionName '3.4.0-alpha38'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'stable path mode':'per-color-medial-gap-v5-stable-width-path' in s,
 'stable width tolerance':'stableBandMm=Math.max(.03,rule*.18)' in s,
 'geodesic path':'bfsFarthest' in s,
 'one-sided taper rejection':'widerSupportAhead' in s,
 'positive wider support':'rule*1.75+.05' in s,
 'negative wider support':'supportLimit=limit*1.75' in s,
 'same colour positive':'owner!=null&&owner[i]>0&&owner[i]!=layerId' in s,
 'diagnostic gap mode':'enclosed+stable-width-path-component-pair+open-channel-v3' in g,
 'technical string':'small_elements_per_color_medial_v6_stable_width_path' in m,
 'corner positive regression':'alpha38 one-sided positive corner plateau is ignored' in t,
 'center positive regression':'alpha38 centered positive thin segment remains violation' in t,
 'corner negative regression':'alpha38 one-sided negative corner throat is ignored' in t,
 'center negative regression':'alpha38 centered negative narrow slot remains violation' in t,
 'Cyrillic I regression':'alpha38 thick Cyrillic-I style joins do not create small positive elements' in t,
 'alpha37 regressions retained':'alpha37 V-notch corner taper is ignored' in t,
 'alpha36 text gaps retained':'alpha36 multiple text-like open gaps are not collapsed' in t,
 'alpha35 quick retained':'quick_check_window_v1' in m,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
