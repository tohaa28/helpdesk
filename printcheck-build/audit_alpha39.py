#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');m=r('app/src/main/java/ru/printcheck/android/MainActivity.java');q=r('app/src/main/java/ru/printcheck/android/QuickCheckEngine.java');p=r('app/src/main/java/ru/printcheck/android/ColorModelPolicy.java');ci=r('app/src/main/java/ru/printcheck/android/ColorModelInspector.java');tm=r('app/src/main/java/ru/printcheck/android/TechnologyCheckMatrix.java');rv=r('app/src/main/java/ru/printcheck/android/ResultView.java');t=r('tests/CoreTests.java');sh=r('tests/run_core.sh')
checks={
 'version code':'versionCode 340039' in b,
 'version name':"versionName '3.4.0-alpha39'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'Pantone rule':'static final String PANTONE="PANTONE_C"' in p,
 'CMYK rule':'static final String CMYK="CMYK"' in p,
 'CMYK White rule':'static final String CMYK_WHITE="CMYK_WHITE"' in p,
 'AR alternate rule':'PANTONE_OR_CMYK_WHITE' in p and 'AR[12]' in p,
 'Heraeus rule':'PANTONE_OR_HERAEUS' in p and 'H[1-3]' in p,
 'Pantone screen/tampo/embroidery':'B[1-4]|D[1-4]|I[1-3]|IB[1-3]|IO[1-3]|A[0-4]|HC[12]' in p,
 'CMYK sublimation/digital/stickers':'SB1|SB21|SB22|SBR1|SBR2|SB3|M[1-3]|SL[12]|PS1' in p,
 'CMYK White UV DTG DTF':'UV1|UV2|UV3|UVR|UVP|UVRL|DTG[1-3]|DTF[1-4]|UV-DTF[12]' in p,
 'manual technology palettes':'F[1-3]|FS' in p and 'DTF-F' in p and 'MS[12]' in p,
 'PDFBox object inspector':'extends PDFGraphicsStreamEngine' in ci,
 'path colours scoped':'getNonStrokingColor' in ci and 'getStrokingColor' in ci,
 'image colours scoped':'drawImage(PDImage im)' in ci and 'im.getColorSpace()' in ci,
 'Device CMYK':'DEVICECMYK' in ci,
 'Device RGB':'DEVICERGB' in ci,
 'Device Gray':'DEVICEGRAY' in ci,
 'Separation spot':'SEPARATION' in ci and 'getColorantName' in ci,
 'DeviceN':'DEVICEN' in ci and 'getColorantNames' in ci,
 'ICC components':'ICCBASED' in ci and 'getNumberOfComponents' in ci,
 'artwork bbox scope':'ax0' in ci and 'artArea' in ci and 'ignoredLargeObjects' in ci,
 'main colour scope':'color_model_scope' in m,
 'main colour check':'check("color_model"' in m,
 'quick colour check':'ColorModelInspector.inspect(layoutFile' in q,
 'automatic avoids duplicate manual':'!ColorModelPolicy.ruleFor(code).automatic()' in tm,
 'manual palette retained':'Технологическая палитра' in tm,
 'colour help':'case "color_model"' in rv,
 'policy core compiled':'ColorModelPolicy' in sh,
 'policy tests':'alpha39 Gifts Pantone methods mapped' in t and 'alpha39 AR rejects Pantone CMYK mixture' in t,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
