// The legend of the states (chosen at step 7: the counters, L1), folded away behind the "Légende" button at the bottom
// left; it opens upwards like the menus of the command bar. Each state with its number of tables; hover or click one
// to outline those tables on the map.
import { ETATS, ALERTE } from './service.js';

export class Legende {
  constructor(service, systemes) {
    this.s = service; this.sys = systemes; this.fixe = null;
    this.el = document.getElementById('legende');
    this.bouton = document.getElementById('legende-b');
    this.el.innerHTML = '<div class="l-titre">États des tables</div>' +
      [...Object.entries(ETATS), ['alerte', { nom: 'Alerte', couleur: ALERTE }]].map(([k, e]) =>
      `<button class="l1-c" data-e="${k}"><i style="background:${e.couleur}"></i><span>${e.nom.split(',')[0]}</span><b></b></button>`).join('') +
      '<div class="l-aide">Touchez un état pour repérer ses tables sur la carte.</div>';
    // hovering previews the tables of a state on the map; only a click selects the state (the black button)
    const montrer = e => { this.sys.surligne = e ?? this.fixe; this.el.querySelectorAll('.l1-c').forEach(b =>
      b.classList.toggle('on', b.dataset.e === this.fixe)); };
    this.el.querySelectorAll('.l1-c').forEach(b => {
      b.onmouseenter = () => montrer(b.dataset.e);
      b.onmouseleave = () => montrer(null);
      b.onclick = () => { this.fixe = this.fixe === b.dataset.e ? null : b.dataset.e; montrer(null); };
    });
    this.surligner = e => { this.fixe = e; montrer(null); };
    this.bouton.onclick = () => this.ouvrir(this.el.classList.contains('ferme'));
    this.maj();
  }

  ouvrir(oui) {
    this.el.classList.toggle('ferme', !oui);
    this.bouton.classList.toggle('on', oui);
    this.bouton.setAttribute('aria-expanded', String(oui));
    if (!oui) this.surligner(null);       // folding the legend also clears the outlined tables
  }

  maj() {
    const c = Object.fromEntries(Object.keys(ETATS).map(e => [e, this.s.tables.filter(t => t.etat === e).length]));
    c.alerte = this.s.tables.filter(t => t.alerte).length;
    this.el.querySelectorAll('.l1-c').forEach(b => { const n = c[b.dataset.e]; b.querySelector('b').textContent = n;
      b.classList.toggle('vide', !n); });
  }
}
