#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')

b=r('app/build.gradle')
q=r('app/src/main/java/ru/printcheck/android/QuickCheckActivity.java')
s=r('app/src/main/java/ru/printcheck/android/SvgEditorSupport.java')
p=r('app/src/main/java/ru/printcheck/android/SvgPdfExporter.java')
qe=r('app/src/main/java/ru/printcheck/android/QuickCheckEngine.java')

checks={
 'version code':'versionCode 340046' in b,
 'version name':"versionName '3.4.0-alpha46'" in b,
 'persistent signer':'alphaPersistent' in b,
 'template upload':'Загрузить шаблон' in q and 'PICK_TEMPLATE=301' in q,
 'artwork upload':'Загрузить нанесение' in q and 'PICK_ARTWORK=302' in q,
 'Gifts removed from QuickCheckActivity':'gifts.ru' not in q,
 'SVG editor button':'Редактировать SVG' in q,
 'save ready layout':'Сохранить макет' in q and 'ready_layout.svg' in q,
 'check ready layout':'Проверить готовый макет' in q,
 'JS bridge':'addJavascriptInterface' in q and 'class EditorBridge' in q,
 'template PDF support':'application/pdf' in q and 'pdfTemplate' in s,
 'template SVG support':'image/svg+xml' in q and 'svgTemplate' in s,
 'art SVG support':'SVG/PNG/JPG' in q and 'loadArtwork' in s,
 'PDF artwork refusal':'PDF нанесения не растрируется автоматически' in s,
 'physical SVG size':'width=\\"' in s and 'mm\\" height=\\"' in s,
 'field dimensions mm':'field_width_mm' in s and 'field_height_mm' in s,
 'art dimensions mm':'art_width_mm' in s and 'art_height_mm' in s,
 'position relative field':'art_x_in_field_mm' in s and 'art_y_in_field_mm' in s,
 'drag artwork':"mode='moveArt'" in s,
 'resize artwork':"mode='resizeArt'" in s,
 'fit artwork':'fitArt()' in s,
 'center artwork':'centerArt()' in s,
 'manual field edit':"mode='moveField'" in s and "mode='resizeField'" in s,
 'multiple fields':'FIELD_CANDIDATES' in s and 'prevField()' in s and 'nextField()' in s,
 'PDF colored field detection':'MIN_COLOR_HIGHLIGHT_SCORE' in s,
 'SVG highlighted rect detection':'findHighlightedRects' in s,
 'editor template export':'exportBoth' in s,
 'clean template and layout':'clean(false)' in s and 'clean(true)' in s,
 'WebView PDF export':'PdfDocument' in p and 'web.draw(canvas)' in p,
 'physical PDF page size':'wMm / 25.4 * 72.0' in p and 'hMm / 25.4 * 72.0' in p and 'PageInfo.Builder' in p,
 'exact-page rendering':'width:100vw!important' in p and 'height:100vh!important' in p,
 'QuickCheck normalized pair':'preparePdfCheck' in q and 'selected_application.pdf' in q and 'layout.pdf' in q,
 'engine uses template wording':'выбранное поле шаблона' in qe,
 'old Gifts wording gone':'Gifts' not in qe,
 'colour model browser caveat':'Цветовая модель исходника требует проверки' in q,
 'save to Downloads':'MediaStore.Downloads' in q and 'Downloads/PrintCheck' in q,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
