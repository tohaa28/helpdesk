package ru.printcheck.android;

import android.app.*;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import org.json.*;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
    private static final String VERSION = "3.4.0-alpha6";
    private static final String SITE = "https://gifts.ru/";

    private EditText orderInput;
    private Button loginButton, checkButton, diagnosticsButton, closeWebButton;
    private TextView status, logView, filesView, mappingView, resultsView, techView;
    private ProgressBar overall, stage;
    private ImageView preview;
    private WebView web;
    private final ExecutorService pool = Executors.newFixedThreadPool(2);
    private volatile boolean waitingOrder = false;
    private File runDir, diagFile;
    private final Object logLock = new Object();

    @Override public void onCreate(Bundle b){super.onCreate(b);buildUi();configureWeb();}
    @Override protected void onDestroy(){super.onDestroy();pool.shutdownNow();}

    private void buildUi(){
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(16),dp(12),dp(16),dp(12));
        TextView title=t("PrintCheck Android "+VERSION,22,true);root.addView(title);
        TextView sub=t("Авторизация через gifts.ru · сопоставление 1:1 · техпроверка только фактического нанесения",13,false);root.addView(sub);

        orderInput=new EditText(this);orderInput.setHint("Номер заказа");orderInput.setInputType(2);orderInput.setSingleLine(true);root.addView(orderInput,new LinearLayout.LayoutParams(-1,dp(52)));

        LinearLayout buttons=new LinearLayout(this);buttons.setOrientation(LinearLayout.HORIZONTAL);buttons.setPadding(0,dp(6),0,dp(6));
        loginButton=button("Войти");checkButton=button("Проверить");diagnosticsButton=button("Диагностика");
        buttons.addView(loginButton,weighted());buttons.addView(checkButton,weighted());buttons.addView(diagnosticsButton,weighted());root.addView(buttons);

        closeWebButton=button("Закрыть сайт");closeWebButton.setVisibility(View.GONE);root.addView(closeWebButton,new LinearLayout.LayoutParams(-1,dp(48)));
        web=new WebView(this);web.setVisibility(View.GONE);root.addView(web,new LinearLayout.LayoutParams(-1,0));

        status=t("Готово",15,true);root.addView(status);
        overall=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);overall.setMax(100);root.addView(overall,new LinearLayout.LayoutParams(-1,dp(14)));
        stage=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);stage.setMax(100);root.addView(stage,new LinearLayout.LayoutParams(-1,dp(9)));

        ScrollView sc=new ScrollView(this);LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);
        body.addView(section("Скачанные PDF"));filesView=t("—",12,false);body.addView(filesView);
        body.addView(section("Шаблон → артикул"));mappingView=t("—",12,false);body.addView(mappingView);
        body.addView(section("Сопоставления"));resultsView=t("—",12,false);body.addView(resultsView);
        body.addView(section("Техническая проверка"));techView=t("—",12,false);techView.setTextIsSelectable(true);body.addView(techView);
        preview=new ImageView(this);preview.setAdjustViewBounds(true);preview.setScaleType(ImageView.ScaleType.FIT_CENTER);body.addView(preview,new LinearLayout.LayoutParams(-1,dp(320)));
        body.addView(section("Диагностика"));logView=t("—",11,false);logView.setTextIsSelectable(true);body.addView(logView);
        sc.addView(body);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);

        loginButton.setOnClickListener(v->openLogin());
        closeWebButton.setOnClickListener(v->hideWeb());
        checkButton.setOnClickListener(v->startOrder());
        diagnosticsButton.setOnClickListener(v->showDiagnosticsDialog());
    }

    private LinearLayout.LayoutParams weighted(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(52),1);p.setMargins(dp(3),0,dp(3),0);return p;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setMinHeight(dp(48));return b;}
    private TextView section(String s){TextView v=t(s,16,true);v.setPadding(0,dp(14),0,dp(3));return v;}
    private TextView t(String s,int sp,boolean bold){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(Color.rgb(31,44,66));v.setPadding(0,dp(4),0,dp(4));if(bold)v.setTypeface(null,1);return v;}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}

    private void configureWeb(){
        WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setUserAgentString(s.getUserAgentString()+" PrintCheckAndroid/"+VERSION);
        android.webkit.CookieManager.getInstance().setAcceptCookie(true);android.webkit.CookieManager.getInstance().setAcceptThirdPartyCookies(web,true);
        web.addJavascriptInterface(new Bridge(),"PrintCheckBridge");
        web.setWebViewClient(new WebViewClient(){
            @Override public void onPageFinished(WebView v,String url){
                super.onPageFinished(v,url);append("web.page "+url);
                if(waitingOrder){
                    if(url.matches("https://gifts\\.ru/private/order/\\d+.*")){
                        waitingOrder=false;hideWeb();injectCollector();
                    }else if(url.startsWith("https://gifts.ru/") && !url.equals("about:blank")){
                        waitingOrder=false;showWeb(dp(420));status("Нужен вход на gifts.ru. После входа нажмите «Проверить» ещё раз.",2,0);
                    }
                }
            }
        });
    }

    private void openLogin(){waitingOrder=false;showWeb(dp(430));web.loadUrl(SITE);status("Войдите на gifts.ru через сайт",0,0);}
    private void showWeb(int h){web.setVisibility(View.VISIBLE);LinearLayout.LayoutParams p=(LinearLayout.LayoutParams)web.getLayoutParams();p.height=h;p.weight=0;web.setLayoutParams(p);closeWebButton.setVisibility(View.VISIBLE);}
    private void hideWeb(){web.setVisibility(View.GONE);LinearLayout.LayoutParams p=(LinearLayout.LayoutParams)web.getLayoutParams();p.height=0;p.weight=0;web.setLayoutParams(p);closeWebButton.setVisibility(View.GONE);}

    private void startOrder(){
        String n=orderInput.getText().toString().trim();if(!n.matches("\\d+")){toast("Введите номер заказа");return;}
        resetRun(n);status("Открываю заказ в сохранённой сессии",3,10);waitingOrder=true;hideWeb();web.loadUrl("https://gifts.ru/private/order/"+n);
    }

    private void resetRun(String n){
        runDir=new File(getExternalFilesDir(null),"orders/"+n+"/run_"+System.currentTimeMillis());runDir.mkdirs();diagFile=new File(runDir,"matching_trace.jsonl");
        filesView.setText("—");mappingView.setText("—");resultsView.setText("—");techView.setText("—");preview.setImageDrawable(null);logView.setText("");overall.setProgress(0);stage.setProgress(0);append("run.start version="+VERSION+" order="+n);
    }

    private void injectCollector(){
        try{String js=readAsset("collector_android.js")+"\ncollectAndroidOrder().then(r=>PrintCheckBridge.onCollected(JSON.stringify(r))).catch(e=>PrintCheckBridge.onError(String(e&&e.stack||e)));";status("Читаю «Макеты для заказа»",8,25);web.evaluateJavascript(js,null);}catch(Exception e){fail(e);}
    }
    private String readAsset(String n)throws Exception{try(InputStream in=getAssets().open(n)){ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] x=new byte[8192];for(int r;(r=in.read(x))>0;)b.write(x,0,r);return b.toString("UTF-8");}}

    private final class Bridge {
        @JavascriptInterface public void onCollected(String json){runOnUiThread(()->{append("collector.done bytes="+json.length());status("Скачиваю PDF",16,5);});pool.submit(()->processCollected(json));}
        @JavascriptInterface public void onError(String error){runOnUiThread(()->{append("collector.error "+error);status.setText("Ошибка чтения заказа");});}
    }

    private void processCollected(String json){
        try{
            JSONObject root=new JSONObject(json);String order=root.optString("orderNumber",orderInput.getText().toString());
            ArrayList<Models.RemotePdf> layouts=parse(root.getJSONArray("layouts"),false),constructors=parse(root.getJSONArray("constructors"),true);
            long missing=constructors.stream().filter(x->x.article==null||x.article.isEmpty()).count();
            if(missing>0)throw new Exception("У "+missing+" PDF-конструкторов не прочитан артикул из вкладки «Шаблоны макетов»");
            writeText(new File(runDir,"collector.json"),json);
            downloadAll(layouts,constructors);runOnUiThread(()->renderFiles(layouts,constructors));

            statusBg("Индексирую PDF",34,0);ArrayList<Models.PdfIndex> li=new ArrayList<>(),ci=new ArrayList<>();int total=layouts.size()+constructors.size(),done=0;
            for(Models.RemotePdf p:layouts){li.add(RasterPdfIndexer.index(p,s->statusBg(s,34,0)));done++;stageBg(done*100/Math.max(1,total));}
            for(Models.RemotePdf p:constructors){ci.add(RasterPdfIndexer.index(p,s->statusBg(s,42,0)));done++;stageBg(done*100/Math.max(1,total));}

            statusBg("Сопоставляю макеты с конструкторами",50,0);ArrayList<Models.Occurrence> found=new ArrayList<>();int comparisons=0,totalCmp=Math.max(1,li.size()*ci.size());
            for(Models.PdfIndex l:li)for(Models.PdfIndex c:ci){
                Models.CompareStats st=new Models.CompareStats();List<Models.Occurrence> occ=RasterMatcher.compare(l,c,st);comparisons++;
                JSONObject tr=new JSONObject().put("event","compare").put("layout",l.pdf.label).put("constructor",c.pdf.label).put("article",c.pdf.article).put("comparison",comparisons).put("total",totalCmp).put("layoutPages",l.pages.size()).put("constructorPages",c.pages.size()).put("sizeCandidates",st.sizeCandidates).put("signatureCandidates",st.signatureCandidates).put("voteClusters",st.voteClusters).put("confirmed",occ.size()).put("bestCoverage",st.bestCoverage).put("bestScore",st.bestScore);trace(tr.toString());
                for(Models.Occurrence o:occ){o.id=String.format(Locale.US,"%s:p%d:%s:%d:%d",safe(l.pdf.label),o.layoutPage+1,o.article,o.dx,o.dy);found.add(o);}
                int pct=comparisons*100/totalCmp;stageBg(pct);statusBg("Сравнение "+comparisons+" / "+totalCmp,50+(pct*20/100),pct);
            }
            found=resolveConflicts(found);

            statusBg("Техническая проверка нанесений",72,0);ArrayList<Models.TechnicalReport> technical=new ArrayList<>();int ti=0;
            for(Models.Occurrence o:found){
                Models.PdfIndex l=findIndex(li,o.layoutFile),c=findIndex(ci,o.constructorFile);if(l==null||c==null)continue;
                try{
                    Models.TechnicalReport r=PdfTechnicalAnalyzer.analyze(l,c,o,new File(runDir,"technical"),s->statusBg(s,72,0));technical.add(r);
                    trace(technicalJson(r).put("event","technical").toString());
                }catch(Exception ex){trace(new JSONObject().put("event","technical_error").put("occurrence",o.id).put("error",String.valueOf(ex)).toString());}
                ti++;stageBg(ti*100/Math.max(1,found.size()));
            }

            writeResults(order,layouts,constructors,found,technical,comparisons);
            ArrayList<Models.Occurrence> finalFound=found;ArrayList<Models.TechnicalReport> finalTech=technical;int finalComparisons=comparisons;
            runOnUiThread(()->{renderResults(finalFound,finalComparisons,layouts.size(),constructors.size());renderTechnical(finalTech);status("Проверка завершена",100,100);hideWeb();});
        }catch(Exception e){fail(e);}
    }

    private Models.PdfIndex findIndex(List<Models.PdfIndex> xs,String label){for(Models.PdfIndex x:xs)if(Objects.equals(x.pdf.label,label))return x;return null;}
    private ArrayList<Models.RemotePdf> parse(JSONArray a,boolean constructor)throws Exception{ArrayList<Models.RemotePdf> out=new ArrayList<>();for(int i=0;i<a.length();i++){JSONObject o=a.getJSONObject(i);String url=o.getString("url");if(!url.toLowerCase(Locale.ROOT).contains(".cdr"))out.add(new Models.RemotePdf(url,o.optString("label","file.pdf"),constructor?o.optString("article",null):null));}return out;}

    private void downloadAll(List<Models.RemotePdf> layouts,List<Models.RemotePdf> constructors)throws Exception{
        ArrayList<Models.RemotePdf> all=new ArrayList<>();all.addAll(layouts);all.addAll(constructors);int i=0;
        for(Models.RemotePdf p:all){i++;download(p);stageBg(i*100/Math.max(1,all.size()));statusBg("Скачивание "+i+" / "+all.size()+" · "+p.label,16+(i*16/Math.max(1,all.size())),i*100/Math.max(1,all.size()));}
    }
    private void download(Models.RemotePdf p)throws Exception{
        String cookie=android.webkit.CookieManager.getInstance().getCookie(p.url);HttpURLConnection c=(HttpURLConnection)new URL(p.url).openConnection();c.setInstanceFollowRedirects(true);c.setConnectTimeout(20000);c.setReadTimeout(60000);c.setRequestProperty("User-Agent",web.getSettings().getUserAgentString());if(cookie!=null)c.setRequestProperty("Cookie",cookie);c.connect();
        if(c.getResponseCode()/100!=2)throw new IOException("HTTP "+c.getResponseCode()+" для "+p.label);String name=fileName(c,p);File dir=new File(runDir,p.article==null?"layouts":"constructors");dir.mkdirs();p.file=new File(dir,name);
        try(InputStream in=c.getInputStream();OutputStream out=new FileOutputStream(p.file)){byte[] b=new byte[65536];for(int n;(n=in.read(b))>0;)out.write(b,0,n);}trace(new JSONObject().put("event","download").put("file",p.file.getName()).put("bytes",p.file.length()).put("article",p.article).toString());c.disconnect();
    }
    private String fileName(HttpURLConnection c,Models.RemotePdf p){String cd=c.getHeaderField("Content-Disposition");if(cd!=null){java.util.regex.Matcher m=java.util.regex.Pattern.compile("filename\\*?=(?:UTF-8''|\\\")?([^\\\";]+)",2).matcher(cd);if(m.find())try{return URLDecoder.decode(m.group(1).trim(),"UTF-8");}catch(Exception ignored){}}String s=safe(p.label);return s.toLowerCase(Locale.ROOT).endsWith(".pdf")?s:s+".pdf";}

    private ArrayList<Models.Occurrence> resolveConflicts(List<Models.Occurrence> src){src.sort((a,b)->Double.compare(b.score,a.score));ArrayList<Models.Occurrence> out=new ArrayList<>();for(Models.Occurrence o:src){boolean conflict=false;for(Models.Occurrence k:out){if(k.layoutFile.equals(o.layoutFile)&&k.layoutPage==o.layoutPage&&overlap(k,o)>0.55){conflict=true;break;}}if(!conflict)out.add(o);}return out;}
    private double overlap(Models.Occurrence a,Models.Occurrence b){int x0=Math.max(a.x0,b.x0),y0=Math.max(a.y0,b.y0),x1=Math.min(a.x1,b.x1),y1=Math.min(a.y1,b.y1);int inter=Math.max(0,x1-x0)*Math.max(0,y1-y0);int aa=Math.max(1,(a.x1-a.x0)*(a.y1-a.y0)),bb=Math.max(1,(b.x1-b.x0)*(b.y1-b.y0));return inter/(double)Math.min(aa,bb);}

    private JSONObject technicalJson(Models.TechnicalReport r)throws Exception{
        JSONObject j=new JSONObject().put("occurrence",r.occurrenceId).put("layout",r.layoutFile).put("article",r.article).put("page",r.page).put("liveText",r.liveTextCount).put("smallPositive",r.positiveSmall).put("smallNegative",r.negativeSmall).put("gradientSuspected",r.gradientSuspected).put("softEffectSuspected",r.softEffectSuspected).put("pdfShading",r.pdfHasShading).put("pdfTransparency",r.pdfHasTransparency).put("pdfBlendMode",r.pdfHasBlendMode);
        JSONArray fs=new JSONArray();for(Models.Finding f:r.findings)fs.put(new JSONObject().put("code",f.code).put("severity",f.severity.name()).put("message",f.message));j.put("findings",fs);if(r.annotatedImage!=null)j.put("markedImage",r.annotatedImage.getAbsolutePath());return j;
    }

    private void writeResults(String order,List<Models.RemotePdf> l,List<Models.RemotePdf> c,List<Models.Occurrence> o,List<Models.TechnicalReport> technical,int cmp)throws Exception{
        JSONObject r=new JSONObject().put("version",VERSION).put("order",order).put("layoutFiles",l.size()).put("constructors",c.size()).put("comparisons",cmp);
        JSONArray a=new JSONArray();for(Models.Occurrence x:o)a.put(new JSONObject().put("id",x.id).put("layout",x.layoutFile).put("page",x.layoutPage+1).put("constructor",x.constructorFile).put("article",x.article).put("matched",x.matched).put("total",x.total).put("coverage",x.coverage).put("score",x.score).put("translationPx",new JSONArray().put(x.dx).put(x.dy)));r.put("matches",a);
        JSONArray tr=new JSONArray();for(Models.TechnicalReport x:technical)tr.put(technicalJson(x));r.put("technical",tr);writeText(new File(runDir,"result.json"),r.toString(2));
    }

    private void renderFiles(List<Models.RemotePdf> l,List<Models.RemotePdf> c){StringBuilder f=new StringBuilder();for(Models.RemotePdf p:l)f.append("✓ ").append(p.file.getName()).append(" · ").append(p.file.length()/1024).append(" KB\n");filesView.setText(f.length()==0?"—":f.toString());StringBuilder m=new StringBuilder();for(Models.RemotePdf p:c)m.append(p.article).append("  →  ").append(p.file.getName()).append("\n");mappingView.setText(m.length()==0?"—":m.toString());}
    private void renderResults(List<Models.Occurrence> o,int cmp,int lf,int cf){StringBuilder b=new StringBuilder();b.append("PDF макетов: ").append(lf).append("\nPDF конструкторов: ").append(cf).append("\nСравнений PDF×PDF: ").append(cmp).append("\nНайдено нанесений: ").append(o.size()).append("\n\n");int i=1;for(Models.Occurrence x:o)b.append(i++).append(". ").append(x.layoutFile).append(" · стр. ").append(x.layoutPage+1).append("\n   → арт. ").append(x.article).append(" · ").append(x.constructorFile).append("\n   score ").append(String.format(Locale.US,"%.1f%%",x.score*100)).append(" · coverage ").append(String.format(Locale.US,"%.1f%%",x.coverage*100)).append("\n\n");resultsView.setText(b.toString());}
    private void renderTechnical(List<Models.TechnicalReport> rs){
        if(rs.isEmpty()){techView.setText("Нет сопоставленных нанесений для технической проверки.");return;}StringBuilder b=new StringBuilder();int errors=0,warnings=0;File first=null;
        for(Models.TechnicalReport r:rs){for(Models.Finding f:r.findings){if(f.severity==Models.Severity.ERROR)errors++;if(f.severity==Models.Severity.WARNING)warnings++;}if(first==null&&r.annotatedImage!=null)first=r.annotatedImage;}
        b.append("Ошибок: ").append(errors).append(" · предупреждений: ").append(warnings).append("\n");
        for(Models.TechnicalReport r:rs){b.append("\n").append(r.layoutFile).append(" · стр. ").append(r.page).append(" · арт. ").append(r.article).append("\n");if(r.findings.isEmpty())b.append("  ✓ замечаний не найдено\n");for(Models.Finding f:r.findings)b.append(f.severity==Models.Severity.ERROR?"  ✕ ":"  ! ").append(f.message).append("\n");if(r.annotatedImage!=null)b.append("  Маркеры: ").append(r.annotatedImage.getName()).append("\n");}
        techView.setText(b.toString());if(first!=null){Bitmap bm=BitmapFactory.decodeFile(first.getAbsolutePath());preview.setImageBitmap(bm);}
    }

    private void trace(String line){synchronized(logLock){try(FileOutputStream out=new FileOutputStream(diagFile,true)){out.write((line+"\n").getBytes(StandardCharsets.UTF_8));}catch(Exception ignored){}}append(line);}
    private void append(String s){runOnUiThread(()->{String old=logView.getText().toString();if(old.length()>18000)old=old.substring(old.length()-12000);logView.setText(old+s+"\n");});}
    private void writeText(File f,String s)throws Exception{try(OutputStream out=new FileOutputStream(f)){out.write(s.getBytes(StandardCharsets.UTF_8));}}
    private String safe(String s){return s==null?"file":s.replaceAll("[^A-Za-z0-9А-Яа-я._-]","_");}
    private void status(String s,int ov,int st){status.setText(s);overall.setProgress(ov);stage.setProgress(st);}
    private void statusBg(String s,int ov,int st){runOnUiThread(()->status(s,ov,st));}
    private void stageBg(int x){runOnUiThread(()->stage.setProgress(x));}
    private void fail(Exception e){append("ERROR "+android.util.Log.getStackTraceString(e));runOnUiThread(()->{status.setText("Ошибка: "+e.getMessage());overall.setProgress(Math.min(99,overall.getProgress()));});}
    private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_SHORT).show();}
    private void showDiagnosticsDialog(){new AlertDialog.Builder(this).setTitle("Диагностика "+VERSION).setMessage(runDir==null?"Запуск ещё не выполнялся":"Папка:\n"+runDir.getAbsolutePath()+"\n\nmatching_trace.jsonl — сопоставление и техпроверка\nresult.json — полный результат\ntechnical/*.png — отмеченные проблемные элементы").setPositiveButton("OK",null).show();}
}
