// Table numbers: five design prototypes, none shown by default (the numbering exists in the data).
//   1  Peints au sol         a numeral painted on the floor in the aisle, like venue signage (Futura)
//   2  Plaque sur la table   a small engraved disc set on the table top, like a brass table marker (Didot)
//   3  Étiquette             a black pill floating over the table on a hairline, a map callout
//   4  Repère d'architecte   a hairline circle with the numeral and a short leader, the language of the plans
//   5  Zones                 a zone letter and a number (T tambours, R rangée, S salle, F façade, D debout)
import * as THREE from 'three';

const ZONES = { tambour: 'T', table: null, 'table haute': 'F', 'mange-debout': 'D' };
// where the floor numbers (1, 4) go, placed by hand in the free aisle next to each table (plan px of floor1.png)
const AU_SOL = { 1: [571, 1003], 2: [571, 1306], 3: [571, 1712], 4: [571, 2015], 5: [711, 1176], 6: [858, 1745],
  7: [892, 1374], 8: [892, 1612], 9: [1043, 1885], 10: [1186, 964], 11: [1186, 1157], 12: [1186, 1357], 13: [1186, 1657],
  14: [632, 1076], 15: [819, 1076], 16: [1105, 1076] };
const plan = ([x, y]) => new THREE.Vector3((x - 837) / 120, 0, (y - 1230) / 120);

function zoneDe(g) {
  if (g.type === 'table') return g.id <= 6 ? 'R' : 'S';
  return ZONES[g.type];
}

function texture(dessin, px = 512) {
  const c = document.createElement('canvas'); c.width = c.height = px;
  const x = c.getContext('2d'); dessin(x, px);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

export class Numeros {
  constructor(scene, groupes, calque) {
    this.groupes = groupes; this.calque = calque; this.variante = '0';
    this.racine = new THREE.Group(); this.racine.name = 'numeros'; scene.add(this.racine);
    this.objets = { 1: [], 2: [], 4: [] }; this.html = { 3: [], 5: [] };
    const plat = (tex, taille, pos, y) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(taille, taille).rotateX(-Math.PI / 2).rotateY(-Math.PI / 2),
        new THREE.MeshLambertMaterial({ map: tex, transparent: true, depthWrite: false }));
      m.position.set(pos.x, y, pos.z); m.receiveShadow = true; m.renderOrder = 1; return m;
    };
    const parZone = {};
    for (const g of groupes.values()) {
      const z = zoneDe(g); parZone[z] = (parZone[z] || 0) + 1; g.code = `${z}${parZone[z]}`;
      const n = String(g.id), sol = plan(AU_SOL[g.id]);
      const vers = sol.clone().sub(g.centre);             // from the table towards its number
      const dir = Math.abs(vers.x) >= Math.abs(vers.z) ? new THREE.Vector3(Math.sign(vers.x), 0, 0)
        : new THREE.Vector3(0, 0, Math.sign(vers.z));
      // 1. painted on the floor
      const t1 = texture((x, s) => {
        x.fillStyle = '#7d7d7a'; x.font = `500 ${s * 0.62}px Futura, "Avenir Next", sans-serif`;
        x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(n, s / 2, s * 0.53);
      });
      this.objets[1].push(plat(t1, g.type === 'tambour' || g.type === 'table haute' ? 0.42 : 0.5, sol, 0.005));
      // 2. a disc on the table top, near its edge on the aisle side
      const top = g.plateau;
      const surPlateau = top.centre.clone().addScaledVector(dir, Math.max(0, (Math.abs(dir.x) ? top.demiX : top.demiZ) - 0.11));
      const t2 = texture((x, s) => {
        const gr = x.createRadialGradient(s * 0.42, s * 0.38, s * 0.05, s / 2, s / 2, s / 2);
        gr.addColorStop(0, '#fbf6ea'); gr.addColorStop(1, '#e4d9bf');
        x.fillStyle = gr; x.beginPath(); x.arc(s / 2, s / 2, s / 2 - 2, 0, Math.PI * 2); x.fill();
        x.strokeStyle = 'rgba(120,100,60,.55)'; x.lineWidth = s * 0.018;
        x.beginPath(); x.arc(s / 2, s / 2, s * 0.43, 0, Math.PI * 2); x.stroke();
        x.fillStyle = '#3b3326'; x.font = `${s * 0.46}px Didot, "Bodoni 72", serif`;
        x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(n, s / 2, s * 0.54);
      });
      // a 4 mm brass edge, and the engraved face on top, upright in the top view like the other numbers
      const disque = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.004, 40),
        new THREE.MeshStandardMaterial({ color: 0xd9ceb3, roughness: 0.4, metalness: 0.3 }));
      disque.position.set(surPlateau.x, top.y + 0.0025, surPlateau.z); disque.castShadow = true;
      const face = new THREE.Mesh(new THREE.CircleGeometry(0.06, 40).rotateX(-Math.PI / 2).rotateY(-Math.PI / 2),
        new THREE.MeshStandardMaterial({ map: t2, roughness: 0.45, metalness: 0.15, polygonOffset: true, polygonOffsetFactor: -1 }));
      face.position.y = 0.0021; disque.add(face);
      this.objets[2].push(disque);
      // 4. the architect's reference bubble, on the floor
      // texture space: up = +x of the world, right = +z; the leader goes from the circle towards the table
      const v = g.centre.clone().sub(sol).normalize(), qx = v.z, qy = -v.x;
      const t4 = texture((x, s) => {
        x.strokeStyle = '#3a3a3a'; x.lineWidth = s * 0.012;
        x.beginPath(); x.arc(s / 2, s / 2, s * 0.27, 0, Math.PI * 2); x.stroke();
        x.beginPath(); x.moveTo(s / 2 + qx * s * 0.27, s / 2 + qy * s * 0.27);
        x.lineTo(s / 2 + qx * s * 0.49, s / 2 + qy * s * 0.49); x.stroke();
        x.fillStyle = '#2e2e2e'; x.font = `500 ${s * 0.24}px Inter, sans-serif`;
        x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(n, s / 2, s * 0.515);
      });
      this.objets[4].push(plat(t4, 0.56, sol, 0.006));
      // 3 and 5: HTML labels over the table
      const e3 = document.createElement('div'); e3.className = 'badge etiquette';
      e3.innerHTML = `<div class="pastille">${n}</div><div class="fil"></div>`;
      const e5 = document.createElement('div'); e5.className = 'badge';
      e5.innerHTML = `<div class="zone"><em>${g.code[0]}</em><span>${g.code.slice(1)}</span></div>`;
      for (const [k, e] of [[3, e3], [5, e5]]) { e.hidden = true; calque.appendChild(e); this.html[k].push({ e, g }); }
    }
    for (const l of Object.values(this.objets)) l.forEach(o => { o.visible = false; this.racine.add(o); });
  }

  _direction(g) {   // towards the room, along the main axis: where the aisle is
    if (g.type === 'tambour') return new THREE.Vector3(1, 0, 0);
    const d = new THREE.Vector3(0, 0, 0.4).sub(g.centre);
    return Math.abs(d.x) >= Math.abs(d.z) ? new THREE.Vector3(Math.sign(d.x), 0, 0) : new THREE.Vector3(0, 0, Math.sign(d.z));
  }

  regler(v) {
    this.variante = v;
    for (const [k, l] of Object.entries(this.objets)) l.forEach(o => { o.visible = k === v; });
    for (const [k, l] of Object.entries(this.html)) l.forEach(({ e }) => { e.hidden = k !== v; });
  }

  maj(cam, canvas) {
    if (this.variante !== '3' && this.variante !== '5') return;
    const W = canvas.clientWidth, H = canvas.clientHeight, p = new THREE.Vector3(), q = new THREE.Vector3();
    for (const { e, g } of this.html[this.variante]) {
      p.set(g.centre.x, g.plateau.y, g.centre.z).project(cam);
      const x0 = (p.x + 1) / 2 * W, y0 = (1 - p.y) / 2 * H;
      if (this.variante === '3') {
        q.set(g.centre.x, g.plateau.y + 0.95, g.centre.z).project(cam);
        const y1 = (1 - q.y) / 2 * H, fil = Math.max(0, y0 - y1 - 13);
        e.querySelector('.fil').style.height = `${fil}px`;
        e.style.transform = `translate(${x0}px, ${y1}px) translate(-50%, -13px)`;
      } else {
        e.style.transform = `translate(${x0}px, ${y0}px) translate(-50%, -50%)`;
      }
    }
  }
}
