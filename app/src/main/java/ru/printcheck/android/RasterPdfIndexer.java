package ru.printcheck.android;

import android.graphics.*;
import android.graphics.pdf.PdfRenderer;
import android.os.ParcelFileDescriptor;
import java.io.*;
import java.util.*;

final class RasterPdfIndexer {
    static final int DPI = 100;
    private static final int MIN_PIXELS = 18;
    private static final int MIN_BOX = 3;
    interface Progress { void onProgress(String s); }

    static Models.PdfIndex index(Models.RemotePdf pdf, Progress cb) throws Exception {
        Models.PdfIndex out = new Models.PdfIndex(); out.pdf = pdf;
        try (ParcelFileDescriptor pfd = ParcelFileDescriptor.open(pdf.file, ParcelFileDescriptor.MODE_READ_ONLY);
             PdfRenderer renderer = new PdfRenderer(pfd)) {
            for (int pi=0; pi<renderer.getPageCount(); pi++) {
                try (PdfRenderer.Page page = renderer.openPage(pi)) {
                    int w = Math.max(1, Math.round(page.getWidth() * DPI / 72f));
                    int h = Math.max(1, Math.round(page.getHeight() * DPI / 72f));
                    float scale = Math.min(1f, 2200f / Math.max(w,h));
                    w = Math.max(1, Math.round(w*scale)); h = Math.max(1, Math.round(h*scale));
                    Bitmap bmp = Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
                    bmp.eraseColor(Color.WHITE);
                    page.render(bmp,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
                    Models.PageIndex idx = new Models.PageIndex(); idx.page=pi; idx.width=w; idx.height=h;
                    idx.features = extract(bmp);
                    out.pages.add(idx);
                    if (cb!=null) cb.onProgress(pdf.label+" · стр. "+(pi+1)+" · признаков "+idx.features.size());
                    bmp.recycle();
                }
            }
        }
        return out;
    }

    static List<Models.Feature> extract(Bitmap b) {
        final int w=b.getWidth(), h=b.getHeight();
        int[] px = new int[w*h]; b.getPixels(px,0,w,0,0,w,h);
        boolean[] fg = new boolean[w*h];
        for(int i=0;i<px.length;i++){
            int c=px[i], r=Color.red(c), g=Color.green(c), bl=Color.blue(c);
            int max=Math.max(r,Math.max(g,bl)), min=Math.min(r,Math.min(g,bl));
            fg[i] = max < 238 || (max-min)>28;
        }
        boolean[] d = new boolean[w*h];
        for(int y=1;y<h-1;y++) for(int x=1;x<w-1;x++) if(fg[y*w+x]){
            int q=y*w+x; d[q]=d[q-1]=d[q+1]=d[q-w]=d[q+w]=true;
        }
        boolean[] seen=new boolean[w*h]; ArrayList<Models.Feature> out=new ArrayList<>();
        for(int sy=0;sy<h;sy++) for(int sx=0;sx<w;sx++){
            int si=sy*w+sx; if(!d[si]||seen[si]) continue;
            int count=0,minx=sx,maxx=sx,miny=sy,maxy=sy;
            ArrayDeque<Integer> q=new ArrayDeque<>(); q.add(si); seen[si]=true;
            while(!q.isEmpty()){
                int v=q.removeFirst(), y=v/w, x=v-y*w; count++;
                if(x<minx)minx=x;if(x>maxx)maxx=x;if(y<miny)miny=y;if(y>maxy)maxy=y;
                if(x>0){int n=v-1;if(d[n]&&!seen[n]){seen[n]=true;q.add(n);}}
                if(x+1<w){int n=v+1;if(d[n]&&!seen[n]){seen[n]=true;q.add(n);}}
                if(y>0){int n=v-w;if(d[n]&&!seen[n]){seen[n]=true;q.add(n);}}
                if(y+1<h){int n=v+w;if(d[n]&&!seen[n]){seen[n]=true;q.add(n);}}
            }
            int bw=maxx-minx+1,bh=maxy-miny+1;
            if(count<MIN_PIXELS || Math.max(bw,bh)<MIN_BOX) continue;
            if(bw>0.97*w && bh>0.97*h) continue;
            long sig=signature(d,w,h,minx,miny,maxx,maxy);
            out.add(new Models.Feature(minx,miny,bw,bh,count,sig));
        }
        out.sort((a,c)->Integer.compare(c.area(),a.area()));
        if(out.size()>500) return new ArrayList<>(out.subList(0,500));
        return out;
    }

    private static long signature(boolean[] fg,int W,int H,int x0,int y0,int x1,int y1){
        long s=0; int bw=Math.max(1,x1-x0+1), bh=Math.max(1,y1-y0+1);
        for(int gy=0;gy<8;gy++) for(int gx=0;gx<8;gx++){
            int ax=x0+gx*bw/8, bx=x0+(gx+1)*bw/8;
            int ay=y0+gy*bh/8, by=y0+(gy+1)*bh/8;
            int n=0, hit=0;
            for(int y=ay;y<Math.max(ay+1,by)&&y<H;y+=Math.max(1,(by-ay)/3))
                for(int x=ax;x<Math.max(ax+1,bx)&&x<W;x+=Math.max(1,(bx-ax)/3)){n++;if(fg[y*W+x])hit++;}
            if(n>0 && hit*5>=n) s|=1L<<(gy*8+gx);
        }
        return s;
    }
}
