#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
pb=repo/'printcheck-build'
subprocess.run([sys.executable,str(pb/'prepare_alpha14.py'),str(repo)],check=True)
src14=repo/'.printcheck-alpha14'
src15=repo/'.printcheck-alpha15'
if src15.exists(): shutil.rmtree(src15)
shutil.copytree(src14,src15)

def read(rel): return (src15/rel).read_text(encoding='utf-8')
def write(rel,s): (src15/rel).write_text(s,encoding='utf-8')

# Version.
s=read('app/build.gradle').replace('versionCode 340014','versionCode 340015').replace("versionName '3.4.0-alpha14'","versionName '3.4.0-alpha15'")
write('app/build.gradle',s)

# MainActivity: restore alpha7 geometry reference semantics while retaining later constructor mapping.
p='app/src/main/java/ru/printcheck/android/MainActivity.java'
s=read(p).replace('Preflight 3.4 alpha14','Preflight 3.4 alpha15')
s=s.replace('constructor_geometry_primary_v1+','constructor_identity_application_geometry_v1+')
s=s.replace('no_skipped_checks_v1+small_element_proof_v2+clickable_reports_v1','alpha7_application_geometry_v1+no_skipped_checks_v1+small_element_proof_v2+clickable_reports_v1')
s=s.replace(
'Preflight 3.4 alpha15: полный чек-лист без пропусков, восстановленный анализ мелких позитивных/негативных элементов с доказательным изображением, кликабельные PDF-отчёты заказа и позиций, компактные раскрывающиеся результаты и пакетная проверка; групповые связи размеров по базовому артикулу, сравнение макета с PDF-конструктором, геометрия, рабочее поле, позитивные/негативные мелкие элементы и структурная проверка PDF.',
'Preflight 3.4 alpha15: полный чек-лист без пропусков; конструктор используется для идентификации позиции и общего совмещения, а геометрия, поле нанесения и мелкие элементы рассчитываются по конкретному PDF-шаблону выбранного нанесения, как в рабочей alpha7. Сохранены доказательные изображения, кликабельные PDF-отчёты заказа и позиций, компактные раскрывающиеся результаты и пакетная проверка.'
)
lines=s.splitlines()
new_geo='''     if("constructor".equals(c.pdf.role)&&shared!=null){try{PreflightRules.RuleSet rules=rulesForItem(root,shared);Models.RemotePdf app=findApplicationTemplate(applicationOk,shared);if(app==null)throw new IOException("Для item_id "+shared+" не найден PDF-шаблон выбранного нанесения. Геометрия по общему конструктору запрещена.");int gdpi=RasterPdfIndexer.commonDpi(Arrays.asList(l.pdf,app));Models.PdfIndex gl=gdpi==dpi?l:RasterPdfIndexer.index(l.pdf,gdpi,x->update("Геометрия макета: "+x,48));Models.PdfIndex ga=RasterPdfIndexer.index(app,gdpi,x->update("Шаблон нанесения: "+x,48));Models.CompareStats gst=new Models.CompareStats();List<Models.Occurrence> gocc=bestOnly(RasterMatcher.compare(gl,ga,gst));Models.Occurrence gb=gocc.isEmpty()?null:gocc.get(0);comparison.put("geometry_reference_file",app.file.getName()).put("geometry_reference_name",app.displayName).put("geometry_reference_type","application").put("geometry_dpi",gdpi).put("geometry_candidate_count",gocc.size()).put("geometry_best_coverage",gst.bestCoverage).put("geometry_best_score",gst.bestScore);trace(new JSONObject().put("event","geometry-application-reference").put("item_id",shared).put("layout",l.pdf.file.getName()).put("application",app.file.getName()).put("dpi",gdpi).put("candidates",gocc.size()).put("coverage",gst.bestCoverage).put("score",gst.bestScore));if(gb==null)throw new IOException("Конкретный шаблон выбранного нанесения не совмещён с макетом; анализ поля и мелких элементов по общему конструктору не выполняется.");File overlay=new File(new File(runDir,"preflight"),"overlay_"+Safety.filename(shared+".pdf").replaceAll("\\\\.pdf$",".png"));JSONObject geo=GeometryAnalyzer.analyze(l.pdf.file,gb.layoutPage,app.file,gb.constructorPage,gdpi,gb,rules,overlay);geo.put("reference_role","application").put("reference_file",app.file.getName()).put("reference_name",app.displayName);comparison.put("geometry",geo);PdfObjectInspector.Result pr=pdfObjectResults.get(l.pdf.file.getName());if(pr!=null){JSONObject art=geo.optJSONObject("artwork");PdfObjectInspector.FontScope fs;if(geo.optBoolean("detected")&&art!=null)fs=pr.fontsInArtwork(art.optDouble("x0"),art.optDouble("y0"),art.optDouble("x1"),art.optDouble("y1"),gdpi,gb.layoutPage);else{fs=new PdfObjectInspector.FontScope();fs.totalTextShows=pr.textShows;fs.locatedTextShows=pr.locatedTextShows;fs.unlocatedTextShows=pr.unlocatedTextShows;fs.available=!pr.hasAnyLiveText();fs.reason=pr.hasAnyLiveText()?"Само нанесение не выделено; шрифты вне нанесения не являются ошибкой, поэтому нужна ручная проверка.":"В PDF нет операторов живого текста.";}comparison.put("font_scope",fontScopeJson(fs));trace(new JSONObject(fontScopeJson(fs).toString()).put("event","font-scope").put("item_id",shared).put("file",l.pdf.file.getName()));}}catch(Exception gx){comparison.put("geometry_error",String.valueOf(gx.getMessage()));trace(new JSONObject().put("event","geometry-warning").put("item_id",shared).put("message",String.valueOf(gx.getMessage())));}}'''
replaced=False
for i,line in enumerate(lines):
    if 'if("constructor".equals(c.pdf.role)&&shared!=null){try{' in line:
        lines[i]=new_geo
        replaced=True
        break
if not replaced: raise RuntimeError('alpha14 geometry block not found')
s='\n'.join(lines)+'\n'
helper=' private static Models.RemotePdf findApplicationTemplate(List<Models.RemotePdf> apps,String itemId){if(apps==null||itemId==null)return null;Models.RemotePdf fallback=null;for(Models.RemotePdf p:apps){if(p.itemIds.contains(itemId)){if(fallback==null)fallback=p;if(p.file!=null&&p.file.isFile())return p;}}return fallback;}\n'
marker=' private static boolean sameItem(Models.RemotePdf a,Models.RemotePdf b)'
if helper.strip() not in s: s=s.replace(marker,helper+marker)
write(p,s)

# Public technology page parser: never store a whole-page text blob as one requirement.
p='app/src/main/java/ru/printcheck/android/OfficialRequirements.java'
s=read(p)
old='for(int j=i;j<end;j++){String x=clean(lines[j]);if(!x.isEmpty()&&!out.contains(x))out.add(x);}'
new='for(int j=i;j<end;j++){String x=clean(lines[j]);if(x.length()>700)continue;if(!x.isEmpty()&&!out.contains(x))out.add(x);}'
if old not in s: raise RuntimeError('feature extractor line not found')
write(p,s.replace(old,new))

# Constructor source formats are not errors if a PDF for the same constructor article exists.
p='app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java'
s=read(p)
old='out.put("unsupported", dedupe(unsupported, "url", null));'
new='out.put("unsupported", filterUnsupportedConstructorDuplicates(dedupe(unsupported, "url", null), constructors));'
if old not in s: raise RuntimeError('unsupported assignment not found')
s=s.replace(old,new)
helper2='''    private static JSONArray filterUnsupportedConstructorDuplicates(JSONArray unsupported, JSONArray constructors) throws JSONException {
        HashSet<String> pdfArticles=new HashSet<>();
        for(int i=0;i<constructors.length();i++){JSONObject c=constructors.optJSONObject(i);String a=c==null?"":c.optString("article","");if(!a.isEmpty()&&!"null".equals(a))pdfArticles.add(a);}
        JSONArray out=new JSONArray();
        for(int i=0;i<unsupported.length();i++){JSONObject u=unsupported.optJSONObject(i);if(u==null){out.put(unsupported.opt(i));continue;}String reason=u.optString("reason","");String a=u.optString("article","");if(reason.contains("Формат конструктора требует PDF")&&pdfArticles.contains(a))continue;out.put(u);}
        return out;
    }

'''
marker='    private static boolean isAuxiliaryConstructorPdf'
if 'filterUnsupportedConstructorDuplicates' not in s[s.find(marker)-1000:s.find(marker)]:
    s=s.replace(marker,helper2+marker)
write(p,s)

# Core regression test for the public features parser.
p='tests/CoreTests.java'
s=read(p)
needle='  test("official catalog thresholds",()->{PreflightRules.RuleSet lm=PreflightRules.parse("LM1","Лазерная гравировка","",Collections.emptyList());ok(Math.abs(lm.effectivePositiveMm()-.1)<1e-6&&Math.abs(lm.effectiveNegativeMm()-.2)<1e-6);PreflightRules.RuleSet uv=PreflightRules.parse("UV-DTF2","UV-DTF","",Collections.emptyList());ok(Math.abs(uv.effectivePositiveMm()-.6)<1e-6&&Math.abs(uv.effectiveNegativeMm()-.6)<1e-6&&Math.abs(uv.minSingleElementMm-2)<1e-6&&uv.minRasterDpi==300);});\n'
test='  test("technology feature extractor rejects whole-page blobs",()->{String huge="UV-DTF2 "+"x".repeat(900);ok(OfficialRequirements.extractFeatureTexts("<html><body>"+huge+"</body></html>","UV-DTF2").isEmpty());});\n'
if test not in s:
    if needle not in s: raise RuntimeError('core test insertion point missing')
    s=s.replace(needle,needle+test)
write(p,s)

# Source-level anti-regression audit.
audit='''from pathlib import Path
r=Path(__file__).resolve().parents[1]
main=(r/'app/src/main/java/ru/printcheck/android/MainActivity.java').read_text(encoding='utf-8')
geo=(r/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(encoding='utf-8')
off=(r/'app/src/main/java/ru/printcheck/android/OfficialRequirements.java').read_text(encoding='utf-8')
http=(r/'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java').read_text(encoding='utf-8')
gradle=(r/'app/build.gradle').read_text(encoding='utf-8')
checks={
 'version': "versionName '3.4.0-alpha15'" in gradle and 'versionCode 340015' in gradle,
 'alpha7 geometry reference': 'alpha7_application_geometry_v1' in main and 'geometry_reference_type","application"' in main,
 'no constructor geometry fallback': 'Геометрия по общему конструктору запрещена' in main,
 'application template selector': 'findApplicationTemplate(applicationOk,shared)' in main,
 'pair adaptive dpi': 'commonDpi(Arrays.asList(l.pdf,app))' in main,
 'positive negative retained': 'small_elements_positive_negative_v1' in main and 'SmallElementAnalyzer.analyze' in geo,
 'boundary suppression retained': 'suppressProductionBoundary(hi,target)' in geo,
 'proof image retained': 'saveSmallElementOverlay' in geo and 'component_circles_v3_high_contrast' in geo,
 'no skipped checklist retained': 'ensureCoreChecklist' in main,
 'pdf links retained': 'position_report_file' in main and 'PdfReportWriter.writePosition' in main,
 'feature blob cap': 'x.length()>700' in off,
 'cdr duplicate filter': 'filterUnsupportedConstructorDuplicates' in http,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
if failed: raise SystemExit('alpha15 audit failed: '+', '.join(failed))
print('TOTAL',len(checks),'alpha15 source invariants passed')
'''
(src15/'tests/audit_alpha15.py').write_text(audit,encoding='utf-8')

# Docs.
readme=read('README_RU.md')
write('README_RU.md','# PrintCheck Android 3.4.0-alpha15\n\n## Главное исправление alpha15\n- Геометрия, поле нанесения и поиск мелких элементов снова используют конкретный application-template выбранного нанесения, как в рабочей alpha7.\n- Общий конструктор используется для идентификации артикула и общего совмещения изделия, но запрещён как эталон поля нанесения.\n- Application-template индексируется только для связанной позиции и на адаптивном DPI, поэтому огромные PDF не участвуют в общем индексе заказа.\n- Позитивные и негативные мелкие элементы используют прежнюю рабочую морфологию alpha7; пунктирная рамка подавляется перед анализом.\n- Если application-template не найден или не совмещён, проверка не подменяется конструктором: зависимые пункты остаются ручными с причиной.\n- CDR/AI/EPS-дубликат конструктора не выводится как необработанный файл, если PDF того же артикула уже найден.\n- Парсер технологических особенностей не переносит в отчёт текст всей страницы Gifts.\n\nВсе функции alpha14 сохранены.\n\n'+readme)
progress=read('PROGRESS.md')
write('PROGRESS.md','# 3.4.0-alpha15\n\n- restored alpha7 application-template geometry path;\n- constructor retained for identity/general registration;\n- on-demand application-template match with adaptive pair DPI;\n- small-element morphology and proof image preserved;\n- no constructor fallback for production field;\n- duplicate unsupported constructor formats suppressed when PDF exists;\n- giant technology-page blobs rejected;\n- alpha15 regression audit added.\n\n'+progress)

# Final verification.
required=[
 ("app/build.gradle","versionName '3.4.0-alpha15'"),
 (p if False else "app/src/main/java/ru/printcheck/android/MainActivity.java","alpha7_application_geometry_v1"),
 ("app/src/main/java/ru/printcheck/android/MainActivity.java","geometry_reference_type\",\"application"),
 ("app/src/main/java/ru/printcheck/android/MainActivity.java","findApplicationTemplate(applicationOk,shared)"),
 ("app/src/main/java/ru/printcheck/android/OfficialRequirements.java","x.length()>700"),
 ("app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java","filterUnsupportedConstructorDuplicates"),
]
for rel,tok in required:
    if tok not in read(rel): raise RuntimeError('alpha15 verification missing '+tok)
print('Prepared',src15)
