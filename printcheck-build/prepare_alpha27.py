#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
pb = repo / 'printcheck-build'
subprocess.run([sys.executable, str(pb / 'prepare_alpha26.py'), str(repo)], check=True)

src26 = repo / '.printcheck-alpha26'
src27 = repo / '.printcheck-alpha27'
if src27.exists():
    shutil.rmtree(src27)
shutil.copytree(src26, src27)

def replace_once(path, old, new):
    p = src27 / path
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise RuntimeError(f'alpha27 transform anchor missing in {path}: {old[:80]!r}')
    if s.count(old) != 1:
        raise RuntimeError(f'alpha27 transform anchor not unique in {path}: {old[:80]!r}')
    p.write_text(s.replace(old, new, 1), encoding='utf-8')

replace_once('app/build.gradle', 'versionCode 340026', 'versionCode 340027')
replace_once('app/build.gradle', "versionName '3.4.0-alpha26'", "versionName '3.4.0-alpha27'")
replace_once('app/src/main/java/ru/printcheck/android/MainActivity.java',
             'centered_issue_markers_v1',
             'centered_issue_markers_v2_rule_diameter_no_center_dot')

(src27 / 'app/src/main/java/ru/printcheck/android/MarkerSizeLogic.java').write_text(r'''package ru.printcheck.android;

/** Physical marker sizing for evidence overlays. */
final class MarkerSizeLogic {
    private MarkerSizeLogic() {}

    /** Marker diameter in output-image pixels. */
    static float diameterPx(double ruleMm,double pixelsPerMm,float outputScale){
        if(!(ruleMm>0)||!Double.isFinite(ruleMm)||!(pixelsPerMm>0)||!Double.isFinite(pixelsPerMm)||!(outputScale>0)||!Float.isFinite(outputScale))return 0f;
        return (float)(ruleMm*pixelsPerMm*outputScale);
    }

    static float radiusPx(double ruleMm,double pixelsPerMm,float outputScale){
        return diameterPx(ruleMm,pixelsPerMm,outputScale)*0.5f;
    }
}
''', encoding='utf-8')

replace_once('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java',
             'centered_features_v6_intersection_safe_reference_ruler',
             'rule_diameter_circles_v7_no_center_dot_reference_ruler')
p = src27 / 'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'
g = p.read_text(encoding='utf-8')
if 'centered_features_v6_intersection_safe_reference_ruler' in g:
    g = g.replace('centered_features_v6_intersection_safe_reference_ruler', 'rule_diameter_circles_v7_no_center_dot_reference_ruler')
p.write_text(g, encoding='utf-8')

replace_once('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java',
             '.put("cross_color_negative_gaps_ignored",true).put("cross_color_intersections_excluded",true);',
             '.put("cross_color_negative_gaps_ignored",true).put("cross_color_intersections_excluded",true).put("marker_diameter_mode","minimum-allowed-rule-mm").put("marker_center_symbol",false);')
replace_once('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java',
             'JSONObject j=new JSONObject().put("rule_mm",f.ruleMm).put("resolution_sufficient",f.resolutionSufficient)',
             'JSONObject j=new JSONObject().put("rule_mm",f.ruleMm).put("marker_diameter_mm",f.ruleMm).put("resolution_sufficient",f.resolutionSufficient)')
replace_once('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java',
'''        if(sr.positive!=null)drawIssueCircles(c,sr.positive.examples,hi.originX,hi.originY,scale,Color.rgb(255,214,0));
        if(sr.negative!=null)drawIssueCircles(c,sr.negative.examples,hi.originX,hi.originY,scale,Color.rgb(0,229,255));
        if(sr.single!=null)drawIssueCircles(c,sr.single.examples,hi.originX,hi.originY,scale,Color.rgb(255,128,0));''',
'''        double pxPerMm=ruler!=null&&ruler.valid?ruler.effectivePxPerMm:sr.pixelsPerMm;
        if(sr.positive!=null)drawIssueCircles(c,sr.positive,hi.originX,hi.originY,scale,pxPerMm,Color.rgb(255,214,0));
        if(sr.negative!=null)drawIssueCircles(c,sr.negative,hi.originX,hi.originY,scale,pxPerMm,Color.rgb(0,229,255));
        if(sr.single!=null)drawIssueCircles(c,sr.single,hi.originX,hi.originY,scale,pxPerMm,Color.rgb(255,128,0));''')
replace_once('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java',
'''    private static void drawIssueCircles(Canvas c,List<SmallElementAnalyzer.Box> boxes,int ox,int oy,float scale,int color){
        if(boxes==null||boxes.isEmpty())return;Paint halo=new Paint(Paint.ANTI_ALIAS_FLAG),p=new Paint(Paint.ANTI_ALIAS_FLAG);halo.setStyle(Paint.Style.STROKE);halo.setStrokeWidth(8.0f);halo.setColor(Color.rgb(20,24,28));p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(5.2f);p.setColor(color);ArrayList<float[]> placed=new ArrayList<>();
        for(SmallElementAnalyzer.Box b:boxes){float lx=(float)(Double.isFinite(b.centerX)?b.centerX:(b.x0+b.x1)*0.5),ly=(float)(Double.isFinite(b.centerY)?b.centerY:(b.y0+b.y1)*0.5);float cx=(ox+lx)*scale,cy=(oy+ly)*scale;float radius=18f;boolean near=false;for(float[] q:placed){float dx=cx-q[0],dy=cy-q[1];if(dx*dx+dy*dy<400f){near=true;break;}}if(near)continue;c.drawCircle(cx,cy,radius,halo);c.drawCircle(cx,cy,radius,p);c.drawLine(cx-6,cy,cx+6,cy,p);c.drawLine(cx,cy-6,cx,cy+6,p);if(b.rgb>=0){Paint sw=new Paint(Paint.ANTI_ALIAS_FLAG);sw.setStyle(Paint.Style.FILL);sw.setColor(Color.rgb((b.rgb>>16)&255,(b.rgb>>8)&255,b.rgb&255));c.drawCircle(cx,cy,5.5f,halo);c.drawCircle(cx,cy,4f,sw);}placed.add(new float[]{cx,cy});}
    }''',
'''    private static void drawIssueCircles(Canvas c,SmallElementAnalyzer.FeatureResult feature,int ox,int oy,float scale,double pxPerMm,int color){
        if(feature==null||feature.examples==null||feature.examples.isEmpty())return;
        float diameter=MarkerSizeLogic.diameterPx(feature.ruleMm,pxPerMm,scale);
        if(!(diameter>0))return;
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        float stroke=Math.max(.8f,Math.min(2.8f,diameter*.18f));
        float radius=Math.max(.4f,(diameter-stroke)*.5f);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(stroke);p.setColor(color);
        ArrayList<float[]> placed=new ArrayList<>();
        for(SmallElementAnalyzer.Box b:feature.examples){
            float lx=(float)(Double.isFinite(b.centerX)?b.centerX:(b.x0+b.x1)*0.5),ly=(float)(Double.isFinite(b.centerY)?b.centerY:(b.y0+b.y1)*0.5);
            float cx=(ox+lx)*scale,cy=(oy+ly)*scale;boolean near=false;
            float minCenterDistance=Math.max(diameter*.55f,4f);
            for(float[] q:placed){float dx=cx-q[0],dy=cy-q[1];if(dx*dx+dy*dy<minCenterDistance*minCenterDistance){near=true;break;}}
            if(near)continue;
            c.drawCircle(cx,cy,radius,p);
            placed.add(new float[]{cx,cy});
        }
    }''')

replace_once('tests/run_core.sh',
             'MeasurementCalibrationLogic,ArtworkColorLayerLogic}.java',
             'MeasurementCalibrationLogic,ArtworkColorLayerLogic,MarkerSizeLogic}.java')
ct = src27 / 'tests/CoreTests.java'
cs = ct.read_text(encoding='utf-8')
anchor = '  System.out.println("TOTAL "+passed+" passed);\n'
if anchor not in cs:
    raise RuntimeError('CoreTests final anchor missing')
extra = '''  test("alpha27 marker diameter equals physical rule",()->{float d=MarkerSizeLogic.diameterPx(.20,40.0f,1.0f);ok(Math.abs(d-8.0f)<.0001f);ok(Math.abs(MarkerSizeLogic.radiusPx(.20,40.0f,1.0f)-4.0f)<.0001f);});
  test("alpha27 marker diameter respects evidence scale",()->{float d=MarkerSizeLogic.diameterPx(.30,30.0f,.5f);ok(Math.abs(d-4.5f)<.0001f);});
  test("alpha27 invalid marker rule produces no circle",()->{ok(MarkerSizeLogic.diameterPx(-1,30.0f,1.0f)==0f);ok(MarkerSizeLogic.diameterPx(.2,0,1.0f)==0f);ok(MarkerSizeLogic.diameterPx(.2,30.0f,0)==0f);});
'''
ct.write_text(cs.replace(anchor, extra + anchor, 1), encoding='utf-8')

(src27 / 'tests/audit_alpha27.py').write_text(r'''from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(rel): return (root/rel).read_text(encoding='utf-8')
g=read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java')
m=read('app/src/main/java/ru/printcheck/android/MainActivity.java')
s=read('app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java')
ms=read('app/src/main/java/ru/printcheck/android/MarkerSizeLogic.java')
b=read('app/build.gradle')
start=g.index('private static void drawIssueCircles')
end=g.index('private static Bitmap renderPage',start)
draw=g[start:end]
checks={
'version code': 'versionCode 340027' in b,
'version name': "versionName '3.4.0-alpha27'" in b,
'app id': "applicationId 'ru.printcheck.android'" in b,
'persistent signer': 'alphaPersistent' in b,
'alpha26 geometry retained': 'per-color-medial-gap-v2-intersection-safe' in s and 'distanceToOtherColour' in s and 'negativeSameColor' in s,
'centered geometry retained': 'centerX' in s and 'centerY' in s,
'new technical marker': 'centered_issue_markers_v2_rule_diameter_no_center_dot' in m,
'new marker style': 'rule_diameter_circles_v7_no_center_dot_reference_ruler' in g,
'marker diameter mode json': 'marker_diameter_mode' in g and 'minimum-allowed-rule-mm' in g,
'center symbol false json': 'marker_center_symbol",false' in g,
'per-feature diameter json': 'marker_diameter_mm' in g,
'marker size helper exists': 'class MarkerSizeLogic' in ms,
'diameter is rule times pixels/mm': 'ruleMm*pixelsPerMm*outputScale' in ms,
'geometry uses physical rule diameter': 'MarkerSizeLogic.diameterPx(feature.ruleMm,pxPerMm,scale)' in draw,
'no fixed 18px radius': 'radius=18f' not in draw and 'float radius=18f' not in g,
'no center crosshair': 'drawLine(' not in draw,
'no center color dot': 'b.rgb' not in draw and 'Paint sw' not in draw,
'one hollow circle only': draw.count('c.drawCircle(cx,cy,radius,p)')==1,
'circle outer diameter compensated for stroke': '(diameter-stroke)*.5f' in draw,
'reference ruler retained': 'drawReferenceRuler' in g and 'reference_ruler' in g,
'cross color exclusion retained': 'cross_color_intersections_excluded' in g and 'cross_color_negative_gaps_ignored' in g,
'performance retained': 'ARTWORK_TARGET_DPI = 720' in g and 'MAX_ARTWORK_PIXELS = 4_000_000L' in g and 'collectRegistrationSamples' in g,
'constructor safety retained': 'artwork_reference_authoritative' in g and 'if(!authoritativeArtworkReference)' in g,
'no synthetic mapper': not (root/'app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java').exists(),
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
if bad: raise SystemExit('FAILED: '+', '.join(bad))
print(f'TOTAL {len(checks)}/{len(checks)} passed')
''', encoding='utf-8')

for rel in ['README_RU.md','PROGRESS.md']:
    p = src27 / rel
    s = p.read_text(encoding='utf-8').replace('3.4.0-alpha26','3.4.0-alpha27')
    p.write_text(s, encoding='utf-8')
with (src27 / 'README_RU.md').open('a', encoding='utf-8') as f:
    f.write('\n\n## alpha27 — размер маркеров по нормативу\n- Центральные точки, цветовые точки и перекрестия внутри маркеров удалены.\n- Внешний диаметр каждого круга равен минимально допустимому физическому размеру соответствующей проверки после калибровки по эталонной линейке.\n- Positive использует positive rule, negative — negative rule, single object — minSingleElementMm.\n- Центр круга остаётся в вычисленном центре реального узкого места/промежутка/объекта.\n')
with (src27 / 'PROGRESS.md').open('a', encoding='utf-8') as f:
    f.write('\n\n## alpha27\n- Hollow issue circles: no center dot, color swatch or crosshair.\n- Circle outer diameter is physically calibrated to the corresponding minimum allowed rule in mm.\n- Marker centers from alpha26 are retained unchanged.\n')

build = (src27 / 'app/build.gradle').read_text(encoding='utf-8')
main = (src27 / 'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
geom = (src27 / 'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(encoding='utf-8')
small = (src27 / 'app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java').read_text(encoding='utf-8')
marker = (src27 / 'app/src/main/java/ru/printcheck/android/MarkerSizeLogic.java').read_text(encoding='utf-8')
draw = geom[geom.index('private static void drawIssueCircles'):geom.index('private static Bitmap renderPage')]
required = {
    'versionCode 340027': 'versionCode 340027' in build,
    'versionName alpha27': "versionName '3.4.0-alpha27'" in build,
    'application id retained': "applicationId 'ru.printcheck.android'" in build,
    'persistent signer retained': 'alphaPersistent' in build and 'printcheck-alpha-test.p12' in build,
    'alpha26 intersection-safe geometry retained': 'per-color-medial-gap-v2-intersection-safe' in small and 'negativeSameColor' in small and 'distanceToOtherColour' in small,
    'new marker technical id': 'centered_issue_markers_v2_rule_diameter_no_center_dot' in main,
    'new marker style': 'rule_diameter_circles_v7_no_center_dot_reference_ruler' in geom,
    'marker diameter json': 'marker_diameter_mm' in geom and 'marker_diameter_mode' in geom,
    'center symbol false': 'marker_center_symbol",false' in geom,
    'marker helper': 'ruleMm*pixelsPerMm*outputScale' in marker,
    'physical diameter used': 'MarkerSizeLogic.diameterPx(feature.ruleMm,pxPerMm,scale)' in draw,
    'no fixed radius': 'radius=18f' not in draw,
    'no center cross': 'drawLine(' not in draw,
    'no center color swatch': 'b.rgb' not in draw and 'Paint sw' not in draw,
    'single hollow circle': draw.count('c.drawCircle(cx,cy,radius,p)') == 1,
    'stroke compensated diameter': '(diameter-stroke)*.5f' in draw,
    'reference ruler retained': 'reference_ruler' in geom and 'drawReferenceRuler' in geom,
    'performance retained': 'ARTWORK_TARGET_DPI = 720' in geom and 'MAX_ARTWORK_PIXELS = 4_000_000L' in geom and 'collectRegistrationSamples' in geom,
    'no synthetic mapper': not (src27 / 'app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java').exists(),
}
bad = [k for k,v in required.items() if not v]
if bad:
    raise RuntimeError('alpha27 generated source invariant failure: ' + ', '.join(bad))

signing = src27 / 'signing/printcheck-alpha-test.p12'
expected_signing_sha = '153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    raise RuntimeError('persistent alpha signing key missing from generated alpha27 tree')
if hashlib.sha256(signing.read_bytes()).hexdigest() != expected_signing_sha:
    raise RuntimeError('alpha27 signing identity changed unexpectedly')

print('Prepared canonical PrintCheck 3.4.0-alpha27 source')
print('source:', src27)
print('signing_sha256:', expected_signing_sha)
