// The map camera: an orthographic camera around a target point, set by an azimuth, an elevation and a visible
// width (metres). Same views as the renders: from the top (long side across, bar on the left, entry on the right)
// and in 3D (the corner of the architects' axonometry). Pan, orbit, zoom by mouse, trackpad and touch.
import * as THREE from 'three';

const DEG = Math.PI / 180;
// three.js frame: x = plan right, y = up, z = plan down (the Blender model, y-up). Centre of the views: P(837, 1278).
export const VUES = {
  dessus: { az: -90, el: 90, cible: new THREE.Vector3(0, 0, 0.4), largeur: 21.6 },
  '3d': { az: -43.6, el: 38.4, cible: new THREE.Vector3(0, 0.9, 0.4), largeur: 25.5 },
};
const FORMAT = 1.6;                      // the views were framed at 16:10

const doux = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export class CameraCarte {
  constructor(canvas) {
    this.canvas = canvas;
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 400);
    this.cible = VUES.dessus.cible.clone();
    this.az = VUES.dessus.az; this.el = VUES.dessus.el; this.largeur = VUES.dessus.largeur;
    this.vue = 'dessus';
    this.niveau = 0;                     // the floor on show: its height, added to the views' targets
    this.anim = null;
    this.change = true;
    this.surChange = () => {};
    this._entrees();
  }

  // visible width for the current viewport: the 16:10 frame of the renders, contained
  largeurVisible() {
    const a = this.canvas.clientWidth / Math.max(1, this.canvas.clientHeight);
    return this.largeur * Math.max(1, FORMAT / a);
  }

  allerA(nom, duree = 900) {
    const v = VUES[nom];
    this.vue = nom;
    let az1 = v.az;
    while (az1 - this.az > 180) az1 -= 360;
    while (az1 - this.az < -180) az1 += 360;
    this.anim = { t0: performance.now(), duree, de: { az: this.az, el: this.el, l: this.largeur, c: this.cible.clone() },
      a: { az: az1, el: v.el, l: v.largeur, c: v.cible.clone().setY(v.cible.y + this.niveau) } };
  }

  // another floor: the view moves up or down by the difference, the framing kept
  changerNiveau(y, duree = 900) {
    const d = y - this.niveau;
    this.niveau = y;
    this.anim = { t0: performance.now(), duree, de: { az: this.az, el: this.el, l: this.largeur, c: this.cible.clone() },
      a: { az: this.az, el: this.el, l: this.largeur, c: this.cible.clone().setY(this.cible.y + d) } };
  }

  tourner(deg, duree = 500) {
    this.anim = { t0: performance.now(), duree, de: { az: this.az, el: this.el, l: this.largeur, c: this.cible.clone() },
      a: { az: this.az + deg, el: this.el, l: this.largeur, c: this.cible.clone() } };
  }

  zoomer(f, duree = 300) {
    this.anim = { t0: performance.now(), duree, de: { az: this.az, el: this.el, l: this.largeur, c: this.cible.clone() },
      a: { az: this.az, el: this.el, l: THREE.MathUtils.clamp(this.largeur / f, 3, 40), c: this.cible.clone() } };
  }

  maj(now) {
    if (this.anim) {
      const k = Math.min(1, (now - this.anim.t0) / this.anim.duree), e = doux(k);
      const { de, a } = this.anim;
      this.az = de.az + (a.az - de.az) * e;
      this.el = de.el + (a.el - de.el) * e;
      this.largeur = de.l + (a.l - de.l) * e;
      this.cible.lerpVectors(de.c, a.c, e);
      if (k >= 1) this.anim = null;
      this.change = true;
    }
    if (!this.change) return false;
    const az = this.az * DEG, el = this.el * DEG;
    const D = new THREE.Vector3(Math.cos(el) * Math.sin(az), Math.sin(el), Math.cos(el) * Math.cos(az));
    // the no-roll up vector, still defined straight from the top: Y cos(el) + F sin(el)
    const up = new THREE.Vector3(-Math.sin(el) * Math.sin(az), Math.cos(el), -Math.sin(el) * Math.cos(az));
    this.cam.position.copy(this.cible).addScaledVector(D, 120);
    this.cam.up.copy(up);
    this.cam.lookAt(this.cible);
    const w = this.largeurVisible() / 2, h = w * this.canvas.clientHeight / Math.max(1, this.canvas.clientWidth);
    Object.assign(this.cam, { left: -w, right: w, top: h, bottom: -h });
    this.cam.updateProjectionMatrix();
    this.cam.updateMatrixWorld();
    this.change = false;
    this.surChange();
    return true;
  }

  // ---- input: drag = pan, right drag / shift drag / two fingers = orbit, wheel / pinch = zoom at the cursor
  metresParPixel() { return this.largeurVisible() / this.canvas.clientWidth; }

  deplacer(dx, dy) {
    const m = this.metresParPixel();
    const droite = new THREE.Vector3().setFromMatrixColumn(this.cam.matrixWorld, 0); droite.y = 0; droite.normalize();
    const haut = new THREE.Vector3().setFromMatrixColumn(this.cam.matrixWorld, 1); haut.y = 0; haut.normalize();
    const s = 1 / Math.max(0.35, Math.sin(this.el * DEG));     // a screen pixel covers more ground when tilted
    this.cible.addScaledVector(droite, -dx * m).addScaledVector(haut, dy * m * s);
    this.change = true;
  }

  orbiter(dAz, dEl) {
    this.az -= dAz; this.el = THREE.MathUtils.clamp(this.el + dEl, 12, 90);
    this.change = true;
  }

  zoomEn(f, x, y) {
    const avant = this._sol(x, y);
    this.largeur = THREE.MathUtils.clamp(this.largeur / f, 3, 40);
    this.maj(performance.now());
    const apres = this._sol(x, y);
    if (avant && apres) { this.cible.add(avant.sub(apres)); this.change = true; }
  }

  _sol(x, y) {   // the point of the floor on show under a screen point
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
    const ray = new THREE.Raycaster(); ray.setFromCamera(ndc, this.cam);
    const p = new THREE.Vector3();
    return ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), -this.niveau), p) ? p : null;
  }

  _entrees() {
    const c = this.canvas, pts = new Map();
    let mode = null, dernier = null, geste = null;
    this.clicPossible = false;
    c.addEventListener('contextmenu', e => e.preventDefault());
    c.addEventListener('pointerdown', e => {
      c.setPointerCapture(e.pointerId);
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      this.anim = null;
      if (pts.size === 1) {
        mode = (e.button === 2 || e.shiftKey) ? 'orbite' : 'pan';
        dernier = { x: e.clientX, y: e.clientY };
        this.clicPossible = { x: e.clientX, y: e.clientY };
        c.classList.add('prise');
      } else if (pts.size === 2) {
        mode = 'deux'; geste = this._geste(pts); this.clicPossible = false;
      }
    });
    c.addEventListener('pointermove', e => {
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (mode === 'deux' && pts.size === 2) {
        const g = this._geste(pts);
        this.largeur = THREE.MathUtils.clamp(this.largeur * geste.d / g.d, 3, 40);
        this.orbiter((g.a - geste.a) * 180 / Math.PI, (g.cy - geste.cy) * 0.25);
        this.deplacer(g.cx - geste.cx, 0);
        geste = g; this.change = true;
        return;
      }
      if (!dernier) return;
      const dx = e.clientX - dernier.x, dy = e.clientY - dernier.y;
      dernier = { x: e.clientX, y: e.clientY };
      if (this.clicPossible && Math.hypot(e.clientX - this.clicPossible.x, e.clientY - this.clicPossible.y) > 5) this.clicPossible = false;
      if (mode === 'orbite') this.orbiter(dx * 0.3, dy * 0.25);
      else if (mode === 'pan') this.deplacer(dx, dy);
    });
    const fin = e => {
      pts.delete(e.pointerId);
      if (pts.size === 0) { mode = null; dernier = null; c.classList.remove('prise'); }
      else if (pts.size === 1) { const p = [...pts.values()][0]; dernier = { ...p }; mode = 'pan'; }
    };
    c.addEventListener('pointerup', fin);
    c.addEventListener('pointercancel', fin);
    c.addEventListener('wheel', e => {
      e.preventDefault();
      this.anim = null;
      if (e.ctrlKey) this.zoomEn(Math.exp(-e.deltaY * 0.01), e.clientX, e.clientY);        // trackpad pinch
      else if (Math.abs(e.deltaX) > Math.abs(e.deltaY) && !e.shiftKey) this.deplacer(-e.deltaX, -e.deltaY);
      else this.zoomEn(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY);
    }, { passive: false });
  }

  _geste(pts) {
    const [a, b] = [...pts.values()];
    return { d: Math.hypot(b.x - a.x, b.y - a.y), a: Math.atan2(b.y - a.y, b.x - a.x), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
  }
}
