'use strict';
async function collectAndroidOrder() {
  const clean = t => (t || '').replace(/\s+/g, ' ').trim();
  const log = [];
  const rec = (event, data={}) => log.push({t:Date.now(), event, ...data});
  if (location.origin !== 'https://gifts.ru' || !/^\/private\/order(?:\/|$)/.test(location.pathname)) {
    throw new Error('Откройте страницу заказа gifts.ru');
  }
  const rows = [...document.querySelectorAll('li[data-itemid]')];
  if (!rows.length) throw new Error('Позиции заказа не найдены. Возможно, требуется вход.');
  const orderNumber = (document.title.match(/Заказ\s*№?\s*(\d+)/i) || location.pathname.match(/\/private\/order\/(\d+)/) || [])[1] || '';
  const items = [];
  for (const row of rows) {
    const product = row.querySelector('a.cart-tbl-name[href]');
    if (!product) continue;
    const article = (clean(product.textContent).match(/\d+(?:\.\d+)*/) || [])[0];
    if (!article) continue;
    items.push({item_id: row.getAttribute('data-itemid') || '', article, name: clean(product.parentElement?.textContent)});
  }
  const articles = [...new Set(items.map(x => x.article))];
  rec('order', {orderNumber, rows: rows.length, articles});

  const safeUrl = href => {
    try {
      const u = new URL(href, location.href);
      if (u.protocol !== 'https:' || !['gifts.ru','files.gifts.ru'].includes(u.hostname)) return null;
      if (/\.(cdr)$/i.test(u.pathname)) return null;
      const ok = /\.pdf$/i.test(u.pathname) || /^\/cart\/act\/mda$/.test(u.pathname) || /^\/private\/order\/act\/amda\/\d+$/.test(u.pathname);
      return ok ? u.href : null;
    } catch { return null; }
  };

  const before = new Set([...document.querySelectorAll('a[href]')].map(a => safeUrl(a.href)).filter(Boolean));
  const global = document.querySelector('a.j_add_maket, a[data-ga-action="Макеты для заказа"]');
  if (!global) throw new Error('Кнопка «Макеты для заказа» не найдена');
  global.click(); rec('popup-click');
  let stable = 0, last = '';
  for (let i=0;i<40;i++) {
    await new Promise(r => setTimeout(r, 300));
    const sig = [...document.querySelectorAll('a[href]')].map(a => safeUrl(a.href)).filter(Boolean).sort().join('\n');
    stable = sig === last ? stable + 1 : 0; last = sig;
    if (stable >= 3 && sig) break;
  }
  const anchors = [...document.querySelectorAll('a[href]')];
  const files = anchors.map(a => ({url:safeUrl(a.href), label:clean(a.textContent), el:a})).filter(x => x.url && !before.has(x.url));
  const layouts = [];
  const constructors = [];

  const findArticleNear = a => {
    let n = a;
    for (let depth=0; n && depth<10; depth++, n=n.parentElement) {
      const text = clean(n.textContent).replace(/,/g,'.');
      const explicit = text.match(/(?:арт(?:икул)?\.?|article)\s*(?:[:№#]|\s)*\s*(\d+(?:\.\d+)*)/i);
      if (explicit && articles.includes(explicit[1])) return explicit[1];
      const hits = articles.filter(x => new RegExp(`(^|[^0-9.])${x.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?=$|[^0-9.])`).test(text));
      if (hits.length === 1) return hits[0];
    }
    return null;
  };

  for (const f of files) {
    const u = new URL(f.url);
    if (/\/reviewer\/constructor\//.test(u.pathname)) {
      const article = findArticleNear(f.el);
      constructors.push({url:f.url, label:f.label || u.pathname.split('/').pop(), article});
      rec('constructor', {file:f.label, article});
    } else {
      layouts.push({url:f.url, label:f.label || u.pathname.split('/').pop() || 'layout.pdf'});
      rec('layout', {file:f.label});
    }
  }

  const dedupe = arr => [...new Map(arr.map(x => [x.url, x])).values()];
  const out = {orderNumber, items, layouts:dedupe(layouts), constructors:dedupe(constructors), diagnostic:log};
  rec('done', {layouts:out.layouts.length, constructors:out.constructors.length, mapped:out.constructors.filter(x=>x.article).length});
  return out;
}
