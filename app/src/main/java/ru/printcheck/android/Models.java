package ru.printcheck.android;

import java.io.File;
import java.util.*;

final class Models {
    static final class RemotePdf {
        String url, label, article;
        File file;
        RemotePdf(String u, String l, String a){url=u;label=l;article=a;}
    }

    static final class Feature {
        final int x,y,w,h,pixels;
        final long signature;
        Feature(int x,int y,int w,int h,int pixels,long signature){
            this.x=x;this.y=y;this.w=w;this.h=h;this.pixels=pixels;this.signature=signature;
        }
        int area(){return Math.max(1,w*h);}
    }

    static final class PageIndex {
        int page, width, height;
        float pageWidthPt, pageHeightPt;
        List<Feature> features = new ArrayList<>();
    }

    static final class PdfIndex {
        RemotePdf pdf;
        List<PageIndex> pages = new ArrayList<>();
        PageIndex page(int n){
            for(PageIndex p:pages) if(p.page==n) return p;
            return null;
        }
    }

    static final class Occurrence {
        String layoutFile, constructorFile, article;
        int layoutPage, constructorPage;
        int dx,dy, matched,total;
        double coverage, score;
        int x0,y0,x1,y1;
        String id;
    }

    static final class CompareStats {
        int sizeCandidates, signatureCandidates, voteClusters, confirmed;
        double bestCoverage, bestScore;
    }

    enum Severity { ERROR, WARNING, INFO }

    static final class Finding {
        String code;
        Severity severity;
        String message;
        int page;
        float xMm, yMm, sizeMm;
        Finding(String code, Severity severity, String message, int page){
            this.code=code;this.severity=severity;this.message=message;this.page=page;
        }
    }

    static final class TechnicalReport {
        String occurrenceId, layoutFile, article;
        int page;
        int positiveSmall, negativeSmall, liveTextCount;
        boolean gradientSuspected, softEffectSuspected;
        boolean pdfHasShading, pdfHasTransparency, pdfHasBlendMode;
        File annotatedImage;
        final List<Finding> findings = new ArrayList<>();
        boolean hasErrors(){
            for(Finding f:findings) if(f.severity==Severity.ERROR) return true;
            return false;
        }
        boolean hasWarnings(){
            for(Finding f:findings) if(f.severity==Severity.WARNING) return true;
            return false;
        }
    }
}
