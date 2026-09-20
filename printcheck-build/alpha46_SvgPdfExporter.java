package ru.printcheck.android;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.pdf.PdfDocument;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * Renders a clean physical-size SVG into a one-page PDF used only as a normalized
 * Quick Check transport. The ready production artifact remains the saved SVG.
 *
 * This deliberately avoids PrintDocumentAdapter callbacks: their constructors are
 * package-private on Android and cannot be instantiated by an app.
 */
final class SvgPdfExporter {
    interface Callback { void done(File pdf); void error(Exception e); }

    static void export(Activity a, WebView web, String svg, double widthMm, double heightMm, File out, Callback cb) {
        a.runOnUiThread(() -> {
            try {
                web.getSettings().setJavaScriptEnabled(false);
                web.getSettings().setAllowFileAccess(false);
                web.getSettings().setAllowContentAccess(false);
                web.getSettings().setBlockNetworkLoads(true);
                web.setLayerType(View.LAYER_TYPE_SOFTWARE, null);
                web.setWebViewClient(new WebViewClient() {
                    @Override public void onPageFinished(WebView v, String url) {
                        v.postDelayed(() -> render(a, v, widthMm, heightMm, out, cb), 180);
                    }
                });
                String html = "<!doctype html><html><head><meta charset='utf-8'>"
                    + "<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1'>"
                    + "<style>html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#fff}"
                    + "svg{display:block;margin:0;padding:0;width:100vw!important;height:100vh!important}</style>"
                    + "</head><body>" + svg + "</body></html>";
                web.loadDataWithBaseURL("https://printcheck.local/", html, "text/html", "UTF-8", null);
            } catch (Exception e) {
                cb.error(e);
            }
        });
    }

    private static void render(Activity a, WebView web, double wMm, double hMm, File out, Callback cb) {
        try {
            if (!(wMm > 0) || !(hMm > 0)) throw new IOException("Некорректный физический размер SVG.");

            final double targetDpi = 300.0;
            int pxW = Math.max(64, (int)Math.round(wMm / 25.4 * targetDpi));
            int pxH = Math.max(64, (int)Math.round(hMm / 25.4 * targetDpi));
            final int maxSide = 5000;
            final long maxPixels = 16_000_000L;
            double scale = Math.min(1.0, Math.min(maxSide / (double)Math.max(pxW, pxH),
                Math.sqrt(maxPixels / (double)Math.max(1L, (long)pxW * (long)pxH))));
            if (scale < 1.0) {
                pxW = Math.max(64, (int)Math.round(pxW * scale));
                pxH = Math.max(64, (int)Math.round(pxH * scale));
            }

            web.measure(
                View.MeasureSpec.makeMeasureSpec(pxW, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(pxH, View.MeasureSpec.EXACTLY));
            web.layout(0, 0, pxW, pxH);

            int wPt = Math.max(1, (int)Math.round(wMm / 25.4 * 72.0));
            int hPt = Math.max(1, (int)Math.round(hMm / 25.4 * 72.0));

            File parent = out.getParentFile();
            if (parent != null) parent.mkdirs();

            PdfDocument doc = new PdfDocument();
            FileOutputStream fos = null;
            try {
                PdfDocument.PageInfo info = new PdfDocument.PageInfo.Builder(wPt, hPt, 1).create();
                PdfDocument.Page page = doc.startPage(info);
                Canvas canvas = page.getCanvas();
                canvas.scale(wPt / (float)pxW, hPt / (float)pxH);
                web.draw(canvas);
                doc.finishPage(page);

                fos = new FileOutputStream(out, false);
                doc.writeTo(fos);
                fos.flush();
            } finally {
                try { if (fos != null) fos.close(); } catch (Exception ignored) {}
                try { doc.close(); } catch (Exception ignored) {}
            }

            if (!out.isFile() || out.length() < 100) throw new IOException("PDF не был создан.");
            cb.done(out);
        } catch (Exception e) {
            cb.error(e);
        }
    }
}
