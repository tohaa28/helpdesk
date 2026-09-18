'use strict';
async function collectAndroidOrder() {
  const clean = t => (t || '').replace(/\s+/g, ' ').trim();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
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
    const article = (clean(product.textContent).replace(/,/g,'.').match(/\d+(?:\.\d+)*/) || [])[0];
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
      const ok = /\.pdf$/i.test(u.pathname) || /^\/cart\/act\/mda$/.test(u.pathname) || /^\/private\/order\/act\/amda\/\d+$/.test(u.pathname) || /\/reviewer\/constructor\//.test(u.pathname);
      return ok ? u.href : null;
    } catch { return null; }
  };

  const visible = el => {
    if (!el) return false;
    const st = getComputedStyle(el);
    return st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0' && (el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  };
  const anchorRows = () => [...document.querySelectorAll('a[href]')]
      .filter(a => visible(a))
      .map(a => ({url:safeUrl(a.href), label:clean(a.textContent), el:a}))
      .filter(x => x.url);

  const before = new Set([...document.querySelectorAll('a[href]')].map(a => safeUrl(a.href)).filter(Boolean));
  const global = document.querySelector('a.j_add_maket, a[data-ga-action="Макеты для заказа"]');
  if (!global) throw new Error('Кнопка «Макеты для заказа» не найдена');
  global.click(); rec('popup-click');

  for (let i=0;i<40;i++) {
    await sleep(250);
    if ([...document.querySelectorAll('body *')].some(e => /Загрузка макетов|Шаблоны макетов/i.test(clean(e.textContent)) && visible(e))) break;
  }

  const clickTab = async wanted => {
    const candidates = [...document.querySelectorAll('a,button,[role="tab"],li')].filter(visible);
    const el = candidates.find(e => wanted.test(clean(e.textContent)));
    if (!el) { rec('tab-missing',{wanted:String(wanted)}); return false; }
    el.click(); await sleep(450); rec('tab-click',{text:clean(el.textContent)}); return true;
  };

  const collectNewVisible = () => anchorRows().filter(x => !before.has(x.url));
  let uploadLinks = [], templateLinks = [];
  if (await clickTab(/Загрузка\s+макетов/i)) uploadLinks = collectNewVisible();
  if (await clickTab(/Шаблоны\s+макетов/i)) templateLinks = collectNewVisible();

  if (!uploadLinks.length && !templateLinks.length) {
    const all = [...document.querySelectorAll('a[href]')].map(a => ({url:safeUrl(a.href), label:clean(a.textContent), el:a})).filter(x => x.url && !before.has(x.url));
    uploadLinks = all.filter(x => !/\/reviewer\/constructor\//.test(new URL(x.url).pathname));
    templateLinks = all.filter(x => /\/reviewer\/constructor\//.test(new URL(x.url).pathname));
    rec('tabs-fallback',{all:all.length});
  }

  const findArticlesNear = a => {
    let n = a;
    for (let depth=0; n && depth<12; depth++, n=n.parentElement) {
      const text = clean(n.textContent).replace(/,/g,'.');
      const hits = articles.filter(x => new RegExp(`(^|[^0-9.])${x.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?=$|[^0-9.])`).test(text));
      if (hits.length) return hits;
    }
    return [];
  };

  const layouts = [];
  for (const f of uploadLinks) {
    const u = new URL(f.url);
    if (/\/reviewer\/constructor\//.test(u.pathname)) continue;
    layouts.push({url:f.url, label:f.label || u.pathname.split('/').pop() || 'layout.pdf'});
    rec('layout',{file:f.label,url:f.url});
  }

  const constructors = [];
  for (const f of templateLinks) {
    const u = new URL(f.url);
    if (!/\/reviewer\/constructor\//.test(u.pathname) && !/\.pdf$/i.test(u.pathname)) continue;
    const hits = findArticlesNear(f.el);
    if (!hits.length) constructors.push({url:f.url,label:f.label || u.pathname.split('/').pop(),article:null});
    for (const article of hits) constructors.push({url:f.url,label:f.label || u.pathname.split('/').pop(),article});
    rec('constructor',{file:f.label,articles:hits,url:f.url});
  }

  const dedupeLayouts = arr => [...new Map(arr.map(x => [x.url, x])).values()];
  const dedupeConstructors = arr => [...new Map(arr.map(x => [x.url+'|'+(x.article||''), x])).values()];
  const out = {orderNumber, items, layouts:dedupeLayouts(layouts), constructors:dedupeConstructors(constructors), diagnostic:log};
  rec('done', {layouts:out.layouts.length, constructors:out.constructors.length, mapped:out.constructors.filter(x=>x.article).length});
  return out;
}
