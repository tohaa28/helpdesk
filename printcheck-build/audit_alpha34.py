#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle'); rv=r('app/src/main/java/ru/printcheck/android/ResultView.java'); m=r('app/src/main/java/ru/printcheck/android/MainActivity.java'); o=r('app/src/main/java/ru/printcheck/android/OfficialRequirements.java')
checks={
 'version code':'versionCode 340034' in b,
 'version name':"versionName '3.4.0-alpha34'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'brief gets run context':'addBriefChecks(a,briefNode.body,checks,runDir,pf)' in rv,
 'cell gets run context':'briefCheckCell(a,left,runDir,pf)' in rv and 'briefCheckCell(a,right,runDir,pf)' in rv,
 'problem status only':'return "error".equals(st)||"warning".equals(st)' in rv,
 'small positive evidence':'"min_positive".equals(id)' in rv,
 'small negative evidence':'"min_negative".equals(id)' in rv,
 'single element evidence':'"single_element".equals(id)' in rv,
 'small overlay':'small.optString("overlay_file")' in rv,
 'guard focus':'"guard_field".equals(id)' in rv and 'geo.optString("focus_file")' in rv,
 'position focus':'"inside_surface".equals(id)' in rv and '"size".equals(id)' in rv,
 'alignment overlay':'"alignment".equals(id)' in rv and 'geo.optString("overlay_file")' in rv,
 'artwork image':'"artwork".equals(id)' in rv and 'geo.optString("artwork_file")' in rv,
 'visual evidence title':'Визуальное доказательство' in rv,
 'circles explanation':'Кружки показывают найденные проблемные зоны' in rv,
 'full screen click':'largeEvidence(a,evidence,380)' in rv,
 'fallback text dialog':'if(evidence==null)' in rv and '.setMessage(msg.toString())' in rv,
 'alpha33 labels retained':'label="макет не по тт"' in rv and 'label="макет ок"' in rv,
 'alpha32 matrix retained':'TechnologyCheckMatrix.add(checks,effective)' in m,
 'FS retained':'.codes("FS").elem(1.5).neg(1.1).letter(5)' in o,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
