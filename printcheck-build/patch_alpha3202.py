from pathlib import Path

root = Path(__import__("sys").argv[1])

# Models: keep template and application as separate domain fields.
p = root / "app/src/main/java/ru/printcheck/android/Models.java"
s = p.read_text()
s = s.replace(
    "String url, label, displayName, article, sha256, role;",
    "String url, label, displayName, article, sha256, role, templateName, applicationLabel, applicationCode, applicationName, applicationSize;"
)
p.write_text(s)

# Parser: application PDF metadata must not be merged with template/product name.
p = root / "app/src/main/java/ru/printcheck/android/ReadOnlyHttp.java"
s = p.read_text()
old = '''                String productName = meta.optString("product_name", "");
                String applicationLabel = meta.optString("application_label", "");
                String displayName;
                if (!productName.isEmpty() && !applicationLabel.isEmpty()) displayName = productName + " · " + applicationLabel;
                else if (!productName.isEmpty()) displayName = productName + " · шаблон нанесения";
                else displayName = (article == null ? "Шаблон нанесения" : "Шаблон нанесения арт. " + article);
                JSONObject rel = new JSONObject()
                        .put("url", url)
                        .put("label", text.isEmpty() ? "Скачать PDF" : text)
                        .put("display_name", displayName)
                        .put("product_name", productName.isEmpty() ? JSONObject.NULL : productName)
                        .put("application_label", applicationLabel.isEmpty() ? JSONObject.NULL : applicationLabel)
                        .put("item_id", itemId == null ? JSONObject.NULL : itemId)
                        .put("article", article == null ? JSONObject.NULL : article)
                        .put("relation_source", itemId == null ? "orderitem-template-unresolved" : "orderitemid-query");'''
new = '''                String productName = meta.optString("product_name", "");
                String applicationLabel = meta.optString("application_label", "");
                JSONObject application = splitApplication(applicationLabel);
                String templateName = productName;
                if (templateName.isEmpty()) templateName = article == null ? "Шаблон товара" : "Шаблон товара · арт. " + article;
                JSONObject rel = new JSONObject()
                        .put("url", url)
                        .put("label", text.isEmpty() ? "Скачать PDF" : text)
                        .put("display_name", application.optString("name", "Нанесение") + (application.optString("code", "").isEmpty() ? "" : " [" + application.optString("code") + "]"))
                        .put("template_name", templateName)
                        .put("product_name", productName.isEmpty() ? JSONObject.NULL : productName)
                        .put("application_label", applicationLabel.isEmpty() ? JSONObject.NULL : applicationLabel)
                        .put("application_code", application.optString("code", "").isEmpty() ? JSONObject.NULL : application.optString("code"))
                        .put("application_name", application.optString("name", "").isEmpty() ? JSONObject.NULL : application.optString("name"))
                        .put("application_size", application.optString("size", "").isEmpty() ? JSONObject.NULL : application.optString("size"))
                        .put("item_id", itemId == null ? JSONObject.NULL : itemId)
                        .put("article", article == null ? JSONObject.NULL : article)
                        .put("relation_source", itemId == null ? "orderitem-template-unresolved" : "orderitemid-query");'''
if old not in s:
    raise SystemExit("ReadOnlyHttp application block not found")
s = s.replace(old, new)
marker = '    private static JSONObject applicationTemplateMeta(String html, int anchorStart, int anchorEnd) {'
helper = r'''
    private static JSONObject splitApplication(String raw) {
        JSONObject out = new JSONObject();
        String value = raw == null ? "" : raw.trim();
        if (value.isEmpty()) return out;
        String code = "", name = value, size = "";
        Matcher cm = Pattern.compile("^\\[([^\\]]{1,24})\\]\\s*(.*)$").matcher(name);
        if (cm.find()) { code = cm.group(1).trim(); name = cm.group(2).trim(); }
        Matcher sm = Pattern.compile("\\(([^()]*(?:мм|см|mm|cm)[^()]*)\\)\\s*$", Pattern.CASE_INSENSITIVE).matcher(name);
        if (sm.find()) { size = sm.group(1).trim(); name = name.substring(0, sm.start()).trim(); }
        if (code.isEmpty()) {
            Matcher colon = Pattern.compile("^([A-ZА-Я]{1,8}\\d*)\\s*[:—-]\\s*(.+)$", Pattern.CASE_INSENSITIVE).matcher(name);
            if (colon.find()) { code = colon.group(1).trim().toUpperCase(Locale.ROOT); name = colon.group(2).trim(); }
        }
        try {
            if (!code.isEmpty()) out.put("code", code);
            if (!name.isEmpty()) out.put("name", name);
            if (!size.isEmpty()) out.put("size", size);
            out.put("raw", value);
        } catch (JSONException ignored) {}
        return out;
    }

'''
if "private static JSONObject splitApplication" not in s:
    s = s.replace(marker, helper + marker)
p.write_text(s)

# Preserve separated metadata through RemotePdf -> detailed comparisons -> manifest.
p = root / "app/src/main/java/ru/printcheck/android/MainActivity.java"
s = p.read_text()
old = '''String display=o.optString("display_name","");if(display.isEmpty())display=o.optString("source_name",label);if("application".equals(role)){String a=article==null||article.isEmpty()?"item":article;String id=item.isEmpty()?String.valueOf(i+1):item;label="application_"+a+"_"+id+".pdf";}String key=url+"|"+article+"|"+role;Models.RemotePdf p=out.get(key);if(p==null){p=new Models.RemotePdf(url,label,article,role);p.displayName=display;out.put(key,p);}if(!item.isEmpty()&&!item.equals("null"))p.itemIds.add(item);}return new ArrayList<>(out.values());'''
new = '''String display=o.optString("display_name","");if(display.isEmpty())display=o.optString("source_name",label);if("application".equals(role)){String a=article==null||article.isEmpty()?"item":article;String id=item.isEmpty()?String.valueOf(i+1):item;label="application_"+a+"_"+id+".pdf";}String key=url+"|"+article+"|"+role;Models.RemotePdf p=out.get(key);if(p==null){p=new Models.RemotePdf(url,label,article,role);p.displayName=display;p.templateName=o.optString("template_name","");p.applicationLabel=o.optString("application_label","");p.applicationCode=o.optString("application_code","");p.applicationName=o.optString("application_name","");p.applicationSize=o.optString("application_size","");out.put(key,p);}if(!item.isEmpty()&&!item.equals("null"))p.itemIds.add(item);}return new ArrayList<>(out.values());'''
if old not in s:
    raise SystemExit("MainActivity parse block not found")
s = s.replace(old, new)
s = s.replace(
    '.put("reference_name",c.pdf.displayName).put("reference_type",c.pdf.role).put("candidate_count",occ.size())',
    '.put("reference_name",c.pdf.displayName).put("reference_type",c.pdf.role).put("template_name",emptyNull(c.pdf.templateName)).put("application_label",emptyNull(c.pdf.applicationLabel)).put("application_code",emptyNull(c.pdf.applicationCode)).put("application_name",emptyNull(c.pdf.applicationName)).put("application_size",emptyNull(c.pdf.applicationSize)).put("candidate_count",occ.size())'
)
s = s.replace(
    '.put("display_name",p.displayName).put("item_ids",new JSONArray(p.itemIds))',
    '.put("display_name",p.displayName).put("template_name",emptyNull(p.templateName)).put("application_label",emptyNull(p.applicationLabel)).put("application_code",emptyNull(p.applicationCode)).put("application_name",emptyNull(p.applicationName)).put("application_size",emptyNull(p.applicationSize)).put("item_ids",new JSONArray(p.itemIds))'
)
marker = ' private static boolean sameItem(Models.RemotePdf a,Models.RemotePdf b){'
if "emptyNull(String s)" not in s:
    s = s.replace(marker, ' private static Object emptyNull(String s){return s==null||s.isEmpty()?JSONObject.NULL:s;}\\n' + marker)
p.write_text(s)

# Result UI: show template, application and application size as separate concepts.
p = root / "app/src/main/java/ru/printcheck/android/ResultView.java"
s = p.read_text()
s = s.replace(
'''                String article = pos.optString("article");
                String method = pos.optString("method");
                LinearLayout card = card(a);
                card.addView(title(a, product));
                card.addView(text(a, "Арт. " + article + (method.isEmpty() ? "" : " · " + method), 12));

                ArrayList<JSONObject> cc = new ArrayList<>();''',
'''                String article = pos.optString("article");
                String method = pos.optString("method");
                LinearLayout card = card(a);
                card.addView(title(a, product));
                card.addView(text(a, "Арт. " + article, 12));

                ArrayList<JSONObject> cc = new ArrayList<>();''')
old = '''                if (cc.isEmpty()) {
                    TextView t = text(a, "Для этой позиции PrintCheck не выполнил визуальное сравнение.", 13);
                    t.setPadding(0, dp(a, 8), 0, dp(a, 8));
                    card.addView(t);
                } else {
                    String source = cc.get(0).optString("layout_name", cc.get(0).optString("layout_file"));
                    card.addView(text(a, "Макет: " + source, 13));
                    for (JSONObject c : cc) addComparison(a, card, runDir, fileByName, c);
                }'''
new = '''                if (cc.isEmpty()) {
                    String methodLabel = pos.optString("method_label", method);
                    if (!methodLabel.isEmpty()) card.addView(text(a, "Нанесение: " + methodLabel, 13));
                    TextView t = text(a, "Для этой позиции PrintCheck не выполнил визуальное сравнение.", 13);
                    t.setPadding(0, dp(a, 8), 0, dp(a, 8));
                    card.addView(t);
                } else {
                    String source = cc.get(0).optString("layout_name", cc.get(0).optString("layout_file"));
                    card.addView(text(a, "Макет: " + source, 13));

                    String templateName = templateNameForItem(itemId, files);
                    if (!templateName.isEmpty()) card.addView(text(a, "Шаблон: " + templateName, 13));

                    JSONObject application = applicationForComparisons(cc);
                    if (application != null) {
                        String code = application.optString("application_code", "");
                        String appName = application.optString("application_name", "");
                        String appSize = application.optString("application_size", "");
                        String app = (!code.isEmpty() ? "[" + code + "] " : "") + appName;
                        if (app.trim().isEmpty()) app = application.optString("application_label", pos.optString("method_label", method));
                        if (!app.trim().isEmpty()) card.addView(text(a, "Нанесение: " + app.trim(), 13));
                        if (!appSize.isEmpty()) card.addView(text(a, "Размер нанесения: " + appSize, 12));
                    } else {
                        String methodLabel = pos.optString("method_label", method);
                        if (!methodLabel.isEmpty()) card.addView(text(a, "Нанесение: " + methodLabel, 13));
                    }

                    for (JSONObject c : cc) addComparison(a, card, runDir, fileByName, c);
                }'''
if old not in s:
    raise SystemExit("ResultView card block not found")
s = s.replace(old, new)
s = s.replace(
    'String typeText = "application".equals(type) ? "ШАБЛОН НАНЕСЕНИЯ" : "КОНСТРУКТОР";',
    'String typeText = "application".equals(type) ? "СРАВНЕНИЕ С ЭТАЛОНОМ НАНЕСЕНИЯ" : "СРАВНЕНИЕ С ШАБЛОНОМ";'
)
s = s.replace(
'''        String refName = c.optString("reference_name", c.optString("reference_file"));
        card.addView(text(a, refName, 13));''',
'''        String refName;
        if ("application".equals(type)) {
            String code = c.optString("application_code", "");
            String appName = c.optString("application_name", "");
            refName = "Эталон нанесения" + ((!code.isEmpty() || !appName.isEmpty()) ? ": " + (!code.isEmpty() ? "[" + code + "] " : "") + appName : "");
        } else {
            String template = c.optString("template_name", "");
            refName = template.isEmpty() ? c.optString("reference_name", c.optString("reference_file")) : template;
        }
        card.addView(text(a, refName, 13));'''
)
helper = '''    private static String templateNameForItem(String itemId, JSONArray files) {
        if (files == null || itemId == null || itemId.isEmpty()) return "";
        for (int i = 0; i < files.length(); i++) {
            JSONObject f = files.optJSONObject(i);
            if (f == null || !"constructor".equals(f.optString("role"))) continue;
            JSONArray ids = f.optJSONArray("item_ids");
            if (ids == null) continue;
            for (int j = 0; j < ids.length(); j++) {
                if (itemId.equals(ids.optString(j))) {
                    String t = f.optString("template_name", "");
                    if (!t.isEmpty()) return t;
                    return f.optString("display_name", "");
                }
            }
        }
        return "";
    }

    private static JSONObject applicationForComparisons(List<JSONObject> cc) {
        if (cc == null) return null;
        for (JSONObject c : cc) if (c != null && "application".equals(c.optString("reference_type"))) return c;
        return null;
    }

'''
marker = '    private static void addComparison(Activity a, LinearLayout card, File runDir, Map<String, JSONObject> fileByName, JSONObject c) {'
if "templateNameForItem" not in s:
    s = s.replace(marker, helper + marker)
p.write_text(s)

# Version must change everywhere visible.
p = root / "app/build.gradle"
s = p.read_text().replace("versionCode 320001", "versionCode 320002").replace("versionName '3.2.0-alpha1'", "versionName '3.2.0-alpha2'")
p.write_text(s)
for name in ("README_RU.md", "PROGRESS.md"):
    p = root / name
    if p.exists():
        p.write_text(p.read_text().replace("3.2.0-alpha1", "3.2.0-alpha2"))

print("3.2.0-alpha2 separation patch applied")
