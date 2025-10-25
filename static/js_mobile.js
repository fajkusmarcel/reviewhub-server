(function(){
  console.log('[mobile] bootstrap');

  function readData(li){
    try {
      const json = li.querySelector('.js-data')?.textContent || '{}';
      return JSON.parse(json);
    } catch(e){
      console.error('[mobile] JSON parse error', e);
      return {};
    }
  }

  function initFilter(){
    const list = document.getElementById('m-list');
    const search = document.getElementById('m-search');
    const count = document.getElementById('m-count');

    if (!list || !search) {
      console.warn('[mobile] filter init skipped (missing list/search)', { hasList: !!list, hasSearch: !!search });
      return;
    }

    const items = Array.from(list.querySelectorAll('.m-simple-item'));
    function apply(){
      const q = (search.value || '').toLowerCase().trim();
      let shown = 0;
      for (const li of items){
        const d = readData(li);
        const hay = [d.title, d.category, d.subcategory, String(d.year||'')].join(' ').toLowerCase();
        const vis = !q || hay.includes(q);
        li.style.display = vis ? '' : 'none';
        if (vis) shown++;
      }
      if (count) count.textContent = shown + ' výsledků';
    }
    if (count) count.textContent = items.length + ' výsledků';
    search.addEventListener('input', apply);
    console.log('[mobile] filter ready, items=', items.length);
  }

  function initDetail(){
    const list    = document.getElementById('m-list');
    const overlay = document.getElementById('detail-overlay');

    const pdfOvl   = document.getElementById('pdf-overlay');
    const pdfFrame = document.getElementById('pdf-frame');
    const pdfTitle = document.getElementById('pdf-title');
    const pdfBtn   = document.getElementById('d-open-pdf');
    const pdfClose = document.getElementById('btn-close-pdf');
    const btnX     = document.getElementById('d-close');

    if (!list || !overlay) {
      console.warn('[mobile] detail init skipped (missing list/overlay)', { hasList: !!list, hasOverlay: !!overlay });
      return;
    }

    function autobind(container, data){
      container.querySelectorAll('[data-bind]').forEach(el=>{
        const key = el.getAttribute('data-bind');
        const val = (data[key] ?? '').toString();
        el.textContent = val;
      });
    }

function buildPdfUrlFromName(pdfName) {
  if (!pdfName) return "";
  // POZNÁMKA: ve tvém kódu je cesta '/reviewhub/static/uplouds/'
  // (pokud je to překlep a má být 'uploads', změň zde i na serveru)
  const prefix = "/reviewhub/static/uplouds/";
  // Když už je to absolutní URL (http/https) nebo začíná lomítkem, respektuj to
  if (/^https?:\/\//i.test(pdfName)) return pdfName;
  if (pdfName.startsWith("/")) return pdfName;
  return prefix + encodeURIComponent(pdfName);
}

function openDetail(li){
  const data = readData(li);
  console.log('[mobile] openDetail', data);

  // dopočítej pdf_url z pdf_name, pokud chybí
  if ((!data.pdf_url || data.pdf_url === "#") && data.pdf_name) {
    data.pdf_url = buildPdfUrlFromName(data.pdf_name);
  }

  autobind(overlay, data);

  const hasPdf = !!(data.pdf_url && data.pdf_url !== "#");

  if (pdfBtn){
    if (hasPdf){
      pdfBtn.disabled = false;
      pdfBtn.onclick = function(){
        console.log('[mobile] opening PDF:', data.pdf_url);
        pdfTitle.textContent = data.title || '';
        pdfFrame.src = data.pdf_url;
        pdfOvl.hidden = false;
        document.body.classList.add('m-no-scroll');
      };
    } else {
      pdfBtn.disabled = true;
      pdfBtn.onclick = null;
      console.warn('[mobile] PDF not available for', data.id, data.title);
    }
  }

  overlay.hidden = false;
  document.body.classList.add('m-no-scroll');
}


    function closeDetail(){
      overlay.hidden = true;
      document.body.classList.remove('m-no-scroll');
    }

    // Delegovaný click PŘÍMO na #m-list (ještě jistější než na document)
    list.addEventListener('click', function(e){
      const a = e.target.closest('.js-open-detail');
      if (!a || !list.contains(a)) return;
      const li = a.closest('.m-simple-item');
      if (!li) return;
      e.preventDefault();
      openDetail(li);
    });

    if (btnX) btnX.addEventListener('click', closeDetail);
    if (pdfClose){
      pdfClose.addEventListener('click', function(){
        pdfOvl.hidden = true;
        pdfFrame.src = '';
        document.body.classList.remove('m-no-scroll');
      });
    }

    console.log('[mobile] detail ready');
  }

  // Defer = script se spouští po parsování DOMu, ale přidáme i fallback
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){
      console.log('[mobile] DOMContentLoaded');
      initFilter();
      initDetail();
    });
  } else {
    console.log('[mobile] DOM already ready');
    initFilter();
    initDetail();
  }
})();
