#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle'); s=r('app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java'); g=r('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'); m=r('app/src/main/java/ru/printcheck/android/MainActivity.java'); t=r('tests/CoreTests.java')
checks={
 'version code':'versionCode 340037' in b,
 'version name':"versionName '3.4.0-alpha37'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'persistent mode':'per-color-medial-gap-v4-persistent-width' in s,
 'positive persistent run':'positive-persistent-narrow-run' in s,
 'component gap direct rays':'openDifferentComponentChannels' in s,
 'different components required':'la<=0||lb<=0||la==lb' in s,
 'same component open channel retained':'la<=0||la!=lb' in s,
 'other colours barrier':'owner!=null&&owner[i]>0&&owner[i]!=layerId' in s,
 'min path physical':'Math.max(3.0,rule*pxPerMm)' in s and 'Math.max(3.0,limit)' in s,
 'minimum-width core band':'coreBandMm=Math.max(.02,rule*.25)' in s,
 'core path required':'minCorePx=Math.max(2.0,minPathPx*.55)' in s,
 'corner taper explanation':'converge into a corner' in s,
 'diagnostic mode':'persistent-component-pair+persistent-open-channel-v2' in g,
 'geometry mode':'per-color-positive-negative-v3-persistent-width' in g,
 'technical string':'small_elements_per_color_medial_v5_persistent_width' in m,
 'positive corner regression':'alpha37 positive corner taper is ignored' in t,
 'positive run regression':'alpha37 sustained positive thin run remains violation' in t,
 'negative corner regression':'alpha37 converging component corners are not a negative gap' in t,
 'parallel gap regression':'alpha37 persistent parallel same-colour gap remains violation' in t,
 'V notch regression':'alpha37 V-notch corner taper is ignored' in t,
 'alpha36 text gaps retained':'alpha36 multiple text-like open gaps are not collapsed' in t,
 'alpha35 quick retained':'quick_check_window_v1' in m,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
