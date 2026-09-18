from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / "app/src/main/java/ru/printcheck/android/MainActivity.java"
s = p.read_text(encoding="utf-8")

if "private static String preflightOverall(JSONArray a)" in s:
    raise SystemExit(0)

anchor = " private static JSONObject fontScopeJson(PdfObjectInspector.FontScope s)throws JSONException{\n"
if anchor not in s:
    raise SystemExit("fontScopeJson anchor not found")

block = r''' private static String preflightOverall(JSONArray a){boolean manual=false,warning=false;for(int i=0;i<a.length();i++){JSONObject p=a.optJSONObject(i);if(p==null)continue;String s=p.optString("status");if("error".equals(s))return "error";if("warning".equals(s))warning=true;else if("manual_review".equals(s))manual=true;}return warning?"warning":(manual?"manual_review":"ok");}
 private static PreflightRules.RuleSet rulesForItem(JSONObject root,String itemId){
  JSONArray pos=root.optJSONArray("positions");if(pos==null)return new PreflightRules.RuleSet();
  for(int i=0;i<pos.length();i++){JSONObject p=pos.optJSONObject(i);if(p==null||!itemId.equals(p.optString("item_id")))continue;ArrayList<String> texts=new ArrayList<>();JSONArray req=p.optJSONArray("requirements");if(req!=null)for(int j=0;j<req.length();j++){JSONObject q=req.optJSONObject(j);if(q!=null)texts.add(q.optString("text"));}if(!p.optString("place_details").isEmpty())texts.add(p.optString("place_details"));PreflightRules.RuleSet r=PreflightRules.parse(p.optString("method"),p.optString("method_name"),p.optString("place"),texts);
   LinkedHashSet<String> all=new LinkedHashSet<>(OfficialRequirements.globalRequirements());all.addAll(r.officialMandatory);JSONArray pub=p.optJSONArray("public_requirements");if(pub!=null)for(int j=0;j<pub.length();j++){String x=pub.optString(j).trim();if(!x.isEmpty())all.add("[Техтребования Gifts] "+x);}JSONArray tech=p.optJSONArray("technology_features");if(tech!=null)for(int j=0;j<tech.length();j++){String x=tech.optString(j).trim();if(!x.isEmpty())all.add("[Особенности технологии] "+x);}r.officialMandatory.clear();r.officialMandatory.addAll(all);return r;}
  return new PreflightRules.RuleSet();
 }
 private static JSONObject rulesJson(PreflightRules.RuleSet r)throws JSONException{
  JSONObject j=new JSONObject().put("method",r.methodCode).put("catalog_snapshot",r.catalogSnapshot).put("specifications_url",OfficialRequirements.SPEC_URL).put("features_url",OfficialRequirements.FEATURES_URL);
  putPositive(j,"min_positive_mm",r.effectivePositiveMm());putPositive(j,"min_negative_mm",r.effectiveNegativeMm());putPositive(j,"min_single_element_mm",r.minSingleElementMm);putPositive(j,"min_letter_height_mm",r.minLetterHeightMm);putPositive(j,"guard_mm",r.guardMm);putPositive(j,"bleed_mm",r.bleedMm);putPositive(j,"min_raster_percent",r.minRasterPercent);putPositive(j,"min_ink_percent",r.minInkPercent);putPositive(j,"max_cmyk_sum_percent",r.maxCmykSumPercent);if(r.minRasterDpi>0)j.put("min_raster_dpi",r.minRasterDpi);if(r.maxColors>0)j.put("max_colors",r.maxColors);j.put("mandatory",new JSONArray(r.officialMandatory)).put("conditional",new JSONArray(r.officialConditional));return j;
 }
 private static void putPositive(JSONObject j,String key,double v)throws JSONException{if(v>0)j.put(key,v);}
'''

p.write_text(s.replace(anchor, block + anchor, 1), encoding="utf-8")
