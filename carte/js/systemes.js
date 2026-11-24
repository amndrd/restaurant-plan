// How the map shows the state of each table. Four prototypes, switchable in the settings:
//   A  Halo au sol      a soft coloured footprint under the table and its chairs
//   B  Plateau          only the table top takes the colour
//   C  Places occupées  each occupied seat takes the colour, a thin outline gives the state
//   D  Minuteur         a ring over the table fills with the time spent in the current state
// Plus, in every prototype, the alerts (a table waiting too long) pulse in red.
import * as THREE from 'three';
import { ETATS, ALERTE } from './service.js';

const CIBLES = { reservee: 30, installee: 8, commandee: 22, servie: 40, addition: 10, debarrasser: 6 };

function rondRect(w, d, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -d / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + d - r); s.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
  s.lineTo(x + r, y + d); s.quadraticCurveTo(x, y + d, x, y + d - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  return s;
}

const mel = (hex, blanc) => new THREE.Color(hex).lerp(new THREE.Color(0xffffff), blanc);

export class Systemes {
  constructor(scene, groupes, calque) {
    this.groupes = groupes; this.variante = 'A';
    this.racine = new THREE.Group(); this.racine.name = 'systemes'; scene.add(this.racine);
    this.cache = new Map();
    for (const g of groupes.values()) {
      const b = g.boite, pad = 0.16;
      const w = b.max.x - b.min.x + 2 * pad, d = b.max.z - b.min.z + 2 * pad, r = Math.min(0.55, w / 2 - 0.01, d / 2 - 0.01);
      const forme = rondRect(w, d, r);
      g.centre = new THREE.Vector3((b.min.x + b.max.x) / 2, 0, (b.min.z + b.max.z) / 2);
      const halo = new THREE.Mesh(new THREE.ShapeGeometry(forme, 10).rotateX(-Math.PI / 2),
        new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, depthWrite: false }));
      halo.position.set(g.centre.x, 0.004, g.centre.z); halo.receiveShadow = true; halo.renderOrder = -1;
      const pts = forme.getSpacedPoints(80).map(p => new THREE.Vector3(p.x, 0, -p.y));
      const contour = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.9 }));
      contour.position.set(g.centre.x, 0.008, g.centre.z);
      const anneau = new THREE.Mesh(new THREE.ShapeGeometry(this._anneau(forme, w, d, r), 10).rotateX(-Math.PI / 2),
        new THREE.MeshBasicMaterial({ color: ALERTE, transparent: true, opacity: 0.9, depthWrite: false }));
      anneau.position.set(g.centre.x, 0.006, g.centre.z);
      const pick = new THREE.Mesh(new THREE.BoxGeometry(w, 1.3, d), new THREE.MeshBasicMaterial({ visible: false }));
      pick.position.set(g.centre.x, 0.65, g.centre.z); pick.userData.table = g.id;
      this.racine.add(halo, contour, anneau, pick);
      Object.assign(g, { halo, contour, anneau, pick });
      const el = document.createElement('div');
      el.className = 'badge minuteur';
      el.innerHTML = `<svg viewBox="0 0 44 44"><circle cx="22" cy="22" r="21" fill="#fff"/>
        <circle cx="22" cy="22" r="17" fill="none" stroke="#ecebe8" stroke-width="4"/>
        <circle class="arc" cx="22" cy="22" r="17" fill="none" stroke-width="4" stroke-linecap="round"
          stroke-dasharray="0 107" transform="rotate(-90 22 22)"/></svg><b></b>`;
      el.hidden = true; calque.appendChild(el); g.badge = el;
    }
    this.picks = [...groupes.values()].map(g => g.pick);
  }

  _anneau(forme, w, d, r) {   // a 6 cm band just outside the footprint, for the alerts
    const s = rondRect(w + 0.12, d + 0.12, r + 0.06);
    s.holes.push(new THREE.Path(rondRect(w, d, r).getPoints(12).reverse()));
    return s;
  }

  regler(v) { this.variante = v; this.change = true; }

  _teinter(o, couleur, force = 1) {
    const base = o.userData.matBase;
    if (!base) return;
    if (couleur === null) { if (o.material !== base) o.material = base; return; }
    const cle = base.uuid + couleur + force;
    let m = this.cache.get(cle);
    if (!m) {
      m = base.clone();
      if (m.colorWrite === false) { m = new THREE.MeshStandardMaterial({ roughness: 0.8 }); }
      m.color = mel(couleur, 1 - force);
      this.cache.set(cle, m);
    }
    if (o.material !== m) o.material = m;
  }

  maj(service, cam, canvas, now, style) {
    const v = this.variante, pouls = 0.55 + 0.45 * Math.sin(now / 260);
    const traverse = style === 'fil-de-fer' || style === 'transparent';   // see-through styles: the colours too
    const largeur = canvas.clientWidth, hauteur = canvas.clientHeight, p = new THREE.Vector3();
    for (const g of this.groupes.values()) {
      const t = service.tables.find(x => x.id === g.id);
      const etat = ETATS[t.etat], occupe = !['libre', 'reservee', 'debarrasser'].includes(t.etat);
      // A: the footprint
      g.halo.visible = v === 'A' || (v === 'D' && t.etat !== 'libre');
      g.halo.material.depthTest = g.anneau.material.depthTest = !traverse;
      if (g.halo.visible) {
        const c = v === 'D' ? 0xe7e6e2 : t.etat === 'libre' ? 0xe4e3df : etat.couleur;
        g.halo.material.color.set(v === 'A' ? mel(c, 0.1) : c);
        g.halo.material.opacity = t.etat === 'libre' ? 0.55 : 0.92;
      }
      // C: the outline
      g.contour.visible = v === 'C' && t.etat !== 'libre';
      if (g.contour.visible) g.contour.material.color.set(etat.couleur);
      // alerts, every prototype
      g.anneau.visible = v !== '0' && t.alerte;
      if (g.anneau.visible) g.anneau.material.opacity = 0.35 + 0.6 * pouls;
      // B: the table tops
      const modele = style === 'transparent' || style === 'fil-de-fer' ? 'entier' : 'fantome';
      for (const o of g.plateaux[modele]) this._teinter(o, v === 'B' && t.etat !== 'libre' ? (t.alerte ? ALERTE : etat.couleur) : null);
      // C: the seats, as many as the guests (drums: the armchairs, then the banquette)
      const sieges = g.sieges[modele];
      sieges.forEach((s, k) => s.forEach(o => this._teinter(o, v === 'C' && occupe && k < t.invites ? etat.couleur : null, 0.85)));
      for (const o of g.banquette[modele]) this._teinter(o, v === 'C' && occupe && t.invites > sieges.length ? etat.couleur : null, 0.7);
      // D: the timer over the table
      const montrer = v === 'D' && t.etat !== 'libre';
      g.badge.hidden = !montrer;
      if (montrer) {
        p.set(g.centre.x, g.hauteur + 0.55, g.centre.z).project(cam);
        g.badge.style.transform = `translate(${(p.x + 1) / 2 * largeur - 22}px, ${(1 - p.y) / 2 * hauteur - 22}px)`;
        const duree = t.etat === 'reservee' && t.resa ? Math.max(0, t.resa.heure - service.t) : service.t - t.depuis;
        const k = Math.min(1, (t.etat === 'reservee' ? 1 - duree / 30 : duree / CIBLES[t.etat]));
        const arc = g.badge.querySelector('.arc');
        arc.setAttribute('stroke', t.alerte ? ALERTE : etat.couleur);
        arc.setAttribute('stroke-dasharray', `${(k * 106.8).toFixed(1)} 107`);
        g.badge.querySelector('b').textContent = `${Math.round(duree)}′`;
        g.badge.classList.toggle('alerte', t.alerte);
      }
    }
  }
}
