// The interactive map of the room. Settings can also come from the address (for captures):
//   ?vue=dessus|3d  style=fantome|transparent|fil-de-fer  systeme=C|B|D  numeros=3|5|0
//   ouvert=style|systeme|numeros (a menu of the command bar)  legende=1 (unfolded)  surligne=<state>
//   heure=20:40  vitesse=0|1|30|120  fiche=<table>  cam=az,el,largeur,x,y,z  nu=1 (the map alone)
import * as THREE from 'three';
import { Scene3D } from './scene.js';
import { CameraCarte } from './camera.js';
import { Service, hhmm } from './service.js';
import { Systemes } from './systemes.js';
import { Numeros } from './numeros.js';
import { Interface } from './ui.js';
import { Reglages, REGLAGES } from './reglages.js';
import { Legende } from './legende.js';

const P = new URLSearchParams(location.search);
const canvas = document.getElementById('vue');
const calque = document.getElementById('calque');
const s3 = new Scene3D(canvas);
const cam = new CameraCarte(canvas);

const ETAGES = [
  { nom: 'Rez-de-chaussée', sol: 0, graine: 11, tables: 'donnees/floor1-tables.json',
    fichiers: { fantome: 'modele/floor1-fantome.glb', entier: 'modele/floor1-entier.glb' } },
  // the 1st floor stands on the ground floor: its model is raised by 3.35 m and brings the ground floor under its slab
  { nom: '1er étage', sol: 3.35, graine: 23, tables: 'donnees/floor2-tables.json',
    fichiers: { fantome: 'modele/floor2-fantome.glb', entier: 'modele/floor2-entier.glb', dessous: 'modele/floor1-sous-dalle.glb' } },
];
const BANQUETTES = { 49: 1, 114: 2, 306: 3, 413: 4 };   // drum (plan id) -> table
if (P.get('nu')) document.body.classList.add('nu');     // the map alone, without the interface

function groupes(modeles, tables) {
  const G = new Map();
  for (const t of tables) {           // the bars are groups too (0, 100, 101): their stools and their counter
    G.set(t.id, { ...t, boite: new THREE.Box3(), plateaux: { fantome: [], entier: [] }, sieges: { fantome: [], entier: [] },
      banquette: { fantome: [], entier: [] }, boitePlateau: new THREE.Box3() });
  }
  for (const cle of ['fantome', 'entier']) {
    const racine = modeles[cle];
    racine.updateMatrixWorld(true);
    const sieges = new Map();
    racine.traverse(o => {
      if (!o.isMesh) return;
      const ud = o.userData;
      const mb = /^banquette-(\d+)-coussin/.exec(ud.noeud || '');
      if (mb && BANQUETTES[mb[1]] && G.has(BANQUETTES[mb[1]])) { G.get(BANQUETTES[mb[1]]).banquette[cle].push(o); return; }
      const idBar = ud.bar ?? (ud.noeud === 'bar-plateaux' ? 0 : undefined);
      if (idBar !== undefined && cle === 'fantome' && G.has(idBar)) {   // a counter: where its bar's label stands
        G.get(idBar).boite.expandByObject(o); G.get(idBar).boitePlateau.expandByObject(o); return;
      }
      if (ud.table === undefined || ud.role === 'fantome' || ud.role === 'suspension') return;
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
  const [h, m] = (P.get('heure') || '20:10').split(':').map(Number);

  // ---- the settings: style, tables, numbers (first option = default), in the chosen design
  const valeurs = {};
  for (const [cle, r] of Object.entries(REGLAGES)) {
    const v = P.get(cle);
    valeurs[cle] = r.options.some(o => o[0] === v) ? v : r.options[0][0];
  }

  // ---- the floors, each with its model, its tables, its service and its markers. (26/11) The 1st floor loads in the
  //      background once the ground floor is on show: the "1er" button shows it at once, with no loading screen
  const etats = [], charges = [];
  const chargement = document.getElementById('chargement');
  const preparer = n => (charges[n] ??= charger(n));
  async function charger(n) {
    const e = ETAGES[n];
    const modeles = await s3.chargerEtage(n, e.fichiers);
    const tables = (await (await fetch(e.tables, { cache: 'no-cache' })).json()).tables;
    const G = groupes(modeles, tables);
    const service = new Service(tables, { heure: etats[0] ? etats[0].service.t : h * 60 + m, graine: e.graine });
    const sys = new Systemes(s3.scene, G, calque, e.sol);
    const num = new Numeros(G, calque);
    sys.regler(valeurs.systeme); num.regler(valeurs.numeros);
    sys.montrer(false); num.montrer(false);
    return (etats[n] = { G, service, sys, num });
  }
  const e0 = await preparer(0);
  const ui = new Interface(e0.service);
  const legende = new Legende(e0.service, e0.sys);
  let actif = 0;

  // selection: a black band around the chosen table
  const choix = new THREE.Mesh(undefined, new THREE.MeshBasicMaterial({ color: 0x151515, transparent: true, opacity: 0.95, depthWrite: false }));
  choix.renderOrder = 2;
  choix.visible = false; s3.scene.add(choix);
  const choisir = id => {
    const g = etats[actif].G.get(id);
    if (!g) { choix.visible = false; ui.cacher(); return; }
    choix.geometry = g.anneau.geometry; choix.position.copy(g.anneau.position);
    choix.position.y = ETAGES[actif].sol + 0.007; choix.visible = true;
    ui.montrer(id);
  };
  ui.surFermer = () => { choix.visible = false; };

  // ---- showing a floor: its model (the 1st floor over the ground floor), its markers, its service in the panels
  let demande = 0;
  const activer = async (n, duree = 900) => {
    const d = ++demande, b = document.querySelector(`#etages button[data-etage="${n}"]`);
    if (!etats[n]) b.classList.add('attente');          // clicked before the end of the background loading
    const et = await preparer(n);
    b.classList.remove('attente');
    if (d !== demande) return;                           // another floor was asked for meanwhile
    actif = n;
    etats.forEach((x, k) => { if (x) { x.sys.montrer(k === n); x.num.montrer(k === n); } });
    s3.montrerEtage(n);
    choix.visible = false; ui.cacher();
    ui.s = et.service; legende.lier(et.service, et.sys); ui.maj();
    document.getElementById('etage-nom').textContent = `${ETAGES[n].nom} · service du soir`;
    document.querySelectorAll('#etages button').forEach(x => x.classList.toggle('on', Number(x.dataset.etage) === n));
    cam.changerNiveau(ETAGES[n].sol, duree);
  };

  const appliquer = (cle, v) => {
    if (cle === 'style') s3.appliquerStyle(v);
    if (cle === 'systeme') etats.forEach(x => x && x.sys.regler(v));
    if (cle === 'numeros') etats.forEach(x => x && x.num.regler(v));
  };
  Object.entries(valeurs).forEach(([cle, v]) => appliquer(cle, v));
  const reglages = new Reglages(valeurs, appliquer);
  if (P.get('ouvert')) reglages.ouvrir(P.get('ouvert'));
  if (P.get('legende')) legende.ouvrir(true);

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
  // a gesture that tilts the top view (or brings the 3D view flat) selects the matching button, as a click would
  cam.surVue = v => document.querySelectorAll('#vues button').forEach(x => x.classList.toggle('on', x.dataset.vue === v));
  document.querySelectorAll('#etages button').forEach(b => b.onclick = () => {
    const n = Number(b.dataset.etage);
    if (n !== actif) activer(n).catch(err => console.error(err));
  });
  document.querySelectorAll('#outils button[data-action]').forEach(b => b.onclick = () => {
    const a = b.dataset.action;
    if (a === 'zoom+') cam.zoomer(1.4); else if (a === 'zoom-') cam.zoomer(1 / 1.4);
    else if (a === 'gauche') cam.tourner(-45); else if (a === 'droite') cam.tourner(45);
    else cam.allerA(cam.vue);
  });
  const vue = P.get('vue') || 'dessus';
  await activer(Number(P.get('etage')) === 1 ? 1 : 0, 0);
  cam.allerA(vue, 0);
  document.querySelectorAll('#vues button').forEach(x => x.classList.toggle('on', x.dataset.vue === vue));
  if (P.get('cam')) {
    const [az, el, l, x, y, z] = P.get('cam').split(',').map(Number);
    Object.assign(cam, { az, el, largeur: l, anim: null }); cam.cible.set(x, y, z); cam.change = true;
  }
  if (P.get('surligne')) { legende.ouvrir(true); legende.surligner(P.get('surligne')); }

  // ---- picking: click a table for its card, hover shows the hand
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  const viser = ev => {
    const r = canvas.getBoundingClientRect();
    ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, cam.cam);
    const hit = ray.intersectObjects(etats[actif].sys.picks, false)[0];
    return hit ? hit.object.userData.table : null;
  };
  canvas.addEventListener('pointerup', ev => { if (cam.clicPossible) { choisir(viser(ev)); } });
  canvas.addEventListener('pointermove', ev => { if (ev.buttons === 0) canvas.classList.toggle('survol', viser(ev) !== null); });
  if (P.get('fiche')) choisir(Number(P.get('fiche')));

  window.addEventListener('resize', () => { s3.taille(); cam.change = true; });

  // ---- the loop: every floor's service runs on the same clock; the floor on show is drawn
  let avant = performance.now(), tick = 0;
  const boucle = now => {
    const dt = Math.min(0.1, (now - avant) / 1000); avant = now;
    if (vitesse) etats.forEach(x => x && x.service.avancer(dt * vitesse / 60));
    cam.maj(now);
    const et = etats[actif];
    et.sys.maj(et.service, cam.cam, canvas, now, s3.style);
    et.num.maj(cam.cam, canvas);
    if (now - tick > 250) { ui.maj(); legende.maj(); tick = now; }
    s3.rendre(cam.cam);
    requestAnimationFrame(boucle);
  };
  ui.maj();
  requestAnimationFrame(boucle);
  chargement.classList.add('fini');
  // the other floor, in the background, once the first frames are drawn
  setTimeout(() => {
    const n = actif ? 0 : 1;
    preparer(n).then(() => { if (actif !== n) s3.prechauffer(n, cam.cam); }).catch(err => console.error(err));
  }, 400);
  window.carte = { s3, cam, etats, activer, get actif() { return actif; }, ui, choisir, reglages, legende, hhmm,
    get service() { return etats[actif].service; }, get G() { return etats[actif].G; }, pret: true };
}

demarrer().catch(err => {
  document.getElementById('chargement').textContent = 'La carte n’a pas pu se charger : ' + err.message;
  console.error(err);
});
