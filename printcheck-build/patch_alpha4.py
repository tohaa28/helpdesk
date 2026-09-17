from pathlib import Path
import sys
root=Path(sys.argv[1])
rh=root/'app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java'
s=rh.read_text()
old='''            if (isMda) {\n                JSONObject rel = new JSONObject()\n                        .put("url", url)\n                        .put("label", text.isEmpty() ? filename(path) : text)\n                        .put("item_id", JSONObject.NULL)\n                        .put("relation_source", "popup-uploaded-maket");\n                layouts.put(rel);\n                trace.put(new JSONObject(rel.toString()).put("event", "layout-link"));\n                continue;\n            }'''
new='''            if (isMda) {\n                String sourceName = sourceNameNear(html, a.start(), a.end());\n                JSONObject item = uniqueItemForSourceName(sourceName, shell.optJSONArray("items"));\n                JSONObject rel = new JSONObject()\n                        .put("url", url)\n                        .put("label", text.isEmpty() ? filename(path) : text)\n                        .put("source_name", sourceName == null ? JSONObject.NULL : sourceName)\n                        .put("item_id", item == null ? JSONObject.NULL : item.optString("item_id"))\n                        .put("article", item == null ? JSONObject.NULL : item.optString("article"))\n                        .put("relation_source", item == null ? "popup-source-name-unresolved" : "popup-source-name-unique");\n                layouts.put(rel);\n                trace.put(new JSONObject(rel.toString()).put("event", "layout-link"));\n                continue;\n            }'''
if old not in s: raise SystemExit('mda block not found')
s=s.replace(old,new)
insert='''\n    private static String sourceNameNear(String html, int start, int end) {\n        int b = html.lastIndexOf("<div class=\\\"j_maket_host", start);\n        if (b < 0) b = Math.max(0, start - 1000);\n        int e = html.indexOf("</g-gallery>", end);\n        if (e < 0) e = Math.min(html.length(), end + 1600);\n        String block = html.substring(b, Math.min(html.length(), e));\n        Matcher m = Pattern.compile("Исходное имя закачанного файла[^>]*>([^<]+)</span>", Pattern.CASE_INSENSITIVE | Pattern.DOTALL).matcher(block);\n        return m.find() ? decode(m.group(1)).trim() : null;\n    }\n\n    private static JSONObject uniqueItemForSourceName(String sourceName, JSONArray items) {\n        if (sourceName == null || items == null) return null;\n        Set<String> src = nameTokens(sourceName);\n        if (src.isEmpty()) return null;\n        int best = 0; JSONObject winner = null; boolean tie = false;\n        for (int i=0;i<items.length();i++) {\n            JSONObject it = items.optJSONObject(i); if (it == null) continue;\n            Set<String> dst = nameTokens(it.optString("name", ""));\n            int score=0; for(String t:src) if(dst.contains(t)) score++;\n            if (score > best) { best=score; winner=it; tie=false; }\n            else if (score > 0 && score == best) tie=true;\n        }\n        return best > 0 && !tie ? winner : null;\n    }\n\n    private static Set<String> nameTokens(String value) {\n        LinkedHashSet<String> out = new LinkedHashSet<>();\n        if (value == null) return out;\n        String n = value.toLowerCase(Locale.ROOT).replace('ё','е').replaceAll("\\.pdf$", " ");\n        for(String t:n.split("[^a-zа-я0-9]+")) {\n            if(t.length()<4) continue;\n            if(t.equals("тираж")||t.equals("макет")||t.equals("заказ")||t.equals("формат")) continue;\n            out.add(t);\n        }\n        return out;\n    }\n'''
marker='''    private static String unwrapPopupHtml(String response, JSONArray trace) throws Exception {'''
if marker not in s: raise SystemExit('marker missing')
s=s.replace(marker,insert+'\n'+marker)
rh.write_text(s)
ma=root/'app/src/main/java/ru/printcheck/android/MainActivity.java'
s=ma.read_text()
s=s.replace('''ArrayList<Models.RemotePdf> layouts=parse(root.getJSONArray("layouts"),false),templates=parse(root.getJSONArray("constructors"),true);''','''ArrayList<Models.RemotePdf> layouts=parse(root.getJSONArray("layouts"),false),templates=parse(root.getJSONArray("constructors"),true),applicationTemplates=parse(root.optJSONArray("applicationTemplates"),true);''')
s=s.replace('''ArrayList<Models.RemotePdf> all=new ArrayList<>(layouts);all.addAll(templates);int i=0;''','''ArrayList<Models.RemotePdf> all=new ArrayList<>(layouts);all.addAll(templates);all.addAll(applicationTemplates);int i=0;''')
oldloop='''   ArrayList<Models.Occurrence> found=new ArrayList<>();int cmp=0,total=li.size()*ci.size();\n   for(Models.PdfIndex l:li)for(Models.PdfIndex c:ci){ensure();Models.CompareStats st=new Models.CompareStats();List<Models.Occurrence> occ=RasterMatcher.compare(l,c,st);cmp++;'''
newloop='''   ArrayList<Models.Occurrence> found=new ArrayList<>();int cmp=0,total=0;\n   for(Models.PdfIndex l:li)for(Models.PdfIndex c:ci)if(!l.pdf.itemIds.isEmpty()&&!c.pdf.itemIds.isEmpty()&&!Collections.disjoint(l.pdf.itemIds,c.pdf.itemIds))total++;\n   for(Models.PdfIndex l:li)for(Models.PdfIndex c:ci){ensure();if(l.pdf.itemIds.isEmpty()||c.pdf.itemIds.isEmpty())continue;if(!Collections.disjoint(l.pdf.itemIds,c.pdf.itemIds)){}else continue;Models.CompareStats st=new Models.CompareStats();List<Models.Occurrence> occ=bestOnly(RasterMatcher.compare(l,c,st));cmp++;'''
if oldloop not in s: raise SystemExit('compare loop missing')
s=s.replace(oldloop,newloop)
s=s.replace(''' private ArrayList<Models.RemotePdf> parse(JSONArray arr,boolean cons)throws Exception{\n  if(arr.length()>100)''',''' private ArrayList<Models.RemotePdf> parse(JSONArray arr,boolean cons)throws Exception{\n  if(arr==null)return new ArrayList<>();\n  if(arr.length()>100)''')
helper='''\n private static List<Models.Occurrence> bestOnly(List<Models.Occurrence> src){\n  if(src.size()<2)return src;\n  src.sort((a,b)->Double.compare(b.score,a.score));\n  Models.Occurrence best=src.get(0), second=src.get(1);\n  if(best.coverage>=0.75 || best.score-second.score>=0.12)return Collections.singletonList(best);\n  return src;\n }\n'''
marker2=''' private JSONObject occurrence(Models.Occurrence o,JSONArray positions,int dpi)throws Exception{'''
s=s.replace(marker2,helper+'\n'+marker2)
ma.write_text(s)
for p in [root/'app/build.gradle', root/'app/build.gradle.kts']:
 if p.exists():
  x=p.read_text();x=x.replace('3.1.0-alpha3','3.1.0-alpha4').replace('versionCode 310003','versionCode 310004').replace('versionCode = 310003','versionCode = 310004');p.write_text(x)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in {'.java','.xml','.md','.txt','.json','.js','.cjs'}:
  try:
   x=p.read_text();
   if '3.1.0-alpha3' in x:p.write_text(x.replace('3.1.0-alpha3','3.1.0-alpha4'))
  except: pass
print('patched alpha4')
