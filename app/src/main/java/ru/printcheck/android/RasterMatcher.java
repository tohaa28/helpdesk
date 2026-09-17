package ru.printcheck.android;

import java.util.*;

final class RasterMatcher {
    static final int SIZE_TOL=3, SHIFT_BIN=4, SHIFT_TOL=5, HAMMING_TOL=22;

    static List<Models.Occurrence> compare(Models.PdfIndex layout, Models.PdfIndex cons, Models.CompareStats stats){
        ArrayList<Models.Occurrence> all=new ArrayList<>();
        for(Models.PageIndex lp:layout.pages) for(Models.PageIndex cp:cons.pages){
            all.addAll(comparePage(layout.pdf,lp,cons.pdf,cp,stats));
        }
        return dedupe(all);
    }

    private static List<Models.Occurrence> comparePage(Models.RemotePdf layout, Models.PageIndex lp, Models.RemotePdf cons, Models.PageIndex cp, Models.CompareStats stats){
        HashMap<Long,ArrayList<Pair>> votes=new HashMap<>();
        List<Models.Feature> C=cp.features,L=lp.features;
        int consTotalPixels=0; for(Models.Feature c:C) if(structural(c)) consTotalPixels+=Math.min(c.pixels,50000);
        if(consTotalPixels==0) return Collections.emptyList();
        for(int ci=0;ci<C.size();ci++){
            Models.Feature c=C.get(ci); if(!structural(c)) continue;
            for(int li=0;li<L.size();li++){
                Models.Feature l=L.get(li);
                if(Math.abs(c.w-l.w)>SIZE_TOL||Math.abs(c.h-l.h)>SIZE_TOL) continue;
                stats.sizeCandidates++;
                int ham=Long.bitCount(c.signature^l.signature);
                double pixRatio=Math.min(c.pixels,l.pixels)/(double)Math.max(c.pixels,l.pixels);
                if(ham>HAMMING_TOL || pixRatio<0.42) continue;
                stats.signatureCandidates++;
                int dx=l.x-c.x,dy=l.y-c.y;
                long key=(((long)Math.round(dx/(double)SHIFT_BIN))<<32) ^ (Math.round(dy/(double)SHIFT_BIN)&0xffffffffL);
                votes.computeIfAbsent(key,k->new ArrayList<>()).add(new Pair(ci,li,dx,dy));
            }
        }
        stats.voteClusters+=votes.size();
        ArrayList<Models.Occurrence> out=new ArrayList<>();
        for(ArrayList<Pair> raw:votes.values()){
            raw.sort((a,b)->Integer.compare(C.get(b.ci).area(),C.get(a.ci).area()));
            HashSet<Integer> uc=new HashSet<>(),ul=new HashSet<>(); ArrayList<Pair> chosen=new ArrayList<>();
            for(Pair p:raw) if(uc.add(p.ci)&&ul.add(p.li)) chosen.add(p);
            if(chosen.isEmpty()) continue;
            double dx=0,dy=0;for(Pair p:chosen){dx+=p.dx;dy+=p.dy;}dx/=chosen.size();dy/=chosen.size();
            double spread=0;for(Pair p:chosen)spread=Math.max(spread,Math.max(Math.abs(p.dx-dx),Math.abs(p.dy-dy)));
            if(spread>SHIFT_TOL) continue;
            int matchedPixels=0,x0=Integer.MAX_VALUE,y0=Integer.MAX_VALUE,x1=0,y1=0;
            for(Pair p:chosen){Models.Feature c=C.get(p.ci),l=L.get(p.li);matchedPixels+=Math.min(c.pixels,50000);x0=Math.min(x0,l.x);y0=Math.min(y0,l.y);x1=Math.max(x1,l.x+l.w);y1=Math.max(y1,l.y+l.h);}
            double coverage=Math.min(1,matchedPixels/(double)consTotalPixels);
            int structuralCount=0;for(Models.Feature c:C)if(structural(c))structuralCount++;
            double ratio=chosen.size()/(double)Math.max(1,structuralCount);
            boolean confirmed=(chosen.size()>=2&&coverage>=0.34)||(chosen.size()>=3&&ratio>=0.35)||(chosen.size()==1&&coverage>=0.78&&C.get(chosen.get(0).ci).area()>4000);
            double score=Math.min(0.999,0.58*coverage+0.27*Math.min(1,chosen.size()/3.0)+0.15*Math.min(1,ratio/0.5));
            stats.bestCoverage=Math.max(stats.bestCoverage,coverage);stats.bestScore=Math.max(stats.bestScore,score);
            if(!confirmed) continue;
            stats.confirmed++;
            Models.Occurrence o=new Models.Occurrence();
            o.layoutFile=layout.label;o.constructorFile=cons.label;o.article=cons.article;o.layoutPage=lp.page;o.constructorPage=cp.page;
            o.dx=(int)Math.round(dx);o.dy=(int)Math.round(dy);o.matched=chosen.size();o.total=structuralCount;o.coverage=coverage;o.score=score;
            o.x0=x0;o.y0=y0;o.x1=x1;o.y1=y1;
            out.add(o);
        }
        return out;
    }

    private static boolean structural(Models.Feature f){return f.area()>=45 && Math.max(f.w,f.h)>=7;}
    private static List<Models.Occurrence> dedupe(List<Models.Occurrence> src){
        src.sort((a,b)->Double.compare(b.score,a.score));ArrayList<Models.Occurrence> out=new ArrayList<>();
        for(Models.Occurrence o:src){boolean dup=false;for(Models.Occurrence k:out){
            if(k.layoutPage==o.layoutPage && Math.abs(k.dx-o.dx)<=8 && Math.abs(k.dy-o.dy)<=8){dup=true;break;}
        }if(!dup)out.add(o);}
        return out;
    }
    private static final class Pair{int ci,li,dx,dy;Pair(int a,int b,int c,int d){ci=a;li=b;dx=c;dy=d;}}
}
