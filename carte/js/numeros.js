// Table numbers (chosen at step 6): the label by default, the zones, or none.
//   3  Étiquette   a black pill floating over the table on a hairline, a map callout
//   5  Zones       a zone letter and a number: T tambours, R rangée, S salle, F façade, B banquette près du bar
// The bars have their own label.
import * as THREE from 'three';

const COURT = { 0: 'Bar', 100: 'Omakase', 101: 'Tablette' };     // the bars' labels (1st floor: 100, 101)

export class Numeros {
  constructor(groupes, calque) {
    this.variante = '3'; this.l = { 3: [], 5: [] };
    const parZone = {};
    for (const g of [...groupes.values()].sort((a, b) => a.id - b.id)) {
      const bar = g.type === 'bar';
      const z = g.zone || 'S';
      if (!bar) { parZone[z] = (parZone[z] || 0) + 1; g.code = `${z}${parZone[z]}`; }
      const e3 = document.createElement('div'); e3.className = 'badge etiquette';
      const nom = COURT[g.id] ?? 'Bar';
      e3.innerHTML = `<div class="pastille">${bar ? nom : g.id}</div><div class="fil"></div>`;
      const e5 = document.createElement('div'); e5.className = 'badge';
      e5.innerHTML = bar ? `<div class="zone"><em>${nom}</em></div>` : `<div class="zone"><em>${z}</em><span>${g.code.slice(1)}</span></div>`;
      for (const [k, e] of [[3, e3], [5, e5]]) { e.hidden = true; calque.appendChild(e); this.l[k].push({ e, g }); }
    }
  }

  regler(v) {
    this.variante = v;
    for (const [k, l] of Object.entries(this.l)) l.forEach(({ e }) => { e.hidden = k !== v || this.actif === false; });
  }

  // only the floor on show carries its numbers
  montrer(oui) { this.actif = oui; this.regler(this.variante); }

  maj(cam, canvas) {
    if (this.variante === '0' || this.actif === false) return;
    const W = canvas.clientWidth, H = canvas.clientHeight, p = new THREE.Vector3(), q = new THREE.Vector3();
    for (const { e, g } of this.l[this.variante]) {
      p.set(g.centre.x, g.plateau.y, g.centre.z).project(cam);
      const x0 = (p.x + 1) / 2 * W, y0 = (1 - p.y) / 2 * H;
      if (this.variante === '3') {
        q.set(g.centre.x, g.plateau.y + 0.95, g.centre.z).project(cam);
        const y1 = (1 - q.y) / 2 * H;
        e.querySelector('.fil').style.height = `${Math.max(0, y0 - y1 - 13)}px`;
        e.style.transform = `translate(${x0}px, ${y1}px) translate(-50%, -13px)`;
      } else {
        e.style.transform = `translate(${x0}px, ${y0}px) translate(-50%, -50%)`;
      }
    }
  }
}
