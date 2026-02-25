const t = (c) => ({ type: "text", content: c });
const h = (c) => ({ type: "head", content: c });
const l = (...items) => ({ type: "list", items });
const nl = (...items) => ({ type: "numlist", items });
const n = (c) => ({ type: "note", content: c });

let CARDS_DATA = [];
let KW_KEYS = [];

async function loadEducationData() {
    try {
        const response = await fetch('/api/education-data/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        CARDS_DATA = await response.json();
        
        const allTags = CARDS_DATA.flatMap(c => c.tags || []);
        KW_KEYS = [...new Set(allTags)];
        
        renderCards(""); 
        
    } catch (error) {
        console.error("Failed to load education cards:", error);
        const grid = document.getElementById('card-grid');
        if (grid) {
            grid.innerHTML = `<p style="color:red; padding:20px; font-weight:600;">Помилка завантаження даних. Будь ласка, спробуйте пізніше.</p>`;
        }
    }
}

loadEducationData();

function escRx(s) { 
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); 
}

function highlightText(text, query) {
    if (!query) return text;
    const lq = query.toLowerCase();
    const targets = KW_KEYS.filter(k => k.toLowerCase().includes(lq) || lq.includes(k.toLowerCase()));
    
    if (!targets.length) return text;
    
    let parts = [{ s: text, raw: true }];
    targets.forEach(kw => {
        const re = new RegExp(escRx(kw), 'gi');
        parts = parts.flatMap(part => {
            if (!part.raw) return [part];
            const segs = []; 
            let last = 0, m; 
            re.lastIndex = 0;
            
            while ((m = re.exec(part.s)) !== null) {
                if (m.index > last) segs.push({ s: part.s.slice(last, m.index), raw: true });
                segs.push({ s: m[0], raw: false });
                last = m.index + m[0].length;
            }
            if (last < part.s.length) segs.push({ s: part.s.slice(last), raw: true });
            
            return segs.length ? segs : [part];
        });
    });
    
    return parts.map(p => p.raw ? p.s : `<span class="kw">${p.s}</span>`).join('');
}

function renderCards(query) {
    const grid = document.getElementById('card-grid');
    if (!grid) return;
    grid.innerHTML = "";

    const lq = query ? query.toLowerCase().trim() : '';

    const ROWS_MAP = {};
    CARDS_DATA.forEach(card => {
        if (!ROWS_MAP[card.row]) ROWS_MAP[card.row] = [];
        ROWS_MAP[card.row].push(card);
    });
    
    const ROWS_SORTED = Object.keys(ROWS_MAP)
        .sort((a, b) => +a - +b)
        .map(k => ROWS_MAP[k]);

    ROWS_SORTED.forEach(row => {
        row.sort((a, b) => (a.col || 1) - (b.col || 1));
        
        const rowEl = document.createElement('div');
        rowEl.className = 'grid-row';

        row.forEach(card => {
            const tags = card.tags || [];
            
            const matchedTags = lq
                ? tags.filter(tag => tag.toLowerCase().includes(lq) || lq.includes(tag.toLowerCase()))
                : [];
                
            const isMatch = matchedTags.length > 0;
            const isDim = lq && !isMatch;

            const el = document.createElement('div');
            let cls = 'card' + (card.col === 2 ? ' col-2' : '');
            if (lq) cls += isMatch ? ' match' : ' dim';
            el.className = cls;

            const textHtml = highlightText(card.text, query);
            
            const tagsHtml = tags.length
                ? '<div class="card-tags">' +
                  tags.map(tag => {
                      const isTagMatch = matchedTags.some(m => m.toLowerCase() === tag.toLowerCase());
                      return `<span class="tag${isTagMatch ? ' tag-match' : ''}">#${tag}</span>`;
                  }).join('') +
                  '</div>'
                : '';

            el.innerHTML = textHtml + tagsHtml;

            if (!isDim) {
                el.addEventListener('click', () => openCardModal(card));
            }
            rowEl.appendChild(el);
        });
        grid.appendChild(rowEl);
    });
}

function renderSections(sections) {
    if (!sections) return '';
    return sections.map(sec => {
        if (sec.type === 'text') return `<p>${sec.content}</p>`;
        if (sec.type === 'head') return `<div class="sec-head">${sec.content}</div>`;
        if (sec.type === 'note') return `<div class="modal-note">${sec.content}</div>`;
        if (sec.type === 'list') return sec.items.map(it => `<div class="li"><span class="li-dot">·</span><span>${it}</span></div>`).join('');
        if (sec.type === 'numlist') return sec.items.map((it, i) => `<div class="li"><span class="li-num">${i + 1}.</span><span>${it}</span></div>`).join('');
        return '';
    }).join('');
}

function openCardModal(card) {
    document.getElementById('modal-title').textContent = card.title;
    document.getElementById('modal-body').innerHTML = renderSections(card.sections);
    
    const imgWrap = document.getElementById('modal-img-wrap');
    const svgDiv = document.getElementById('modal-img-svg');
    
    if (card.image) {
        svgDiv.innerHTML = card.image;
        imgWrap.style.display = 'flex';
    } else {
        imgWrap.style.display = 'none';
        svgDiv.innerHTML = '';
    }
    
    document.getElementById('overlay').classList.add('open');
}

// Обробники подій
function handleSearch(val) { 
    renderCards(val.trim()); 
}

function closeModal() { 
    document.getElementById('overlay').classList.remove('open'); 
}

function handleOverlayClick(e) { 
    if (e.target === document.getElementById('overlay')) closeModal(); 
}

document.addEventListener('keydown', e => { 
    if (e.key === 'Escape') closeModal(); 
});

window.handleSearch = handleSearch;
window.closeModal = closeModal;
window.handleOverlayClick = handleOverlayClick;
