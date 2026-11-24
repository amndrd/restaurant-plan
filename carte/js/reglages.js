// The settings of the map: three settings, chosen at step 6 with their options (the first one is the default), in
// the command bar chosen at step 7 (R3): at the bottom right, with the clock; each menu opens upwards and says what
// each option does. Light by default, dark with the theme of the interface.
export const REGLAGES = {
  style: { titre: 'Style', options: [
    ['fantome', 'Fantôme', 'Les murs pleins jusqu’à 1,20 m, le haut en transparence'],
    ['transparent', 'Transparent', 'Tout le modèle en verre dépoli'],
    ['fil-de-fer', 'Fil de fer', 'Seulement les arêtes, comme un dessin'],
  ] },
  systeme: { titre: 'Tables', options: [
    ['C', 'Places', 'Chaque place occupée prend la couleur de l’état'],
    ['B', 'Plateau', 'Le plateau de la table prend la couleur'],
    ['D', 'Minuteur', 'Le temps passé dans l’état, au-dessus de la table'],
  ] },
  numeros: { titre: 'Numéros', options: [
    ['3', 'Étiquette', 'Le numéro au-dessus de chaque table'],
    ['5', 'Zones', 'Une lettre de zone et un numéro : T1, R2, S3…'],
    ['0', 'Aucun', 'La carte sans numéros'],
  ] },
};

const I = (d) => `<svg viewBox="0 0 20 20" aria-hidden="true">${d}</svg>`;
export const ICONES = {
  fantome: I('<path d="M4 12.5 10 15.5l6-3V9.5l-6 3-6-3z" fill="currentColor" opacity=".22"/><path d="M4 9.5 10 12.5l6-3M4 9.5v3l6 3 6-3v-3M10 12.5v3" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M4 9.5V6.5l6-3 6 3v3M10 3.5v3M4 6.5l6 3 6-3" fill="none" stroke="currentColor" stroke-width="1.1" stroke-dasharray="1.6 1.6" opacity=".7"/>'),
  transparent: I('<rect x="3" y="3" width="10" height="10" rx="2" fill="currentColor" opacity=".22" stroke="currentColor" stroke-width="1.3"/><rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor" opacity=".22" stroke="currentColor" stroke-width="1.3"/>'),
  'fil-de-fer': I('<path d="M4 6.5 10 9.5l6-3M10 9.5v7M4 6.5 10 3.5l6 3v7l-6 3-6-3z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M4 13.5 10 10.5l6 3M10 3.5v7" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="1.4 1.4" opacity=".6"/>'),
  C: I('<rect x="6.5" y="6.5" width="7" height="7" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="10" cy="3.6" r="1.8" fill="currentColor"/><circle cx="16.4" cy="10" r="1.8" fill="currentColor"/><circle cx="10" cy="16.4" r="1.8" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="3.6" cy="10" r="1.8" fill="none" stroke="currentColor" stroke-width="1.2"/>'),
  B: I('<rect x="4" y="4" width="12" height="12" rx="2" fill="currentColor" opacity=".9"/>'),
  D: I('<circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="2" opacity=".22"/><path d="M10 3.5a6.5 6.5 0 0 1 6.2 8.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
  3: I('<rect x="5" y="3" width="10" height="7" rx="3.5" fill="currentColor"/><path d="M10 10v6" stroke="currentColor" stroke-width="1.3"/><circle cx="10" cy="16.5" r="1.2" fill="currentColor"/>'),
  5: I('<rect x="3" y="6" width="14" height="8" rx="2" fill="none" stroke="currentColor" stroke-width="1.3"/><rect x="3" y="6" width="6" height="8" rx="2" fill="currentColor"/>'),
  0: I('<circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M5.5 14.5l9-9" stroke="currentColor" stroke-width="1.3"/>'),
};
const COCHE = '<svg viewBox="0 0 12 12"><path d="m2.5 6.2 2.3 2.3 4.7-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

export class Reglages {
  // valeurs: the current values; changer(cle, valeur) applies one
  constructor(valeurs, changer) {
    this.v = valeurs; this.changer = changer; this.ouvert = null;
    const el = this.el = document.createElement('div'); el.className = 'r3';
    el.innerHTML = Object.keys(REGLAGES).map(cle => `<div class="r3-menu" data-cle="${cle}">
      <button class="r3-b" aria-haspopup="true"><span class="r3-i"></span><span class="r3-txt"><em>${REGLAGES[cle].titre}</em><b></b></span>
      <svg class="r3-fl" viewBox="0 0 10 10"><path d="m2.5 6 2.5-2.5L7.5 6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg></button>
      <div class="r3-pop" hidden>${REGLAGES[cle].options.map(([v, nom, aide]) => `<button data-v="${v}">
        <span class="r3-oi">${ICONES[v]}</span><span class="r3-ot"><b>${nom}</b><span>${aide}</span></span><i class="r3-coche">${COCHE}</i></button>`).join('')}
      </div></div>`).join('') + '<span class="r3-sep"></span>';
    el.appendChild(document.querySelector('.horloge'));
    document.body.appendChild(el);
    el.querySelectorAll('.r3-menu').forEach(m => {
      m.querySelector('.r3-b').onclick = () => this.ouvrir(this.ouvert === m.dataset.cle ? null : m.dataset.cle);
      m.querySelector('.r3-pop').addEventListener('click', e => { const b = e.target.closest('button');
        if (b) { this.choisir(m.dataset.cle, b.dataset.v); this.ouvrir(null); } });
    });
    document.addEventListener('pointerdown', e => { if (this.ouvert && !e.target.closest('.r3-menu')) this.ouvrir(null); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') this.ouvrir(null); });
    this.maj();
  }

  choisir(cle, valeur) { this.v[cle] = valeur; this.changer(cle, valeur); this.maj(); }

  ouvrir(cle) {
    this.ouvert = cle;
    this.el.querySelectorAll('.r3-menu').forEach(m => {
      m.querySelector('.r3-pop').hidden = m.dataset.cle !== cle; m.classList.toggle('on', m.dataset.cle === cle); });
  }

  maj() {
    this.el.querySelectorAll('.r3-menu').forEach(m => {
      const cle = m.dataset.cle, o = REGLAGES[cle].options.find(x => x[0] === this.v[cle]);
      m.querySelector('.r3-i').innerHTML = ICONES[o[0]]; m.querySelector('.r3-txt b').textContent = o[1];
      m.querySelectorAll('.r3-pop button').forEach(b => b.classList.toggle('on', b.dataset.v === this.v[cle]));
    });
  }
}
