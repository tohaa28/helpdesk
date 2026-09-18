package ru.printcheck.android;

import android.graphics.*;
import android.graphics.pdf.PdfRenderer;
import android.os.ParcelFileDescriptor;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;
import java.util.zip.InflaterInputStream;

final class PdfTechnicalAnalyzer {
    static final float MIN_ELEMENT_MM = 0.12f;
    private static final float TARGET_PX_PER_MM = 18f;
    private static final int MAX_CROP_SIDE = 2600;
    private static final int CORE_DIFF = 45;
    private static final int SOFT_DIFF = 12;

    interface Progress { void onProgress(String s); }

    static Models.TechnicalReport analyze(
            Models.PdfIndex layout,
            Models.PdfIndex constructor,
            Models.Occurrence occ,
            File outputDir,
            Progress progress) throws Exception {

        Models.TechnicalReport report = new Models.TechnicalReport();
        report.occurrenceId = occ.id;
        report.layoutFile = layout.pdf.label;
        report.article = occ.article;
        report.page = occ.layoutPage + 1;

        RawFlags flags = inspectRaw(layout.pdf.file);
        report.pdfHasShading = flags.shading;
        report.pdfHasTransparency = flags.transparency;
        report.pdfHasBlendMode = flags.nonNormalBlend;

        Models.PageIndex lp = layout.page(occ.layoutPage);
        Models.PageIndex cp = constructor.page(occ.constructorPage);
        if (lp == null || cp == null) throw new IOException("Не найдена индексированная страница PDF");

        if(progress!=null) progress.onProgress("Техпроверка · " + layout.pdf.label + " · стр. " + report.page);

        RectI crop = occurrenceCrop(lp, occ);
        RectI ccrop = new RectI(crop.x0-occ.dx, crop.y0-occ.dy, crop.x1-occ.dx, crop.y1-occ.dy);
        normalizePairedCrops(crop, ccrop, lp.width, lp.height, cp.width, cp.height);

        float cropWidthMm = (crop.w() / (float)lp.width) * lp.pageWidthPt * 25.4f / 72f;
        float cropHeightMm = (crop.h() / (float)lp.height) * lp.pageHeightPt * 25.4f / 72f;
        float pxPerMm = TARGET_PX_PER_MM;
        int tw = Math.max(80, Math.round(cropWidthMm * pxPerMm));
        int th = Math.max(80, Math.round(cropHeightMm * pxPerMm));
        float cap = Math.min(1f, MAX_CROP_SIDE / (float)Math.max(tw, th));
        if(cap < 1f){ tw=Math.max(80,Math.round(tw*cap)); th=Math.max(80,Math.round(th*cap)); pxPerMm*=cap; }

        Bitmap lb = renderCrop(layout.pdf.file, occ.layoutPage, lp, crop, tw, th);
        Bitmap cb = renderCrop(constructor.pdf.file, occ.constructorPage, cp, ccrop, tw, th);
        try {
            VisualData vd = compareVisual(lb, cb, pxPerMm);
            report.positiveSmall = vd.positiveMarks.size();
            report.negativeSmall = vd.negativeMarks.size();
            report.gradientSuspected = vd.gradientSuspected;
            report.softEffectSuspected = vd.softEffectSuspected;

            List<TextMark> layoutText = extractTextMarks(layout.pdf.file, occ.layoutPage);
            List<TextMark> consText = extractTextMarks(constructor.pdf.file, occ.constructorPage);
            report.liveTextCount = countArtworkText(layoutText, consText, lp, cp, crop, ccrop, vd.coreMask, tw, th);

            if(report.liveTextCount>0){
                report.findings.add(new Models.Finding("LIVE_TEXT", Models.Severity.ERROR,
                        "В нанесении найден живой текст/шрифт: " + report.liveTextCount + " объект(а). Текст должен быть переведён в кривые.", report.page));
            }
            if(report.positiveSmall>0){
                report.findings.add(new Models.Finding("SMALL_POSITIVE", Models.Severity.ERROR,
                        "Найдены слишком тонкие позитивные элементы < " + MIN_ELEMENT_MM + " мм: " + report.positiveSmall + ".", report.page));
            }
            if(report.negativeSmall>0){
                report.findings.add(new Models.Finding("SMALL_NEGATIVE", Models.Severity.ERROR,
                        "Найдены слишком тонкие негативные элементы/выворотки < " + MIN_ELEMENT_MM + " мм: " + report.negativeSmall + ".", report.page));
            }

            if(flags.shading && vd.gradientSuspected){
                report.findings.add(new Models.Finding("GRADIENT", Models.Severity.ERROR,
                        "В области нанесения подтверждён градиент (PDF Shading + плавный цветовой переход).", report.page));
            } else if(vd.gradientSuspected){
                report.findings.add(new Models.Finding("RASTER_GRADIENT", Models.Severity.WARNING,
                        "В нанесении найден плавный тоновый переход. Возможно, градиент уже растрирован — требуется проверка.", report.page));
            }

            if((flags.transparency || flags.nonNormalBlend) && vd.softEffectSuspected){
                report.findings.add(new Models.Finding("TRANSPARENCY_EFFECT", Models.Severity.ERROR,
                        "В области нанесения обнаружены признаки прозрачности/эффекта (SMask/alpha/blend + мягкие переходы).", report.page));
            } else if(vd.softEffectSuspected){
                report.findings.add(new Models.Finding("RASTER_EFFECT", Models.Severity.WARNING,
                        "В нанесении найдены широкие мягкие края. Возможен растрированный эффект/прозрачность.", report.page));
            }

            outputDir.mkdirs();
            File out = new File(outputDir, safe(layout.pdf.label)+"_p"+report.page+"_"+safe(occ.article)+"_marked.png");
            annotate(lb, vd, out);
            report.annotatedImage = out;
        } finally {
            lb.recycle(); cb.recycle();
        }
        return report;
    }

    private static RectI occurrenceCrop(Models.PageIndex p, Models.Occurrence o){
        int bw=Math.max(1,o.x1-o.x0), bh=Math.max(1,o.y1-o.y0);
        int mx=Math.max(18,Math.round(bw*0.10f)), my=Math.max(18,Math.round(bh*0.10f));
        return new RectI(Math.max(0,o.x0-mx),Math.max(0,o.y0-my),Math.min(p.width,o.x1+mx),Math.min(p.height,o.y1+my));
    }

    private static void normalizePairedCrops(RectI a, RectI b, int aw, int ah, int bw, int bh){
        int dl=Math.max(0,-b.x0), dt=Math.max(0,-b.y0), dr=Math.max(0,b.x1-bw), db=Math.max(0,b.y1-bh);
        a.x0+=dl; b.x0+=dl; a.y0+=dt; b.y0+=dt; a.x1-=dr; b.x1-=dr; a.y1-=db; b.y1-=db;
        if(a.x0<0){int d=-a.x0;a.x0+=d;b.x0+=d;} if(a.y0<0){int d=-a.y0;a.y0+=d;b.y0+=d;}
        if(a.x1>aw){int d=a.x1-aw;a.x1-=d;b.x1-=d;} if(a.y1>ah){int d=a.y1-ah;a.y1-=d;b.y1-=d;}
        if(a.w()<10||a.h()<10||b.w()<10||b.h()<10) throw new IllegalArgumentException("Слишком мала область сопоставления");
    }

    private static Bitmap renderCrop(File file,int pageNo,Models.PageIndex idx,RectI crop,int tw,int th)throws Exception{
        try(ParcelFileDescriptor pfd=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
            PdfRenderer r=new PdfRenderer(pfd);
            PdfRenderer.Page p=r.openPage(pageNo)){
            Bitmap b=Bitmap.createBitmap(tw,th,Bitmap.Config.ARGB_8888); b.eraseColor(Color.WHITE);
            float leftPt=crop.x0*(p.getWidth()/(float)idx.width), topPt=crop.y0*(p.getHeight()/(float)idx.height);
            float widthPt=crop.w()*(p.getWidth()/(float)idx.width), heightPt=crop.h()*(p.getHeight()/(float)idx.height);
            float sx=tw/Math.max(0.01f,widthPt), sy=th/Math.max(0.01f,heightPt);
            Matrix m=new Matrix();
            m.setValues(new float[]{sx,0,-leftPt*sx, 0,sy,-topPt*sy, 0,0,1});
            p.render(b,null,m,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
            return b;
        }
    }

    private static VisualData compareVisual(Bitmap l,Bitmap c,float pxPerMm){
        int w=l.getWidth(),h=l.getHeight(),n=w*h;
        int[] a=new int[n],b=new int[n]; l.getPixels(a,0,w,0,0,w,h); c.getPixels(b,0,w,0,0,w,h);
        boolean[] core=new boolean[n], soft=new boolean[n];
        int coreCount=0; HashSet<Integer> bins=new HashSet<>();
        long smoothPairs=0,strongPairs=0;
        for(int i=0;i<n;i++){
            int d=colorDiff(a[i],b[i]);
            if(d>=CORE_DIFF){
                core[i]=true;coreCount++;
                int rr=Color.red(a[i])>>3,gg=Color.green(a[i])>>3,bb=Color.blue(a[i])>>3;
                if(bins.size()<512)bins.add((rr<<10)|(gg<<5)|bb);
            }else if(d>=SOFT_DIFF){soft[i]=true;}
        }
        for(int y=0;y<h;y++)for(int x=0;x<w;x++){
            int i=y*w+x;if(!core[i])continue;
            if(x+1<w&&core[i+1]){int d=colorDiff(a[i],a[i+1]);if(d>=1&&d<=16)smoothPairs++;else if(d>28)strongPairs++;}
            if(y+1<h&&core[i+w]){int d=colorDiff(a[i],a[i+w]);if(d>=1&&d<=16)smoothPairs++;else if(d>28)strongPairs++;}
        }
        VisualData vd=new VisualData(); vd.coreMask=core; vd.softMask=soft; vd.w=w;vd.h=h;vd.pxPerMm=pxPerMm;
        vd.positiveMarks=findThinComponents(core,w,h,pxPerMm,false);
        vd.negativeMarks=findNegativeThin(core,w,h,pxPerMm);
        long transitions=smoothPairs+strongPairs;
        vd.gradientSuspected=coreCount>300 && bins.size()>=24 && smoothPairs>250 && (transitions==0?0:(smoothPairs/(double)transitions))>0.60;
        int nearSoft=0;
        for(int y=1;y<h-1;y++)for(int x=1;x<w-1;x++){int i=y*w+x;if(!soft[i])continue;if(core[i-1]||core[i+1]||core[i-w]||core[i+w])nearSoft++;}
        vd.softEffectSuspected=coreCount>100 && nearSoft>120 && nearSoft/(double)Math.max(1,coreCount)>0.22;
        return vd;
    }

    private static List<Mark> findThinComponents(boolean[] mask,int w,int h,float pxPerMm,boolean negative){
        boolean[] seen=new boolean[mask.length];ArrayList<Mark> out=new ArrayList<>();
        float limitPx=MIN_ELEMENT_MM*pxPerMm;
        for(int sy=0;sy<h;sy++)for(int sx=0;sx<w;sx++){
            int s=sy*w+sx;if(!mask[s]||seen[s])continue;
            ArrayDeque<Integer> q=new ArrayDeque<>();ArrayList<Integer> pts=new ArrayList<>();q.add(s);seen[s]=true;
            int minx=sx,maxx=sx,miny=sy,maxy=sy;
            while(!q.isEmpty()){
                int v=q.removeFirst();pts.add(v);int y=v/w,x=v-y*w;minx=Math.min(minx,x);maxx=Math.max(maxx,x);miny=Math.min(miny,y);maxy=Math.max(maxy,y);
                if(x>0)add(mask,seen,q,v-1);if(x+1<w)add(mask,seen,q,v+1);if(y>0)add(mask,seen,q,v-w);if(y+1<h)add(mask,seen,q,v+w);
            }
            if(pts.size()<4)continue;
            int bw=maxx-minx+1,bh=maxy-miny+1;
            if(bw>0.85*w&&bh>0.85*h)continue;
            float thick=estimateMaxThickness(mask,w,h,minx,miny,maxx,maxy,Math.max(2,(int)Math.ceil(limitPx*2)));
            if(thick<=limitPx+0.35f){
                Mark m=new Mark();m.x=(minx+maxx)/2;m.y=(miny+maxy)/2;m.radius=Math.max(24,Math.max(bw,bh)/2+14);m.negative=negative;m.sizeMm=thick/pxPerMm;out.add(m);
                if(out.size()>=80)return out;
            }
        }
        return out;
    }

    private static List<Mark> findNegativeThin(boolean[] core,int w,int h,float pxPerMm){
        boolean[] bg=new boolean[core.length];for(int i=0;i<core.length;i++)bg[i]=!core[i];
        boolean[] outside=new boolean[core.length];ArrayDeque<Integer> q=new ArrayDeque<>();
        for(int x=0;x<w;x++){seed(bg,outside,q,x);seed(bg,outside,q,(h-1)*w+x);}for(int y=0;y<h;y++){seed(bg,outside,q,y*w);seed(bg,outside,q,y*w+w-1);}
        while(!q.isEmpty()){int v=q.removeFirst(),y=v/w,x=v-y*w;if(x>0)seed(bg,outside,q,v-1);if(x+1<w)seed(bg,outside,q,v+1);if(y>0)seed(bg,outside,q,v-w);if(y+1<h)seed(bg,outside,q,v+w);}
        boolean[] holes=new boolean[core.length];for(int i=0;i<holes.length;i++)holes[i]=bg[i]&&!outside[i];
        return findThinComponents(holes,w,h,pxPerMm,true);
    }

    private static float estimateMaxThickness(boolean[] mask,int w,int h,int x0,int y0,int x1,int y1,int cap){
        int bw=x1-x0+1,bh=y1-y0+1;int[] d=new int[bw*bh];int inf=9999,max=0;
        for(int y=0;y<bh;y++)for(int x=0;x<bw;x++)d[y*bw+x]=mask[(y0+y)*w+x0+x]?inf:0;
        for(int y=0;y<bh;y++)for(int x=0;x<bw;x++){
            int i=y*bw+x;if(d[i]==0)continue;int v=d[i];
            if(x==0||y==0||x==bw-1||y==bh-1)v=1;
            if(x>0)v=Math.min(v,d[i-1]+1);if(y>0)v=Math.min(v,d[i-bw]+1);d[i]=v;
        }
        for(int y=bh-1;y>=0;y--)for(int x=bw-1;x>=0;x--){int i=y*bw+x;if(d[i]==0)continue;int v=d[i];if(x+1<bw)v=Math.min(v,d[i+1]+1);if(y+1<bh)v=Math.min(v,d[i+bw]+1);d[i]=v;max=Math.max(max,Math.min(cap,v));}
        return Math.max(1,2*max-1);
    }

    private static void add(boolean[] m,boolean[] s,ArrayDeque<Integer>q,int n){if(m[n]&&!s[n]){s[n]=true;q.add(n);}}
    private static void seed(boolean[] m,boolean[] s,ArrayDeque<Integer>q,int n){if(m[n]&&!s[n]){s[n]=true;q.add(n);}}

    private static void annotate(Bitmap source,VisualData vd,File out)throws Exception{
        Bitmap copy=source.copy(Bitmap.Config.ARGB_8888,true);Canvas canvas=new Canvas(copy);
        Paint outer=new Paint(Paint.ANTI_ALIAS_FLAG);outer.setStyle(Paint.Style.STROKE);outer.setStrokeWidth(9f);outer.setColor(Color.rgb(30,30,30));
        Paint inner=new Paint(Paint.ANTI_ALIAS_FLAG);inner.setStyle(Paint.Style.STROKE);inner.setStrokeWidth(5f);
        for(Mark m:vd.positiveMarks){canvas.drawCircle(m.x,m.y,m.radius,outer);inner.setColor(Color.YELLOW);canvas.drawCircle(m.x,m.y,m.radius,inner);}
        for(Mark m:vd.negativeMarks){canvas.drawCircle(m.x,m.y,m.radius,outer);inner.setColor(Color.CYAN);canvas.drawCircle(m.x,m.y,m.radius,inner);}
        try(OutputStream os=new FileOutputStream(out)){copy.compress(Bitmap.CompressFormat.PNG,95,os);}finally{copy.recycle();}
    }

    private static int countArtworkText(List<TextMark> lm,List<TextMark> cm,Models.PageIndex lp,Models.PageIndex cp,RectI crop,RectI ccrop,boolean[] mask,int mw,int mh){
        int count=0;
        for(TextMark t:lm){
            float lx=t.x/lp.pageWidthPt*lp.width;
            float ly=lp.height-(t.y/lp.pageHeightPt*lp.height);
            if(lx<crop.x0||lx>crop.x1||ly<crop.y0||ly>crop.y1)continue;
            float cx=lx-(crop.x0-ccrop.x0), cy=ly-(crop.y0-ccrop.y0);
            boolean template=false;
            for(TextMark c:cm){
                float cix=c.x/cp.pageWidthPt*cp.width, ciy=cp.height-(c.y/cp.pageHeightPt*cp.height);
                if(Math.abs(cix-cx)<=8&&Math.abs(ciy-cy)<=8&&Math.abs(c.size-t.size)<=2.5f){template=true;break;}
            }
            if(template)continue;
            int px=Math.round((lx-crop.x0)/Math.max(1,crop.w())*mw),py=Math.round((ly-crop.y0)/Math.max(1,crop.h())*mh);
            if(maskNear(mask,mw,mh,px,py,Math.max(12,Math.round(t.size*0.8f))))count++;
        }
        return count;
    }

    private static boolean maskNear(boolean[] m,int w,int h,int cx,int cy,int r){
        int x0=Math.max(0,cx-r),x1=Math.min(w-1,cx+r),y0=Math.max(0,cy-r),y1=Math.min(h-1,cy+r);
        for(int y=y0;y<=y1;y+=2)for(int x=x0;x<=x1;x+=2)if(m[y*w+x])return true;return false;
    }

    private static RawFlags inspectRaw(File f)throws Exception{
        String s=new String(readAll(f),StandardCharsets.ISO_8859_1);RawFlags r=new RawFlags();
        r.shading=Pattern.compile("/Shading(?:Type)?\\b").matcher(s).find();
        r.transparency=Pattern.compile("/SMask\\s*(?!/None)|/S\\s*/Transparency|/(?:ca|CA)\\s+(?:0(?:\\.\\d+)?|\\.\\d+)").matcher(s).find();
        Matcher bm=Pattern.compile("/BM\\s*/([A-Za-z]+)").matcher(s);while(bm.find())if(!"Normal".equalsIgnoreCase(bm.group(1))){r.nonNormalBlend=true;break;}
        return r;
    }

    private static List<TextMark> extractTextMarks(File f,int pageNo){
        try{
            byte[] bytes=readAll(f);String all=new String(bytes,StandardCharsets.ISO_8859_1);
            LinkedHashMap<Integer,String> objects=new LinkedHashMap<>();Matcher om=Pattern.compile("(?s)(\\d+)\\s+\\d+\\s+obj(.*?)endobj").matcher(all);
            while(om.find())objects.put(Integer.parseInt(om.group(1)),om.group(2));
            ArrayList<String> pages=new ArrayList<>();for(String v:objects.values())if(Pattern.compile("/Type\\s*/Page\\b").matcher(v).find()&&!Pattern.compile("/Type\\s*/Pages\\b").matcher(v).find())pages.add(v);
            if(pageNo<0||pageNo>=pages.size())return Collections.emptyList();String p=pages.get(pageNo);ArrayList<Integer> refs=new ArrayList<>();
            Matcher one=Pattern.compile("/Contents\\s+(\\d+)\\s+\\d+\\s+R").matcher(p);if(one.find())refs.add(Integer.parseInt(one.group(1)));
            Matcher arr=Pattern.compile("(?s)/Contents\\s*\\[(.*?)\\]").matcher(p);if(arr.find()){Matcher rm=Pattern.compile("(\\d+)\\s+\\d+\\s+R").matcher(arr.group(1));while(rm.find())refs.add(Integer.parseInt(rm.group(1)));}
            ArrayList<TextMark> out=new ArrayList<>();for(Integer ref:refs){String obj=objects.get(ref);if(obj==null)continue;String stream=decodeStream(obj);if(stream!=null)parseTextStream(stream,out);}return out;
        }catch(Exception ignored){return Collections.emptyList();}
    }

    private static String decodeStream(String obj){
        int s=obj.indexOf("stream");if(s<0)return null;int start=s+6;if(start<obj.length()&&obj.charAt(start)=='\r')start++;if(start<obj.length()&&obj.charAt(start)=='\n')start++;int end=obj.indexOf("endstream",start);if(end<0)return null;
        byte[] data=obj.substring(start,end).getBytes(StandardCharsets.ISO_8859_1);
        try{if(obj.substring(0,s).contains("/FlateDecode")){try(InflaterInputStream in=new InflaterInputStream(new ByteArrayInputStream(data));ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];for(int n;(n=in.read(b))>0;)out.write(b,0,n);data=out.toByteArray();}}return new String(data,StandardCharsets.ISO_8859_1);}catch(Exception e){return null;}
    }

    private static void parseTextStream(String s,List<TextMark> out){
        Matcher blocks=Pattern.compile("(?s)BT(.*?)ET").matcher(s);Pattern op=Pattern.compile("(?s)([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+Tm|([-+]?\\d*\\.?\\d+)\\s+([-+]?\\d*\\.?\\d+)\\s+T[dD]|/[^\\s]+\\s+([-+]?\\d*\\.?\\d+)\\s+Tf|(\\([^\\r\\n]*?\\)|<[^>]*>|\\[[^\\]]*\\])\\s*(Tj|TJ|'|\\\")");
        while(blocks.find()){
            String b=blocks.group(1);Matcher m=op.matcher(b);float x=Float.NaN,y=Float.NaN,size=0;
            while(m.find()){
                try{
                    if(m.group(1)!=null){x=Float.parseFloat(m.group(5));y=Float.parseFloat(m.group(6));}
                    else if(m.group(7)!=null){float dx=Float.parseFloat(m.group(7)),dy=Float.parseFloat(m.group(8));if(Float.isNaN(x)){x=dx;y=dy;}else{x+=dx;y+=dy;}}
                    else if(m.group(9)!=null){size=Float.parseFloat(m.group(9));}
                    else if(m.group(10)!=null&&!Float.isNaN(x)&&!Float.isNaN(y)){TextMark t=new TextMark();t.x=x;t.y=y;t.size=Math.max(1,size);out.add(t);}
                }catch(Exception ignored){}
            }
        }
    }

    private static int colorDiff(int a,int b){return Math.max(Math.abs(Color.red(a)-Color.red(b)),Math.max(Math.abs(Color.green(a)-Color.green(b)),Math.abs(Color.blue(a)-Color.blue(b))));}
    private static byte[] readAll(File f)throws Exception{try(InputStream in=new FileInputStream(f);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[65536];for(int n;(n=in.read(b))>0;)out.write(b,0,n);return out.toByteArray();}}
    private static String safe(String s){return s==null?"file":s.replaceAll("[^0-9A-Za-zА-Яа-я._-]+","_");}

    private static final class RawFlags{boolean shading,transparency,nonNormalBlend;}
    private static final class TextMark{float x,y,size;}
    private static final class RectI{int x0,y0,x1,y1;RectI(int a,int b,int c,int d){x0=a;y0=b;x1=c;y1=d;}int w(){return x1-x0;}int h(){return y1-y0;}}
    private static final class Mark{int x,y,radius;boolean negative;float sizeMm;}
    private static final class VisualData{boolean[] coreMask,softMask;int w,h;float pxPerMm;List<Mark> positiveMarks,negativeMarks;boolean gradientSuspected,softEffectSuspected;}
}
