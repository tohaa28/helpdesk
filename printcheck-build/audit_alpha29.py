from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(rel): return (root/rel).read_text(encoding='utf-8')
main=read('app/src/main/java/ru/printcheck/android/MainActivity.java')
rv=read('app/src/main/java/ru/printcheck/android/ResultView.java')
b=read('app/build.gradle')
article=rv[rv.index('private static LinearLayout buildArticleTree'):rv.index('private static void populateDetailedChecklist')]
detail=rv[rv.index('private static void populateDetailedChecklist'):rv.index('private static String pd(')]
order=rv[rv.index('private static LinearLayout buildOrderTree'):rv.index('private static LinearLayout buildFailedOrderTree')]
checks={
'version code': 'versionCode 340029' in b,
'version name': "versionName '3.4.0-alpha29'" in b,
'app id': "applicationId 'ru.printcheck.android'" in b,
'persistent signer': 'alphaPersistent' in b,
'brand title one line': 'TextView title=text("PrintCheck",22)' in main and 'title.setSingleLine(true)' in main,
'version inline small': 'TextView version=text(BuildConfig.VERSION_NAME,9)' in main and 'brandLine.addView(version)' in main,
'read only inline small': 'TextView readOnly=text("read-only",9)' in main and 'brandLine.addView(readOnly)' in main,
'old safety subtitle removed': 'безопасная проверка read-only' not in main,
'brand line directly in header': 'header.addView(brandLine,new LinearLayout.LayoutParams(0,-2,1))' in main,
'queue wording retained': 'Заказы ожидающие проверку' in main,
'order has no position status badge': 'treeNode(a,"Заказ №"+result.optString("order"),meta,0,null,expanded)' in order,
'failed order no badge': 'treeNode(a,"Заказ №"+orderNo,"Ошибка обработки",0,null,false)' in rv,
'article status retained': 'statusBadge(a,pf.optString("status"))' in article,
'brief artwork slot': 'LinearLayout artworkSlot' in article,
'brief artwork lazy load': 'Runnable loadArticle=()->populateBriefArtwork' in article and 'bindTree(articleNode,false,loadArticle)' in article,
'brief artwork helper': 'private static void populateBriefArtwork' in rv and 'Найденное нанесение' in rv,
'brief artwork physical source': 'geo.optString("artwork_file")' in rv,
'brief artwork fullscreen evidence': 'largeEvidence(a,f,240)' in rv,
'brief checks two column loop': 'for(int i=0;i<checks.length();i+=2)' in rv,
'two equal cells': rv.count('briefCellParams(a,') >= 4 and 'new LinearLayout.LayoutParams(0,-2,1)' in rv,
'compact brief cell': 'briefCheckCell' in rv and 'setPadding(dp(a,6),dp(a,4),dp(a,6),dp(a,4))' in rv,
'compact brief fonts': 'c.optString("title"),10' in rv and 'shortStatus(st),8' in rv,
'brief summary compact': 'summary.setPadding(dp(a,7),dp(a,5),dp(a,7),dp(a,5))' in article,
'artwork duplicate removed from detailed': 'artwork_file' not in detail and 'visualTitle(a,"Найденное нанесение"' not in detail,
'detailed knows brief artwork exists': 'boolean hasVisual=briefArtworkFile(runDir,pf)!=null' in detail,
'detailed remains lazy': 'Runnable loadDetails' in article and 'bindTree(detailedNode,false,loadDetails)' in article,
'alpha27 marker behavior retained': 'rule_diameter_circles_v7_no_center_dot_reference_ruler' in read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'),
'intersection safe retained': 'per-color-medial-gap-v2-intersection-safe' in read('app/src/main/java/ru/printcheck/android/SmallElementAnalyzer.java'),
'performance retained': 'ARTWORK_TARGET_DPI = 720' in read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java') and 'MAX_ARTWORK_PIXELS = 4_000_000L' in read('app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java'),
'no synthetic mapper': not (root/'app/src/main/java/ru/printcheck/android/ApplicationFieldMapper.java').exists(),
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
if bad: raise SystemExit('FAILED: '+', '.join(bad))
print(f'TOTAL {len(checks)}/{len(checks)} passed')
