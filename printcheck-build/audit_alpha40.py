#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');p=r('app/src/main/java/ru/printcheck/android/ColorModelPolicy.java');i=r('app/src/main/java/ru/printcheck/android/ColorModelInspector.java');t=r('tests/CoreTests.java')
checks={
 'version code':'versionCode 340040' in b,
 'version name':"versionName '3.4.0-alpha40'" in b,
 'neutral counts':'cmykBlack' in p and 'cmykWhite' in p,
 'ordinary CMYK':'ordinaryCmyk()' in p,
 'Pantone neutral exception':'allowedSpots>0||o.neutralCmyk()>0' in p,
 'Heraeus neutral exception':'o.neutralCmyk()>0' in p,
 'AR neutral exception':'o.pantone>0||o.neutralCmyk()>0' in p,
 'black description':'C0 M0 Y0 K100' in p,
 'white description':'C0 M0 Y0 K0' in p,
 'inspect components':'c.getComponents()' in i,
 'pure black detector':'isPureCmykBlack' in i and 'v[3]>=.995f' in i,
 'pure white detector':'isPureCmykWhite' in i,
 'json black':'cmyk_black' in i,
 'json white':'cmyk_white' in i,
 'test black allowed':'alpha40 Pantone accepts pure CMYK black' in t,
 'test white allowed':'alpha40 Pantone accepts pure CMYK white' in t,
 'test rich/colour CMYK rejected':'alpha40 Pantone still rejects coloured CMYK' in t,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
