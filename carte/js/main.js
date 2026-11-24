// The interactive map of the room. Settings can also come from the address (for captures):
//   ?vue=dessus|3d  style=fantome|transparent|fil-de-fer  systeme=C|B|D  numeros=3|5|0  theme=clair|sombre
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
  { nom: 'Rez-de-chaussée', fichiers: { fantome: 'modele/floor1-fantome.glb', entier: 'modele/floor1-entier.glb' },
    tables: 'donnees/floor1-tables.json' },
];
const BANQUETTES = { 49: 1, 114: 2, 306: 3, 413: 4 };   // drum (plan id) -> table
if (P.get('nu')) document.body.classList.add('nu');     // the map alone, without the interface

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
  const tables = donnees.tables;
  const G = groupes(modeles, tables);

  const [h, m] = (P.get('heure') || '20:10').split(':').map(Number);
  const service = new Service(tables, { heure: h * 60 + m });
  const sys = new Systemes(s3.scene, G, calque);
  const num = new Numeros(G, calque);
  const ui = new Interface(service);

  // selection: a black band around the chosen table
  const choix = new THREE.Mesh(undefined, new THREE.MeshBasicMaterial({ color: 0x151515, transparent: true, opacity: 0.95, depthWrite: false }));
  choix.renderOrder = 2;
  choix.visible = false; s3.scene.add(choix);
  const choisir = id => {
    const g = G.get(id);
    if (!g) { choix.visible = false; ui.cacher(); return; }
    choix.geometry = g.anneau.geometry; choix.position.copy(g.anneau.position); choix.position.y = 0.007; choix.visible = true;
    ui.montrer(id);
  };
  ui.surFermer = () => { choix.visible = false; };

  // ---- the settings: style, tables, numbers (first option = default), in the chosen design
  const valeurs = {};
  for (const [cle, r] of Object.entries(REGLAGES)) {
    const v = P.get(cle);
    valeurs[cle] = r.options.some(o => o[0] === v) ? v : r.options[0][0];
  }
  const appliquer = (cle, v) => {
    if (cle === 'style') s3.appliquerStyle(v);
    if (cle === 'systeme') sys.regler(v);
    if (cle === 'numeros') num.regler(v);
  };
  Object.entries(valeurs).forEach(([cle, v]) => appliquer(cle, v));
  const reglages = new Reglages(valeurs, appliquer);
  const legende = new Legende(service, sys);
  if (P.get('ouvert')) reglages.ouvrir(P.get('ouvert'));
  if (P.get('legende')) legende.ouvrir(true);
  if (P.get('surligne')) { legende.ouvrir(true); legende.surligner(P.get('surligne')); }

  // ---- the theme: light or dark, the interface and the map together; remembered on this device
  const LUNE = '<svg viewBox="0 0 20 20"><path d="M15.5 12.6A6.5 6.5 0 0 1 7.4 4.5a6.5 6.5 0 1 0 8.1 8.1z" fill="currentColor"/></svg>';
  const SOLEIL = '<svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="3.6" fill="currentColor"/><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round">' +
    [0, 45, 90, 135, 180, 225, 270, 315].map(a => { const r = a * Math.PI / 180;
      return `<path d="M${10 + 6 * Math.cos(r)} ${10 + 6 * Math.sin(r)}L${10 + 8 * Math.cos(r)} ${10 + 8 * Math.sin(r)}"/>`; }).join('') + '</g></svg>';
  const bTheme = document.getElementById('theme');
  const theme = t => {
    document.body.classList.toggle('sombre', t === 'sombre');
    s3.appliquerTheme(t);
    sys.sombre = t === 'sombre';
    choix.material.color.set(t === 'sombre' ? 0xf2f2f3 : 0x151515);
    bTheme.innerHTML = t === 'sombre' ? SOLEIL : LUNE;
    bTheme.title = t === 'sombre' ? 'Passer en clair' : 'Passer en sombre';
    try { localStorage.setItem('carte-theme', t); } catch (e) { /* private mode */ }
  };
  let leTheme = P.get('theme') || (() => { try { return localStorage.getItem('carte-theme'); } catch (e) { return null; } })() || 'clair';
  theme(leTheme);
  bTheme.onclick = () => { leTheme = leTheme === 'sombre' ? 'clair' : 'sombre'; theme(leTheme); };

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
  document.querySelectorAll('#outils button[data-action]').forEach(b => b.onclick = () => {
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
    if (now - tick > 250) { ui.maj(); legende.maj(); tick = now; }
    s3.rendre(cam.cam);
    requestAnimationFrame(boucle);
  };
  ui.maj();
  requestAnimationFrame(boucle);
  document.getElementById('chargement').classList.add('fini');
  window.carte = { s3, cam, service, sys, num, ui, G, choisir, reglages, legende, theme, hhmm, pret: true };
}

demarrer().catch(err => {
  document.getElementById('chargement').textContent = 'La carte n’a pas pu se charger : ' + err.message;
  console.error(err);
});
