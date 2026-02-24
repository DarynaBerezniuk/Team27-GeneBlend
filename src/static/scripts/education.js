const t=(c)=>({type:"text",content:c});
const h=(c)=>({type:"head",content:c});
const l=(...items)=>({type:"list",items});
const nl=(...items)=>({type:"numlist",items});
const n=(c)=>({type:"note",content:c});

let CARDS_DATA = [];

async function loadEducationData() {
    try {
        const response = await fetch('/api/education-data/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        CARDS_DATA = await response.json();
        
        renderCards(""); 
        
    } catch (error) {
        console.error("Failed to load education cards:", error);
        const grid = document.getElementById('card-grid');
        if (grid) {
            grid.innerHTML = `<p style="color:red; padding:20px;">Помилка завантаження даних. Будь ласка, спробуйте пізніше.</p>`;
        }
    }
}

loadEducationData();

function renderCards(query) {
    const grid = document.getElementById('card-grid');
    if (!grid) return;
    grid.innerHTML = "";

    const q = query.toLowerCase().trim();
    const rows = [...new Set(CARDS_DATA.map(c => c.row))].sort((a, b) => a - b);

    rows.forEach(r => {
        const rowCards = CARDS_DATA.filter(c => c.row === r).sort((a, b) => a.col - b.col);
        const rowEl = document.createElement('div');
        rowEl.className = 'grid-row';

        rowCards.forEach(card => {
            const isDim = q && !card.title.toLowerCase().includes(q) && 
                          !card.text.toLowerCase().includes(q) && 
                          !card.tags.some(t => t.toLowerCase().includes(q));

            const el = document.createElement('div');
            el.className = `card${isDim ? ' dim' : ''}`;
            
            const imgHtml = card.image ? `<div class="card-img-mini">${card.image}</div>` : '';
            
            el.innerHTML = `
                ${imgHtml}
                <div class="card-title">${card.title}</div>
                <div class="card-text">${highlightText(card.text, q)}</div>
                <div class="card-tags">
                    ${card.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
                </div>
            `;

            if (!isDim) {
                el.addEventListener('click', () => openCardModal(card));
            }
            rowEl.appendChild(el);
        });
        grid.appendChild(rowEl);
    });
}

function highlightText(text, query) {
    if (!query) return text;
    const re = new RegExp(`(${query})`, 'gi');
    return text.replace(re, '<span class="match">$1</span>');
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

function renderSections(sections) {
    return sections.map(s => {
        if (s.type === 'text') return `<p>${s.content}</p>`;
        if (s.type === 'head') return `<h4 class="sec-head">${s.content}</h4>`;
        if (s.type === 'note') return `<div class="note">${s.content}</div>`;
        if (s.type === 'list') return `<ul>${s.items.map(i => `<li>${i}</li>`).join('')}</ul>`;
        if (s.type === 'numlist') return `<ol>${s.items.map(i => `<li>${i}</li>`).join('')}</ol>`;
        return '';
    }).join('');
}

function handleSearch(val) { renderCards(val); }
function closeModal() { document.getElementById('overlay').classList.remove('open'); }
function handleOverlayClick(e) { if(e.target === document.getElementById('overlay')) closeModal(); }
