#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')
b=r('app/build.gradle')
rv=r('app/src/main/java/ru/printcheck/android/ResultView.java')

checks={
 'version code':'versionCode 340045' in b,
 'version name':"versionName '3.4.0-alpha45'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'single status font size':'STATUS_TEXT_SP=8' in rv,
 'fixed article badge width':'STATUS_BADGE_WIDTH_DP=116' in rv,
 'fixed article badge height':'STATUS_BADGE_HEIGHT_DP=27' in rv,
 'fixed checklist status height':'STATUS_INLINE_HEIGHT_DP=18' in rv,
 'checklist status uses fixed size':'shortStatus(st),STATUS_TEXT_SP' in rv,
 'checklist status centers vertically':'Gravity.END|Gravity.CENTER_VERTICAL' in rv,
 'checklist font padding disabled':'status.setIncludeFontPadding(false)' in rv,
 'checklist autosize removed':'status.setAutoSizeTextTypeUniformWithConfiguration' not in rv,
 'article badge uses fixed size':'text(a,label,STATUS_TEXT_SP)' in rv,
 'article badge font padding disabled':'t.setIncludeFontPadding(false)' in rv,
 'article badge fixed layout':'new LinearLayout.LayoutParams(dp(a,STATUS_BADGE_WIDTH_DP),dp(a,STATUS_BADGE_HEIGHT_DP))' in rv,
 'article badge autosize removed':'t.setAutoSizeTextTypeUniformWithConfiguration(7,9' not in rv,
 'alpha44 colour status logic retained':'label="макет не по тт"' in rv and 'label="макет ок"' in rv and 'label="РУЧНАЯ ПРОВЕРКА"' in rv,
}
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad: raise SystemExit(1)
