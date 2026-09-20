#!/usr/bin/env python3
from pathlib import Path

root=Path(__file__).resolve().parents[1]
def r(x): return (root/x).read_text(encoding='utf-8')

b=r('app/build.gradle')
u=r('app/src/main/java/ru/printcheck/android/UiMessage.java')
m=r('app/src/main/java/ru/printcheck/android/MainActivity.java')
q=r('app/src/main/java/ru/printcheck/android/QuickCheckActivity.java')
rv=r('app/src/main/java/ru/printcheck/android/ResultView.java')

checks={
 'version code':'versionCode 340044' in b,
 'version name':"versionName '3.4.0-alpha44'" in b,
 'app id':"applicationId 'ru.printcheck.android'" in b,
 'persistent signer':'alphaPersistent' in b,
 'UiMessage class':'class UiMessage' in u,
 'info tone':'static final int INFO' in u,
 'success tone':'SUCCESS=1' in u,
 'warning tone':'WARNING=2' in u,
 'error tone':'ERROR=3' in u,
 'manual tone':'MANUAL=4' in u,
 'automatic tone mapping':'toneForStatus' in u,
 'styled status apply':'applyAuto' in u,
 'styled inline':'inline(TextView' in u,
 'styled card':'card(Activity' in u,
 'styled section':'section(Activity' in u,
 'styled toast':'toast(Activity' in u,
 'styled dialog body':'dialogBody(Activity' in u,
 'paragraph formatter':'paragraphs(String' in u,
 'main styled status':'private void showStatus(String message){UiMessage.applyAuto(this,status,message);}' in m,
 'main progress styled':'Выполняется · ' in m and 'UiMessage.INFO' in m,
 'main completion styled':'Проверка завершена' in m,
 'main raw status removed':'status.setText(' not in m,
 'main dialogs formatted':'UiMessage.dialogBody' in m,
 'quick status formatted':'UiMessage.applyAuto(this,status,s)' in q,
 'quick raw status removed':'status.setText(' not in q,
 'quick action toast':'Нужно действие' in q and 'UiMessage.toast' in q,
 'quick constructor inline':'UiMessage.inline(templateInfo' in q,
 'quick layout inline':'UiMessage.inline(layoutInfo' in q,
 'check dialog status section':'UiMessage.section(a,"Статус"' in rv,
 'check dialog what section':'UiMessage.section(a,"Что проверяется"' in rv,
 'check dialog result section':'UiMessage.section(a,"Результат"' in rv,
 'check dialog evidence section':'UiMessage.section(a,"Визуальное доказательство"' in rv,
 'report failure styled':'Не удалось построить отчёт' in rv,
 'quick summary styled':'Быстрая проверка' in rv and 'UiMessage.apply' in rv,
 'batch summary styled':'renderBatch' in rv and 'UiMessage.apply' in rv,
 'warning cards styled':'Требуется проверка' in rv and 'UiMessage.card' in rv,
 'report open toast styled':'Не удалось открыть отчёт' in rv,
 'image open toast styled':'Не удалось открыть изображение' in rv and 'Toast.makeText' not in rv,
 'order summary styled':'styleSummary' in rv and 'UiMessage.apply(a,details,tone,"Заказ №"+order' in rv,
}
for k,v in checks.items():
    print(('PASS ' if v else 'FAIL ')+k)
bad=[k for k,v in checks.items() if not v]
print(f'TOTAL {len(checks)-len(bad)}/{len(checks)} PASS')
if bad:
    raise SystemExit(1)
