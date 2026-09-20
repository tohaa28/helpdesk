#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle');g=r('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java')
checks={
 'version code':'versionCode 340043' in b,
 'version name':"versionName '3.4.0-alpha43'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'dynamic stroke helper':'overlayBoxStroke' in g,
 'short-side scaling':'Math.min(Math.abs(x1-x0),Math.abs(y1-y0))*scale' in g,
 'field ratio 1.2 percent':'artwork?.015f:.012f' in g,
 'field minimum 1 px':'min=artwork?1.10f:1.00f' in g,
 'field max 4 px':'max=artwork?5.00f:4.00f' in g,
 'art max 5 px':'max=artwork?5.00f:4.00f' in g,
 'dynamic dash helper':'overlayDash' in g,
 'dash follows stroke':'stroke*3.2f' in g and 'stroke*2.1f' in g,
 'small element field frame dynamic':'saveSmallElementOverlay' in g and 'overlayBoxStroke(field.x0,field.y0,field.x1,field.y1,scale,false)' in g,
 'artwork evidence field dynamic':'saveArtworkEvidence' in g,
 'focus overlay dynamic':'saveFocusOverlay' in g,
 'full overlay dynamic':'saveOverlay' in g,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
