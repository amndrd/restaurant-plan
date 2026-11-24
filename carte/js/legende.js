// The legend of the states, under the map. Three designs are proposed (?legende=L1|L2|L3):
//   L1  Compteurs  each state with its number of tables; hover or click one to outline those tables on the map
//   L2  Jauge      the tables of the room as one proportional bar, each state with its count, the alerts apart
//   L3  Frise      the evening from 18:30 to 23:30: the guests in each state, the time now, the bookings to come
import { ETATS, ALERTE, hhmm } from './service.js';

const AVEC_CLIENTS = ['installee', 'commandee', 'servie', 'addition'];
const DEBUT = 18 * 60 + 30, FIN = 23 * 60 + 30;

export class Legende {
  constructor(design, service, systemes) {
    this.d = design; this.s = service; this.sys = systemes; this.fixe = null;
    this.el = document.getElementById('legende');
    this.el.className = `legende ${design.toLowerCase()}`;
    if (design === 'L1') this._L1();
    if (design === 'L3') this._L3();
    this.maj();
  }

  _compte() {
    const c = Object.fromEntries(Object.keys(ETATS).map(e => [e, this.s.tables.filter(t => t.etat === e).length]));
    c.alerte = this.s.tables.filter(t => t.alerte).length;
    return c;
  }

  // ---- L1
  _L1() {
    this.el.innerHTML = [...Object.entries(ETATS), ['alerte', { nom: 'Alerte', couleur: ALERTE }]].map(([k, e]) =>
      `<button class="l1-c" data-e="${k}"><i style="background:${e.couleur}"></i><span>${e.nom.split(',')[0]}</span><b></b></button>`).join('');
    const montrer = e => { this.sys.surligne = e ?? this.fixe; this.el.querySelectorAll('.l1-c').forEach(b =>
      b.classList.toggle('on', b.dataset.e === (e ?? this.fixe))); };
    this.el.querySelectorAll('.l1-c').forEach(b => {
      b.onmouseenter = () => montrer(b.dataset.e);
      b.onmouseleave = () => montrer(null);
      b.onclick = () => { this.fixe = this.fixe === b.dataset.e ? null : b.dataset.e; montrer(null); };
    });
    this.surligner = e => { this.fixe = e; montrer(null); };
  }

  // ---- L3
  _L3() {
    this.el.innerHTML = `<div class="l3-leg">${AVEC_CLIENTS.map(k => `<span><i style="background:${ETATS[k].couleur}"></i>${ETATS[k].nom.split(',')[0]}</span>`).join('')}
      <span><i class="l3-resa"></i>Réservation</span><span><i style="background:${ALERTE}"></i>Alerte</span></div>
      <svg class="l3-svg" viewBox="0 0 600 84" preserveAspectRatio="none"></svg>`;
  }

  maj() {
    const c = this._compte();
    if (this.d === 'L1') {
      this.el.querySelectorAll('.l1-c').forEach(b => { const n = c[b.dataset.e]; b.querySelector('b').textContent = n;
        b.classList.toggle('vide', !n); });
    } else if (this.d === 'L2') {
      const presents = Object.entries(ETATS).filter(([k]) => c[k]);
      this.el.innerHTML = `<div class="l2-g"><div class="l2-barre">${presents.map(([k, e]) =>
        `<span style="flex:${c[k]};background:${e.couleur}"><b>${c[k]}</b></span>`).join('')}</div>
        <div class="l2-noms">${presents.map(([k, e]) => `<span style="flex:${c[k]}">${e.nom.split(',')[0]}</span>`).join('')}</div></div>
        <div class="l2-a ${c.alerte ? 'on' : ''}"><i></i><b>${c.alerte}</b> alerte${c.alerte > 1 ? 's' : ''}</div>`;
    } else {
      this._frise();
    }
  }

  _frise() {
    const W = 600, H = 84, haut = 8, bas = 16, h = H - haut - bas;
    const x = m => (m - DEBUT) / (FIN - DEBUT) * W;
    const places = this.s.tables.reduce((s, t) => s + t.places, 0);
    const y = v => H - bas - v / places * h;
    const pts = this.s.histoire.filter(p => p.t >= DEBUT);
    let svg = '';
    for (let k = 19; k <= 23; k++) {
      svg += `<line x1="${x(k * 60)}" x2="${x(k * 60)}" y1="${haut}" y2="${H - bas}" class="l3-heure"/>`;
      if (Math.abs(x(k * 60) - x(this.s.t)) > 30) svg += `<text x="${x(k * 60)}" y="${H - 3}" class="l3-txt">${k}h</text>`;
    }
    if (pts.length > 1) {
      let dessous = pts.map(() => 0);
      for (const e of AVEC_CLIENTS) {
        const dessus = pts.map((p, i) => dessous[i] + p[e]);
        const d = pts.map((p, i) => `${x(p.t).toFixed(1)},${y(dessus[i]).toFixed(1)}`).join(' L') + ' L' +
          pts.map((p, i) => `${x(p.t).toFixed(1)},${y(dessous[i]).toFixed(1)}`).reverse().join(' L');
        svg += `<path d="M${d} Z" fill="${ETATS[e].couleur}" opacity=".9"/>`;
        dessous = dessus;
      }
    }
    for (const r of this.s.resas.filter(r => !r.arrivee)) {
      svg += `<path d="M${x(r.heure) - 4},${haut - 7} L${x(r.heure) + 4},${haut - 7} L${x(r.heure)},${haut - 1} Z" fill="${ETATS.reservee.couleur}"><title>${hhmm(r.heure)} · ${r.nom}, ${r.couverts} pers.</title></path>`;
    }
    const n = x(this.s.t);
    svg += `<line x1="${n}" x2="${n}" y1="${haut - 2}" y2="${H - bas}" class="l3-now"/>
      <rect x="${n - 19}" y="${H - bas + 1}" width="38" height="14" rx="7" class="l3-pill"/>
      <text x="${n}" y="${H - 4.5}" class="l3-txt l3-tnow">${hhmm(this.s.t)}</text>`;
    this.el.querySelector('.l3-svg').innerHTML = svg;
  }
}
