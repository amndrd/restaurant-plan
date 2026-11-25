// The 3D scene of the map: the floor model (glTF exported by outils/blender/floor1.py), its white styles, the grid
// floor, one sun fixed in the world, and a line pass (depth + normals) that redraws the outlines of the renders.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// Blender material -> white tone of the styles (same values as floor1.py, display sRGB)
const TONS = {
  mur: 0xf7f7f7, 'tete-de-mur': 0xfbfbfb, poteau: 0xf5f5f5, tambour: 0xededeb, marche: 0xe6e6e6, cadre: 0xd2d2d2,
  banquette: 0xf6f5f3, pierre: 0xeeedeb, comptoir: 0xf0f0f0, meuble: 0xf7f7f7, miroir: 0xfafafa, rocher: 0xedecea,
  rideau: 0xf9f8f6, bordure: 0xefefef, gravier: 0xf0efed, plateau: 0xeaeaea, acier: 0xc5c5c5, cuir: 0xf6f5f3,
  bois: 0xf1f0ed, pot: 0xf4f4f4, terre: 0xe9e8e5, feuillage: 0xeef2ea, laiton: 0xfafafa,
  dalle: 0xf3f3f2, lumiere: 0xfdfcf8, ecorce: 0xe8e6e2,
};
const SOLEIL = new THREE.Vector3(-0.492, 0.819, -0.296).normalize();   // Blender (35°, 0, -121°), y-up
const ORIGINE = new THREE.Vector3(0, 0, 0.4);                           // centre of the grid, P(837, 1278)

function grille(base, ligne, mineur, majeur, fondu) {
  // matte floor with the 1 m and 5 m grid of the renders, anti-aliased in screen space
  const m = new THREE.MeshStandardMaterial({ color: base, roughness: 0.95, metalness: 0 });
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, { uLigne: { value: new THREE.Color(ligne) }, uMin: { value: mineur },
      uMaj: { value: majeur }, uO: { value: ORIGINE }, uFondu: { value: new THREE.Vector2(...(fondu || [1e4, 1e4 + 1])) } });
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vMonde;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvMonde = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vMonde; uniform vec3 uLigne; uniform float uMin, uMaj; uniform vec3 uO; uniform vec2 uFondu;
float lignes(vec2 p, float pas, float px) {
  vec2 q = abs(fract(p / pas + 0.5) - 0.5) * pas; vec2 w = fwidth(p) * px;
  vec2 l = 1.0 - smoothstep(vec2(0.0), w, q); return max(l.x, l.y);
}`).replace('#include <color_fragment>', `#include <color_fragment>
vec2 p = vMonde.xz - uO.xz;
float g = max(lignes(p, 1.0, 1.0) * uMin, lignes(p, 5.0, 1.6) * uMaj);
g *= 1.0 - smoothstep(uFondu.x, uFondu.y, length(p));
diffuseColor.rgb = mix(diffuseColor.rgb, uLigne, g);`);
  };
  return m;
}

export class Scene3D {
  constructor(canvas) {
    this.canvas = canvas;
    const r = this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
    r.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    r.shadowMap.enabled = true;
    r.shadowMap.type = THREE.PCFShadowMap;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf4f3f1);

    // light: a soft sky and one sun fixed in the world (the same for both views, as in the renders)
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0xdedad3, 2.55));
    const sun = this.soleil = new THREE.DirectionalLight(0xffffff, 0.95);
    sun.position.copy(SOLEIL).multiplyScalar(40).add(ORIGINE);
    sun.target.position.copy(ORIGINE);
    sun.castShadow = true;
    Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 90 });
    sun.shadow.mapSize.set(4096, 4096);
    sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.02; sun.shadow.radius = 4; sun.shadow.intensity = 0.6;   // soft, like the 25° sun of the renders
    this.scene.add(sun, sun.target);

    // the ground around the building, with the grid fading out
    const sol = new THREE.Mesh(new THREE.PlaneGeometry(240, 240).rotateX(-Math.PI / 2),
      grille(0xe6e5e2, 0xa8a8a8, 0.45, 0.8, [14, 30]));
    sol.position.y = -0.052; sol.receiveShadow = true; sol.layers.enable(1);
    this.scene.add(sol);

    this.etages = [];            // one group per floor
    this.actif = 0;              // the floor on show (the 1st floor brings the ground floor under its slab)
    this.style = 'fantome';
    this._passe();
    this.taille();
  }

  // ---- the line pass: normals + depth of the solid geometry, edges by Laplacian / normal differences
  _passe() {
    const opts = { type: THREE.HalfFloatType };
    this.rtCouleur = new THREE.WebGLRenderTarget(1, 1, { ...opts, samples: 4 });
    this.rtNormales = new THREE.WebGLRenderTarget(1, 1, { ...opts });
    this.rtNormales.depthTexture = new THREE.DepthTexture(1, 1);
    this.matNormales = new THREE.MeshNormalMaterial();
    this.composite = new THREE.ShaderMaterial({
      uniforms: { tCouleur: { value: null }, tNormales: { value: null }, tProf: { value: null }, texel: { value: new THREE.Vector2() },
        pres: { value: 1 }, loin: { value: 1 }, encre: { value: new THREE.Color(0x4d4d4d) }, force: { value: 1 },
        seuil: { value: 0.04 }, pas: { value: 1 } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
      fragmentShader: `
varying vec2 vUv; uniform sampler2D tCouleur, tNormales, tProf; uniform vec2 texel; uniform float pres, loin, force, seuil, pas;
uniform vec3 encre;
float prof(vec2 uv) { return pres + texture2D(tProf, uv).x * (loin - pres); }     // orthographic: linear depth
vec3 nor(vec2 uv) { return texture2D(tNormales, uv).xyz * 2.0 - 1.0; }
void main() {
  vec3 c = texture2D(tCouleur, vUv).rgb;
  vec2 dx = vec2(texel.x * pas, 0.0), dy = vec2(0.0, texel.y * pas);
  float d0 = prof(vUv);
  float lap = abs(prof(vUv + dx) + prof(vUv - dx) - 2.0 * d0) + abs(prof(vUv + dy) + prof(vUv - dy) - 2.0 * d0);
  vec3 n0 = nor(vUv);
  float dn = max(max(1.0 - dot(n0, nor(vUv + dx)), 1.0 - dot(n0, nor(vUv - dx))),
                 max(1.0 - dot(n0, nor(vUv + dy)), 1.0 - dot(n0, nor(vUv - dy))));
  float l = max(smoothstep(seuil, seuil * 2.2, lap), smoothstep(0.18, 0.42, dn));
  c = mix(c, encre, l * force);
  gl_FragColor = linearToOutputTexel(vec4(c, 1.0));
}`,
      depthTest: false, depthWrite: false,
    });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.composite);
    this.quad.frustumCulled = false;
    this.sceneQuad = new THREE.Scene(); this.sceneQuad.add(this.quad);
    this.camQuad = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  }

  taille() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight, pr = this.renderer.getPixelRatio();
    this.renderer.setSize(w, h, false);
    const W = Math.round(w * pr), H = Math.round(h * pr);
    this.rtCouleur.setSize(W, H); this.rtNormales.setSize(W, H);
    this.composite.uniforms.texel.value.set(1 / W, 1 / H);
    this.composite.uniforms.pas.value = pr >= 2 ? 1.5 : 1;
  }

  // ---- loading a floor: two models, cut (fantôme) and whole (transparent, fil de fer); the 1st floor's also has the
  //      ground floor under its slab (dessous), shown in every style
  async chargerEtage(n, fichiers) {
    const charge = new GLTFLoader();
    const g = new THREE.Group(); g.name = `etage-${n}`;
    const modeles = {};
    for (const [cle, url] of Object.entries(fichiers)) {
      const gltf = await charge.loadAsync(url);
      modeles[cle] = gltf.scene;
      this._preparer(gltf.scene);
      gltf.scene.visible = false;
      g.add(gltf.scene);
    }
    this.scene.add(g);
    this.etages[n] = { groupe: g, modeles };
    this.appliquerStyle(this.style);
    return modeles;
  }

  _preparer(racine) {
    // each mesh: its role (from the node extras), a white material by tone, edges for the see-through styles
    racine.traverse(o => {
      if (!o.isMesh) return;
      let p = o; while (p && p.userData.role === undefined) p = p.parent;
      const ud = p ? p.userData : {};
      o.userData.role = ud.role; o.userData.fin = ud.fin; o.userData.table = ud.table; o.userData.noeud = p ? p.name : o.name;
      o.userData.bar = ud.bar; o.userData.feuillage = ud.feuillage;
      const nomMat = (o.material.name || '').replace(/\.\d+$/, '');
      o.userData.mat = nomMat;
      o.castShadow = o.receiveShadow = true;
      o.userData.aretes = new THREE.EdgesGeometry(o.geometry, 28);
    });
  }

  montrerEtage(n) { this.actif = n; this.appliquerStyle(this.style); }

  appliquerStyle(style) {
    this.style = style;
    const entier = style === 'transparent' || style === 'fil-de-fer';
    this.etages.forEach((e, n) => {
      if (!e) return;
      e.groupe.visible = n === this.actif;
      for (const [cle, racine] of Object.entries(e.modeles)) {
        racine.visible = cle === 'dessous' || (cle === 'entier') === entier;
        if (racine.visible && e.groupe.visible) racine.traverse(o => { if (o.isMesh) this._habiller(o, style); });
      }
    });
    this.composite.uniforms.encre.value.set(style === 'fil-de-fer' ? 0x5a5a5a : 0x4d4d4d);
  }

  _habiller(o, style) {
    const ud = o.userData, role = ud.role;
    if (o.userData.trait) { o.remove(o.userData.trait); o.userData.trait = null; }
    if (o.userData.cache) { o.remove(o.userData.cache); o.userData.cache = null; }
    o.layers.set(0); o.castShadow = true;
    const ton = TONS[ud.mat] ?? 0xf3f3f3;
    let mat;
    const trait = (couleur, opacite, devant = true) => {
      const l = new THREE.LineSegments(ud.aretes, new THREE.LineBasicMaterial({ color: couleur, transparent: true,
        opacity: opacite, depthWrite: false, depthTest: devant }));
      l.raycast = () => {}; o.add(l); return l;
    };
    if (role === 'sol') {
      mat = grille(0xf9f8f6, 0xcfcfcf, 0.35, 0.55);
      o.layers.enable(1);
    } else if (ud.feuillage) {   // the ivy: shaded, no lines (thousands of leaves would only make a grey mass)
      mat = style === 'fantome' ? new THREE.MeshStandardMaterial({ color: ton, roughness: 0.9 })
        : new THREE.MeshStandardMaterial({ color: ton, transparent: true, opacity: style === 'transparent' ? 0.42 : 0.22,
          depthWrite: false, roughness: 0.9 });
      o.castShadow = style === 'fantome';
    } else if (style === 'fantome') {
      if (role === 'fantome') {
        mat = new THREE.MeshStandardMaterial({ color: 0xfbfbfb, transparent: true, opacity: 0.16,
          depthWrite: false, roughness: 0.6 });
        o.castShadow = false;
        ud.trait = trait(ud.fin ? 0xd6d6d6 : 0xb8b8b8, ud.fin ? 0.5 : 0.8);
      } else if (ud.mat === 'pave' || ud.mat === 'verre') {
        mat = new THREE.MeshStandardMaterial({ color: 0xf2f6f8, transparent: true, opacity: ud.mat === 'pave' ? 0.55 : 0.16,
          depthWrite: false, roughness: 0.3 });
        o.castShadow = ud.mat === 'pave';
        ud.trait = trait(0xbdbdbd, 0.7);
      } else if (ud.fin) {
        mat = new THREE.MeshStandardMaterial({ color: ton, roughness: 0.9 });
        ud.trait = trait(0xb0b0b0, 0.8);
      } else {
        mat = new THREE.MeshStandardMaterial({ color: ton, roughness: ud.mat === 'laiton' ? 0.45 : 0.88 });
        o.layers.enable(1);
      }
    } else if (style === 'transparent') {
      mat = new THREE.MeshStandardMaterial({ color: ton, transparent: true, opacity: ud.mat === 'pave' ? 0.3 : 0.42,
        depthWrite: false, roughness: 0.85 });
      if (!ud.fin) o.layers.enable(1);
      ud.trait = trait(0xa8a8a8, 0.55, false);
    } else {   // fil de fer: faces almost invisible but hiding what is behind; hidden edges drawn lighter
      mat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.03 });
      o.castShadow = false;
      if (!ud.fin) o.layers.enable(1);
      ud.trait = trait(ud.fin ? 0xb5b5b5 : 0x6a6a6a, ud.fin ? 0.6 : 0.9, true);
      ud.cache = trait(0xb9b9b9, 0.45, false);
    }
    if (o.userData.matBase) o.userData.matBase.dispose?.();
    o.material = mat; o.userData.matBase = mat;
  }

  rendre(cam) {
    const r = this.renderer;
    // 1. normals + depth of the solid geometry (layer 1)
    cam.layers.set(1);
    this.scene.overrideMaterial = this.matNormales;
    const fond = this.scene.background; this.scene.background = null;
    r.setRenderTarget(this.rtNormales); r.setClearColor(0x8080ff, 1); r.clear();
    r.render(this.scene, cam);
    this.scene.overrideMaterial = null; this.scene.background = fond;
    // 2. colour
    cam.layers.set(0); cam.layers.enable(1);
    r.setRenderTarget(this.rtCouleur); r.render(this.scene, cam);
    // 3. lines over the colour, to the screen
    const u = this.composite.uniforms;
    u.tCouleur.value = this.rtCouleur.texture; u.tNormales.value = this.rtNormales.texture;
    u.tProf.value = this.rtNormales.depthTexture; u.pres.value = cam.near; u.loin.value = cam.far;
    u.seuil.value = 0.035;
    r.setRenderTarget(null); r.render(this.sceneQuad, this.camQuad);
  }
}
