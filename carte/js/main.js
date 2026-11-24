// The interactive map of the room. Settings can also come from the address (for captures):
//   ?vue=dessus|3d  style=fantome|blanc|transparent|fil-de-fer  systeme=A|B|C|D|0  numeros=0..5
//   heure=20:40  vitesse=0|1|30|120  fiche=<table>  cam=az,el,largeur,x,y,z  reglages=1
import * as THREE from 'three';
import { Scene3D } from './scene.js';
import { CameraCarte } from './camera.js';
import { Service, hhmm } from './service.js';
import { Systemes } from './systemes.js';
import { Numeros } from './numeros.js';
import { Interface } from './ui.js';

const P = new URLSearchParams(location.search);
const canvas = document.getElementById('vue');
const calque = document.getElementById('calque');
const s3 = new Scene3D(canvas);
const cam = new CameraCarte(canvas);

const ETAGES = [
  { nom: 'Rez-de-chaussée', fichiers: { fantome: 'modele/floor1-fantome.glb', entier: 'modele/floor1-entier.glb' },
    tables: 'donnees/floor1-tables.json' },
];
const BANQUETTES = { 49: 1, 114: 2, 306: 3, 413: 4 };   // drum (plan id) -> table

function groupes(modeles, tables) {
  const G = new Map();
  for (const t of tables) {
    if (t.type === 'bar') continue;
    G.set(t.id, { ...t, boite: new THREE.Box3(), plateaux: { fantome: [], entier: [] }, sieges: { fantome: [], entier: [] },
      banquette: { fantome: [], entier: [] }, boitePlateau: new THREE.Box3() });
  }
  for (const [cle, racine] of Object.entries(modeles)) {
    racine.updateMatrixWorld(true);
    const sieges = new Map();
    racine.traverse(o => {
      if (!o.isMesh) return;
      const ud = o.userData;
      const mb = /^banquette-(\d+)-coussin/.exec(ud.noeud || '');
      if (mb && BANQUETTES[mb[1]]) { G.get(BANQUETTES[mb[1]]).banquette[cle].push(o); return; }
      if (ud.table === undefined || ud.table === 0 || ud.role === 'fantome' || ud.role === 'suspension') return;
      const g = G.get(ud.table); if (!g) return;
      if (cle === 'fantome' && ud.mat !== 'laiton') g.boite.expandByObject(o);
      if (ud.role === 'table' && (ud.mat === 'plateau' || ud.mat === 'bois')) {
        g.plateaux[cle].push(o);
        if (cle === 'fantome') g.boitePlateau.expandByObject(o);
      }
      if (ud.role === 'assise' && ud.mat === 'cuir') {
        const k = Number(/-(\d+)$/.exec(ud.noeud)[1]);
        const cleS = `${ud.table}-${k}`;
        if (!sieges.has(cleS)) sieges.set(cleS, { g, k, l: [] });
        sieges.get(cleS).l.push(o);
      }
    });
    for (const { g, k, l } of [...sieges.values()].sort((a, b) => a.k - b.k)) g.sieges[cle][k - 1] = l;
  }
  for (const g of G.values()) {
    const b = g.boitePlateau;
    g.plateau = { centre: b.getCenter(new THREE.Vector3()), demiX: (b.max.x - b.min.x) / 2, demiZ: (b.max.z - b.min.z) / 2, y: b.max.y };
    g.hauteur = b.max.y;
  }
  return G;
}

async function demarrer() {
  const e = ETAGES[0];
  const modeles = await s3.chargerEtage(0, e.fichiers);
  const donnees = await (await fetch(e.tables)).json();
  const G = groupes(modeles, donnees.tables);

  const [h, m] = (P.get('heure') || '20:10').split(':').map(Number);
  const service = new Service(donnees.tables, { heure: h * 60 + m });
  const sys = new Systemes(s3.scene, G, calque);
  const num = new Numeros(s3.scene, G, calque);
  const ui = new Interface(service);

  // selection: a black band around the chosen table
  const choix = new THREE.Mesh(undefined, new THREE.MeshBasicMaterial({ color: 0x151515, transparent: true, opacity: 0.95, depthWrite: false }));
  choix.visible = false; s3.scene.add(choix);
  const choisir = id => {
    const g = G.get(id);
    if (!g) { choix.visible = false; ui.cacher(); return; }
    choix.geometry = g.anneau.geometry; choix.position.copy(g.anneau.position); choix.position.y = 0.007; choix.visible = true;
    ui.montrer(id);
  };
  ui.surFermer = () => { choix.visible = false; };

  // ---- the settings
  const regler = (sel, val, f) => { const el = document.getElementById(sel); if (val !== null) el.value = val; f(el.value);
    el.onchange = () => f(el.value); };
  regler('style', P.get('style'), v => { s3.appliquerStyle(v); });
  regler('systeme', P.get('systeme'), v => sys.regler(v));
  regler('numeros', P.get('numeros'), v => num.regler(v));
  if (P.get('reglages')) document.getElementById('protos').open = true;
  let vitesse = Number(P.get('vitesse') ?? 30);
  const sv = document.getElementById('vitesse'), lecture = document.getElementById('lecture');
  if (vitesse) sv.value = String(vitesse);
  const majLecture = () => { lecture.textContent = vitesse ? '❚❚' : '▶'; };
  majLecture();
  sv.onchange = () => { vitesse = Number(sv.value); majLecture(); };
  lecture.onclick = () => { vitesse = vitesse ? 0 : Number(sv.value); majLecture(); };

  // views, floors, tools
  const boutons = (id, attr, f) => document.querySelectorAll(`#${id} button`).forEach(b => b.onclick = () => {
    document.querySelectorAll(`#${id} button`).forEach(x => x.classList.toggle('on', x === b)); f(b.dataset[attr]); });
  boutons('vues', 'vue', v => cam.allerA(v));
  boutons('etages', 'etage', () => {});
  document.querySelectorAll('#outils button').forEach(b => b.onclick = () => {
    const a = b.dataset.action;
    if (a === 'zoom+') cam.zoomer(1.4); else if (a === 'zoom-') cam.zoomer(1 / 1.4);
    else if (a === 'gauche') cam.tourner(-45); else if (a === 'droite') cam.tourner(45);
    else cam.allerA(cam.vue);
  });
  const vue = P.get('vue') || 'dessus';
  cam.allerA(vue, 0);
  document.querySelectorAll('#vues button').forEach(x => x.classList.toggle('on', x.dataset.vue === vue));
  if (P.get('cam')) {
    const [az, el, l, x, y, z] = P.get('cam').split(',').map(Number);
    Object.assign(cam, { az, el, largeur: l, anim: null }); cam.cible.set(x, y, z); cam.change = true;
  }

  // ---- picking: click a table for its card, hover shows the hand
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  const viser = ev => {
    const r = canvas.getBoundingClientRect();
    ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, cam.cam);
    const hit = ray.intersectObjects(sys.picks, false)[0];
    return hit ? hit.object.userData.table : null;
  };
  canvas.addEventListener('pointerup', ev => { if (cam.clicPossible) { choisir(viser(ev)); } });
  canvas.addEventListener('pointermove', ev => { if (ev.buttons === 0) canvas.classList.toggle('survol', viser(ev) !== null); });
  if (P.get('fiche')) choisir(Number(P.get('fiche')));

  window.addEventListener('resize', () => { s3.taille(); cam.change = true; });

  // ---- the loop
  let avant = performance.now(), tick = 0;
  const boucle = now => {
    const dt = Math.min(0.1, (now - avant) / 1000); avant = now;
    if (vitesse) service.avancer(dt * vitesse / 60);
    cam.maj(now);
    sys.maj(service, cam.cam, canvas, now, s3.style);
    num.maj(cam.cam, canvas);
    if (now - tick > 250) { ui.maj(); tick = now; }
    s3.rendre(cam.cam);
    requestAnimationFrame(boucle);
  };
  ui.maj();
  requestAnimationFrame(boucle);
  document.getElementById('chargement').classList.add('fini');
  window.carte = { s3, cam, service, sys, num, ui, G, choisir, hhmm, pret: true };
}

demarrer().catch(err => {
  document.getElementById('chargement').textContent = 'La carte n’a pas pu se charger : ' + err.message;
  console.error(err);
});
