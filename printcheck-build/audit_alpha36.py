#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');s=r('app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java');g=r('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java');m=r('app/src/main/java/ru/printcheck/android/MainActivity.java');t=r('tests/CoreTests.java')
checks={
 'version code':'versionCode 340036' in b,
 'version name':"versionName '3.4.0-alpha36'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'new analyzer mode':'per-color-medial-gap-v3-open-channel-ridge' in s,
 'three negative classes':'negative-enclosed-gap' in s and 'negative-same-color-gap' in s and 'negative-open-same-component-channel' in s,
 'open channels use ridge':'ridgeAlong' in s,
 'open channels use two rays':'rayHit' in s,
 'same component required':'if(la<=0||la!=lb)continue' in s,
 'cross colour remains barrier':'owner[i]>0&&owner[i]!=layerId' in s,
 'enclosed excluded from open scan':'enclosed[i]' in s,
 'stability filter':'limit*.70' in s,
 'marker narrowest locus':'widths[v]>minMm+epsMm' in s,
 'diagnostic gap mode':'enclosed+component-pair+open-same-component-ridge-v1' in g,
 'diagnostic mode v2':'per-color-positive-negative-v2-open-channel-ridge-reference-ruler-tight-roi' in g,
 'technical string':'small_elements_per_color_medial_v4_open_channels' in m,
 'open channel test':'alpha36 open same-component channel is negative gap' in t,
 'multiple gap test':'alpha36 multiple text-like open gaps are not collapsed' in t,
 'other colour regression':'alpha36 other colour blocks open negative channel' in t,
 'legacy gap regression':'alpha36 legacy same-colour component gap remains detected' in t,
 'alpha35 quick retained':'quick_check_window_v1' in m,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
