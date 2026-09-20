#!/usr/bin/env python3
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys

repo=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); pb=repo/'printcheck-build'
src28=repo/'.printcheck-alpha28'; src29=repo/'.printcheck-alpha29'
if not src28.exists(): subprocess.run([sys.executable,str(pb/'prepare_alpha28.py'),str(repo)],check=True)
if src29.exists(): shutil.rmtree(src29)
shutil.copytree(src28,src29)

def sub(rel,pattern,repl,count=1,flags=0):
    p=src29/rel; s=p.read_text(encoding='utf-8'); out,n=re.subn(pattern,repl,s,count=count,flags=flags)
    if n!=count: raise RuntimeError(f'alpha29 transform {rel}: expected {count}, got {n}: {pattern[:90]}')
    p.write_text(out,encoding='utf-8')

def replace(rel,old,new,count=1):
    p=src29/rel;s=p.read_text(encoding='utf-8')
    if s.count(old)!=count: raise RuntimeError(f'alpha29 replace {rel}: expected {count}, got {s.count(old)}: {old[:90]}')
    p.write_text(s.replace(old,new,count),encoding='utf-8')

replace('app/build.gradle','versionCode 340028','versionCode 340029')
replace('app/build.gradle',"versionName '3.4.0-alpha28'","versionName '3.4.0-alpha29'")

main='app/src/main/java/ru/printcheck/android/MainActivity.java'
sub(main,r'  LinearLayout brand=new LinearLayout\(this\);brand\.setOrientation\(LinearLayout\.VERTICAL\);.*?  header\.addView\(brand,new LinearLayout\.LayoutParams\(0,-2,1\)\);',r'''  LinearLayout brandLine=new LinearLayout(this);brandLine.setOrientation(LinearLayout.HORIZONTAL);brandLine.setGravity(Gravity.CENTER_VERTICAL);
  TextView title=text("PrintCheck",22);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setTextColor(text);title.setSingleLine(true);brandLine.addView(title);
  TextView version=text(BuildConfig.VERSION_NAME,9);version.setTypeface(Typeface.DEFAULT,Typeface.BOLD);version.setTextColor(muted);version.setSingleLine(true);version.setPadding(dp(6),0,0,0);brandLine.addView(version);
  TextView readOnly=text("read-only",9);readOnly.setTypeface(Typeface.DEFAULT,Typeface.BOLD);readOnly.setTextColor(muted);readOnly.setSingleLine(true);readOnly.setPadding(dp(6),0,0,0);brandLine.addView(readOnly);
  header.addView(brandLine,new LinearLayout.LayoutParams(0,-2,1));''',flags=re.S)

rv='app/src/main/java/ru/printcheck/android/ResultView.java'
replace(rv,'treeNode(a,"Заказ №"+result.optString("order"),meta,0,statusBadge(a,result.optString("status")),expanded)','treeNode(a,"Заказ №"+result.optString("order"),meta,0,null,expanded)')
replace(rv,'treeNode(a,"Заказ №"+orderNo,"Ошибка обработки",0,statusBadge(a,"error"),false)','treeNode(a,"Заказ №"+orderNo,"Ошибка обработки",0,null,false)')

sub(rv,r'        String brief=methodText\.trim\(\);.*?addBriefChecks\(a,briefNode\.body,checks\);',r'''        String brief=methodText.trim();if(!place.isEmpty())brief+=(brief.isEmpty()?"":" · ")+place;String ab=alignmentBrief(pf);if(!ab.isEmpty())brief+=(brief.isEmpty()?"":" · ")+ab;String sb=smallBrief(pf);if(!sb.isEmpty())brief+=(brief.isEmpty()?"":" · ")+sb;if(!brief.isEmpty()){TextView summary=note(a,brief);summary.setPadding(dp(a,7),dp(a,5),dp(a,7),dp(a,5));briefNode.body.addView(summary);}
        LinearLayout artworkSlot=new LinearLayout(a);artworkSlot.setOrientation(LinearLayout.VERTICAL);briefNode.body.addView(artworkSlot,spaced(a,2));
        addBriefChecks(a,briefNode.body,checks);''',flags=re.S)
replace(rv,'briefNode.body.addView(reportAction(a,rf,"PDF-отчёт артикула"),spaced(a,3))','briefNode.body.addView(reportAction(a,rf,"PDF-отчёт артикула"),spaced(a,2))')
replace(rv,'TreeToggle detailedNode=treeNode(a,"Подробный чеклист","Изображения · измерения · требования · файлы",2,null,false);','TreeToggle detailedNode=treeNode(a,"Подробный чеклист","Измерения · требования · остальные изображения · файлы",2,null,false);')
replace(rv,'bindTree(detailedNode,false,loadDetails);articleNode.body.addView(detailedNode.root,spaced(a,3));\n        return articleNode.root;',
'''bindTree(detailedNode,false,loadDetails);articleNode.body.addView(detailedNode.root,spaced(a,3));
        Runnable loadArticle=()->populateBriefArtwork(a,artworkSlot,runDir,pf);
        bindTree(articleNode,false,loadArticle);
        return articleNode.root;''')

sub(rv,r'    private static void addBriefChecks\(Activity a,LinearLayout card,JSONArray checks\)\{.*?\n    \}\n    private static String shortStatus',r'''    private static void addBriefChecks(Activity a,LinearLayout card,JSONArray checks){
        if(checks==null||checks.length()==0){card.addView(note(a,"Чеклист отсутствует."));return;}
        LinearLayout grid=new LinearLayout(a);grid.setOrientation(LinearLayout.VERTICAL);
        for(int i=0;i<checks.length();i+=2){
            LinearLayout row=new LinearLayout(a);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.TOP);
            JSONObject left=checks.optJSONObject(i),right=i+1<checks.length()?checks.optJSONObject(i+1):null;
            if(left!=null)row.addView(briefCheckCell(a,left),briefCellParams(a,true));else row.addView(new Space(a),briefCellParams(a,true));
            if(right!=null)row.addView(briefCheckCell(a,right),briefCellParams(a,false));else row.addView(new Space(a),briefCellParams(a,false));
            grid.addView(row,new LinearLayout.LayoutParams(-1,-2));
        }
        card.addView(grid);
    }
    private static LinearLayout.LayoutParams briefCellParams(Activity a,boolean left){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);p.setMargins(left?0:dp(a,2),dp(a,2),left?dp(a,2):0,dp(a,2));return p;}
    private static LinearLayout briefCheckCell(Activity a,JSONObject c){
        String st=c.optString("status"),mark="i";int col=BLUE,bg=Color.rgb(247,249,252),border=BORDER;
        if("ok".equals(st)){mark="✓";col=GREEN;bg=Color.rgb(241,249,245);border=Color.rgb(205,229,216);}
        else if("error".equals(st)||"warning".equals(st)){mark="!";col=RED;bg=Color.rgb(255,244,242);border=Color.rgb(239,207,202);}
        else if("manual".equals(st)||"manual_review".equals(st)){mark="?";col=ORANGE;bg=Color.rgb(255,249,238);border=Color.rgb(238,218,179);}
        LinearLayout cell=new LinearLayout(a);cell.setOrientation(LinearLayout.VERTICAL);cell.setPadding(dp(a,6),dp(a,4),dp(a,6),dp(a,4));cell.setBackground(rounded(bg,border,7,a));
        LinearLayout top=new LinearLayout(a);top.setOrientation(LinearLayout.HORIZONTAL);top.setGravity(Gravity.TOP);
        TextView m=text(a,mark,11);m.setTypeface(Typeface.DEFAULT_BOLD);m.setTextColor(col);m.setGravity(Gravity.CENTER);top.addView(m,new LinearLayout.LayoutParams(dp(a,18),-2));
        TextView title=text(a,c.optString("title"),10);title.setTextColor(TEXT);title.setMaxLines(2);top.addView(title,new LinearLayout.LayoutParams(0,-2,1));cell.addView(top);
        TextView status=text(a,shortStatus(st),8);status.setTypeface(Typeface.DEFAULT_BOLD);status.setTextColor(col);status.setGravity(Gravity.END);status.setPadding(0,dp(a,1),0,0);cell.addView(status,new LinearLayout.LayoutParams(-1,-2));
        return cell;
    }
    private static String shortStatus''',flags=re.S)

p=src29/rv;s=p.read_text(encoding='utf-8');anchor='    private static void populateDetailedChecklist('
if s.count(anchor)!=1: raise RuntimeError('alpha29 detailed anchor mismatch')
helper='''    private static void populateBriefArtwork(Activity a,LinearLayout slot,File runDir,JSONObject pf){\n        if(slot==null||slot.getChildCount()>0)return;File f=briefArtworkFile(runDir,pf);if(f==null)return;\n        TextView title=text(a,"Найденное нанесение",10);title.setTypeface(Typeface.DEFAULT_BOLD);title.setTextColor(TEXT);title.setPadding(0,dp(a,3),0,dp(a,3));slot.addView(title);\n        ImageView image=largeEvidence(a,f,240);image.setContentDescription("Найденное нанесение. Нажмите, чтобы открыть на весь экран.");slot.addView(image,new LinearLayout.LayoutParams(-1,dp(a,240)));\n    }\n    private static File briefArtworkFile(File runDir,JSONObject pf){\n        if(runDir==null||pf==null)return null;JSONObject geo=pf.optJSONObject("geometry");if(geo==null)return null;String name=geo.optString("artwork_file");if(name.isEmpty())return null;File f=new File(new File(runDir,"preflight"),name);return f.isFile()?f:null;\n    }\n\n'''
p.write_text(s.replace(anchor,helper+anchor,1),encoding='utf-8')

sub(rv,r'JSONObject geo=pf==null\?null:pf\.optJSONObject\("geometry"\);section\(body,a,"Визуальная проверка"\);boolean hasVisual=false;\n            if\(geo!=null\)\{String artworkFile=.*?String focus=geo\.optString\("focus_file"\);',
'''JSONObject geo=pf==null?null:pf.optJSONObject("geometry");section(body,a,"Визуальная проверка");boolean hasVisual=briefArtworkFile(runDir,pf)!=null;
            if(geo!=null){String focus=geo.optString("focus_file");''',flags=re.S)

shutil.copy2(pb/'audit_alpha29.py',src29/'tests/audit_alpha29.py')
for rel in ['README_RU.md','PROGRESS.md']:
    p=src29/rel;s=p.read_text(encoding='utf-8').replace('3.4.0-alpha28','3.4.0-alpha29').replace('versionCode 340028, versionName 3.4.0-alpha29.','versionCode 340029, versionName 3.4.0-alpha29.')
    p.write_text(s,encoding='utf-8')
with (src29/'README_RU.md').open('a',encoding='utf-8') as f:f.write('\n\n## alpha29 — компактное дерево результатов\n- Заголовок: PrintCheck · версия · read-only в одной строке.\n- На уровне заказа больше нет статуса отдельного нанесения/артикула.\n- «Найденное нанесение» перенесено в краткий чеклист и загружается при первом раскрытии артикула.\n- Краткий чеклист — плотная двухколоночная сетка.\n- Дубликат «Найденного нанесения» удалён из подробного чеклиста.\n')
with (src29/'PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\n\n## alpha29\n- Header: PrintCheck + version + read-only on one line.\n- No order-level position badge.\n- Dense two-column brief checklist.\n- Found-artwork evidence moved to brief checklist and lazy-loaded on article expansion.\n')

b=(src29/'app/build.gradle').read_text();m=(src29/main).read_text();r=(src29/rv).read_text();detail=r[r.index('private static void populateDetailedChecklist'):r.index('private static String pd(')]
checks={
'version':'versionCode 340029' in b and "versionName '3.4.0-alpha29'" in b,
'app':"applicationId 'ru.printcheck.android'" in b,
'signer':'alphaPersistent' in b and 'printcheck-alpha-test.p12' in b,
'header':'TextView readOnly=text("read-only",9)' in m and 'безопасная проверка read-only' not in m,
'order badge removed':'treeNode(a,"Заказ №"+result.optString("order"),meta,0,null,expanded)' in r,
'two column':'for(int i=0;i<checks.length();i+=2)' in r and 'briefCheckCell' in r,
'brief artwork':'populateBriefArtwork' in r and 'largeEvidence(a,f,240)' in r and 'bindTree(articleNode,false,loadArticle)' in r,
'no detail duplicate':'visualTitle(a,"Найденное нанесение"' not in detail,
'alpha27 retained':'rule_diameter_circles_v7_no_center_dot_reference_ruler' in (src29/'app/src/main/java/ru/printcheck/android/GeometryAnalyzer.java').read_text(),
}
bad=[k for k,v in checks.items() if not v]
if bad: raise RuntimeError('alpha29 invariant failure: '+', '.join(bad))
signing=src29/'signing/printcheck-alpha-test.p12'; expected='153e3e22548b7c089caff4cf012aa7f0e41b9091b344fb9f6496377feecebb10'
if not signing.is_file():
    if os.environ.get('PRINTCHECK_SKIP_SIGNING_CHECK')!='1': raise RuntimeError('alpha29 signing key missing')
elif hashlib.sha256(signing.read_bytes()).hexdigest()!=expected: raise RuntimeError('alpha29 signing identity changed unexpectedly')
print('Prepared canonical PrintCheck 3.4.0-alpha29 source')
print('source:',src29)
print('signing_sha256:',expected)
