// The legend of the states (26/11, the user's model): a dark card at the bottom left, always on show, the six coloured
// states in two columns, a square of colour for each (a triangle for the bookings). Hover a state to outline its
// tables on the map; a click keeps it outlined, a second click releases it.
import { ETATS, ALERTE } from './service.js';

// in the order of the model, row by row
const ORDRE = [
  ['installee', 'Installée'], ['commandee', 'En attente des plats'],
  ['servie', 'Servie'], ['addition', 'Addition'],
  ['reservee', 'Réservation'], ['alerte', 'Alerte'],
];

export class Legende {
  constructor(service, systemes) {
    this.s = service; this.sys = systemes; this.fixe = null;
    this.el = document.getElementById('legende');
    this.el.innerHTML = ORDRE.map(([k, nom]) => {
      const c = k === 'alerte' ? ALERTE : ETATS[k].couleur;
      const signe = k === 'reservee'
        ? `<svg class="tri" viewBox="0 0 12 12" aria-hidden="true"><path d="M1.6 3h8.8L6 9.6z" fill="${c}"/></svg>`
        : `<i style="background:${c}"></i>`;
      return `<button class="l-e" data-e="${k}">${signe}<span>${nom}</span></button>`;
    }).join('');
    const montrer = e => { this.sys.surligne = e ?? this.fixe; this.el.querySelectorAll('.l-e').forEach(b =>
      b.classList.toggle('on', b.dataset.e === this.fixe)); };
    this.el.querySelectorAll('.l-e').forEach(b => {
      b.onmouseenter = () => montrer(b.dataset.e);
      b.onmouseleave = () => montrer(null);
      b.onclick = () => { this.fixe = this.fixe === b.dataset.e ? null : b.dataset.e; montrer(null); };
    });
    this.surligner = e => { this.fixe = e; montrer(null); };
  }

  // the floor on show: its service and its tables
  lier(service, systemes) {
    if (this.sys && this.sys !== systemes) this.sys.surligne = null;
    this.s = service; this.sys = systemes; this.sys.surligne = this.fixe;
  }

  ouvrir() {}          // always open now (kept for the address settings of the captures)
  maj() {}
}
