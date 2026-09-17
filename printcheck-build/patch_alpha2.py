from pathlib import Path
import sys

root = Path(sys.argv[1])

# Bump the app version everywhere derived from BuildConfig.
bg = root / 'app' / 'build.gradle'
s = bg.read_text(encoding='utf-8')
s = s.replace('versionCode 300004', 'versionCode 300005')
s = s.replace("versionName '3.1.0-alpha1'", "versionName '3.1.0-alpha2'")
bg.write_text(s, encoding='utf-8')

p = root / 'app' / 'src' / 'main' / 'java' / 'ru' / 'printcheck' / 'android' / 'ReadOnlyHttp.java'
s = p.read_text(encoding='utf-8')
a = s.index('    String get(String url) throws Exception {')
b = s.index('\n    private static byte[] readLimited', a)

repl = r'''    String get(String url) throws Exception {
        IOException last = null;
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                return getOnce(url);
            } catch (IOException e) {
                last = e;
                HttpURLConnection c = active;
                active = null;
                if (c != null) c.disconnect();
                if (!isRetryable(e) || attempt == 3) throw e;
                try { Thread.sleep(350L * attempt); }
                catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new IOException("Чтение остановлено", ie);
                }
            }
        }
        throw last == null ? new IOException("Неизвестная ошибка HTTP") : last;
    }

    private String getOnce(String initialUrl) throws Exception {
        String url = initialUrl;
        for (int redirects = 0; redirects < 6; redirects++) {
            assertReadOnly("GET", url);
            HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
            active = c;
            c.setRequestMethod("GET");
            c.setInstanceFollowRedirects(false);
            c.setUseCaches(false);
            c.setConnectTimeout(25000);
            c.setReadTimeout(45000);
            c.setRequestProperty("User-Agent", userAgent);
            c.setRequestProperty("Accept", "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8");
            c.setRequestProperty("Accept-Language", "ru-RU,ru;q=0.9,en;q=0.5");
            c.setRequestProperty("Connection", "close");
            c.setRequestProperty("Accept-Encoding", "identity");
            c.setRequestProperty("Cache-Control", "no-cache");
            c.setRequestProperty("Pragma", "no-cache");
            if (url.contains("/ajax/gifts/order?action=makets_popup")) {
                c.setRequestProperty("X-Requested-With", "XMLHttpRequest");
                c.setRequestProperty("Referer", "https://gifts.ru/private/");
            }
            String cookie = CookieManager.getInstance().getCookie(url);
            if (cookie != null && !cookie.isEmpty()) c.setRequestProperty("Cookie", cookie);
            int code = c.getResponseCode();
            if (code >= 300 && code < 400) {
                String next = c.getHeaderField("Location");
                c.disconnect();
                active = null;
                if (next == null) throw new IOException("Перенаправление без адреса");
                url = new URL(new URL(url), next).toString();
                continue;
            }
            if (code != 200) {
                c.disconnect();
                active = null;
                throw new IOException("HTTP " + code + " при чтении " + Safety.logUrl(url));
            }
            try (InputStream in = new BufferedInputStream(c.getInputStream(), 65536)) {
                byte[] data = readLimited(in, HTML_LIMIT);
                String text = new String(data, StandardCharsets.UTF_8);
                c.disconnect();
                active = null;
                return text;
            } catch (IOException e) {
                c.disconnect();
                active = null;
                throw e;
            }
        }
        throw new IOException("Слишком много перенаправлений");
    }

    private static boolean isRetryable(IOException e) {
        String m = String.valueOf(e.getMessage()).toLowerCase(Locale.ROOT);
        return m.contains("unexpected end of stream") || m.contains("end of stream") ||
               m.contains("connection reset") || m.contains("connection closed") ||
               m.contains("stream was reset") || m.contains("broken pipe") ||
               m.contains("timeout") || m.contains("timed out");
    }
'''

p.write_text(s[:a] + repl + s[b:], encoding='utf-8')

# Keep downloads conservative too: no pooled connection and no compressed transfer.
ma = root / 'app' / 'src' / 'main' / 'java' / 'ru' / 'printcheck' / 'android' / 'MainActivity.java'
t = ma.read_text(encoding='utf-8')
old = 'c.setInstanceFollowRedirects(false);c.setConnectTimeout(20000);c.setReadTimeout(30000);c.setRequestProperty("User-Agent",userAgent);'
new = 'c.setInstanceFollowRedirects(false);c.setUseCaches(false);c.setConnectTimeout(25000);c.setReadTimeout(45000);c.setRequestProperty("User-Agent",userAgent);c.setRequestProperty("Connection","close");c.setRequestProperty("Accept-Encoding","identity");c.setRequestProperty("Cache-Control","no-cache");'
if old in t:
    t = t.replace(old, new)
ma.write_text(t, encoding='utf-8')

print('alpha2 patch applied')
