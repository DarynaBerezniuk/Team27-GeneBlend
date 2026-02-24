/**
 * Updated education.js for Django Integration
 * * Changes: 
 * 1. Removed hardcoded CARDS_DATA array.
 * 2. Added fetch API logic to load data from the database via Django views.
 * 3. Integrated initial rendering into the data-loading promise chain.
 */

// Helper functions for data structure (retained from original )
const t=(c)=>({type:"text",content:c});
const h=(c)=>({type:"head",content:c});
const l=(...items)=>({type:"list",items});
const nl=(...items)=>({type:"numlist",items});
const n=(c)=>({type:"note",content:c});

// Initialize empty data array
let CARDS_DATA = [];

/**
 * Fetches card data from the Django API view.
 */
async function loadEducationData() {
    try {
        // This URL must match the path defined in your calculator/urls.py
        const response = await fetch('/api/education-data/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        CARDS_DATA = await response.json();
        
        // Once data is loaded, perform the initial render [cite: 1]
        renderCards(""); 
        
    } catch (error) {
        console.error("Failed to load education cards:", error);
        const grid = document.getElementById('card-grid');
        if (grid) {
            grid.innerHTML = `<p style="color:red; padding:20px;">Помилка завантаження даних. Будь ласка, спробуйте пізніше.</p>`;
        }
    }
}

// Start loading process immediately
loadEducationData();

/**
 * The remaining rendering logic stays mostly the same as your original file,
 * but now works with the dynamic CARDS_DATA variable.
 */

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
            
            // Image/SVG handling from original logic 
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

// Utility to highlight search matches 
function highlightText(text, query) {
    if (!query) return text;
    const re = new RegExp(`(${query})`, 'gi');
    return text.replace(re, '<span class="match">$1</span>');
}

// Modal handling logic 
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

// Section rendering logic (handles text, head, list, note types) 
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

// Search and Overlay handlers 
function handleSearch(val) { renderCards(val); }
function closeModal() { document.getElementById('overlay').classList.remove('open'); }
function handleOverlayClick(e) { if(e.target === document.getElementById('overlay')) closeModal(); }
