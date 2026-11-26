// Captures of the interactive map (carte/), for the step pages (step 7: the map as chosen; the interface is dark), at
// Retina scale, plus a short video of the map being handled. Serves carte/ itself on a free port.
// usage: node outils/carte_captures.mjs [video | etage | cuisine]   (etage: the 1st floor's captures only, 25/11;
//        cuisine: the open kitchen's, 26/11)
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { spawn, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(process.env.PLAYWRIGHT_PKG || `${homedir()}/Desktop/Portfolio/tools/package.json`);
const { chromium } = require('playwright');

const R = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DOS = { carte: path.join(R, 'rendus', '9-carte-finale'), etage: path.join(R, 'rendus', '19-carte-deux-etages'),
  cuisine: path.join(R, 'rendus', '25-cuisine-ouverte') };
Object.values(DOS).forEach(d => fs.mkdirSync(d, { recursive: true }));
const OUT = DOS.carte;
const port = 8800 + Math.floor(Math.random() * 100);
const serveur = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: path.join(R, 'carte'), stdio: 'ignore' });
await new Promise(r => setTimeout(r, 700));
const base = `http://127.0.0.1:${port}/`;

// step 7, the map as chosen: [folder, name, address settings, element to capture alone (optional)]
const PLANS = [
  ['carte', 'sombre-dessus', 'vitesse=0&heure=20:25'],
  ['carte', 'sombre-3d', 'vitesse=0&heure=20:25&vue=3d'],
  ['carte', 'sombre-legende', 'vitesse=0&heure=20:25&vue=3d&surligne=commandee', '.pied'],
  ['carte', 'sombre-menu', 'vitesse=0&heure=20:25&vue=3d&ouvert=systeme', '.r3'],
  ['carte', 'sombre-fiche', 'vitesse=0&heure=20:25&vue=3d&fiche=15', '#fiche'],
  // the 1st floor, on the ground floor (25/11): the two floors are one building
  ['etage', 'etage-dessus', 'vitesse=0&heure=20:25&etage=1'],
  ['etage', 'etage-3d', 'vitesse=0&heure=20:25&vue=3d&etage=1'],
  ['etage', 'etage-fiche-omakase', 'vitesse=0&heure=20:25&vue=3d&etage=1&fiche=100', '#fiche'],
  ['etage', 'etage-fil-de-fer', 'vitesse=0&heure=20:25&vue=3d&etage=1&style=fil-de-fer'],
  ['etage', 'rdc-3d', 'vitesse=0&heure=20:25&vue=3d'],
  // the open kitchen as chosen (26/11 night); zoom: [world point (three.js, m), wheel steps] to close in on it
  ['cuisine', 'carte-rdc-3d', 'vitesse=0&heure=20:25&vue=3d'],
  ['cuisine', 'carte-rdc-dessus', 'vitesse=0&heure=20:25'],
  ['cuisine', 'carte-rdc-cuisine', 'vitesse=0&heure=20:25&vue=3d', null, ['cuisine-comptoir-inox', 13]],
];

const b = await chromium.launch({ channel: 'chrome', headless: true });
const seul = process.argv[2];
if (seul !== 'video') {
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  for (const [dos, nom, q, el, zoom] of PLANS.filter(x => !seul || x[0] === seul)) {
    await p.goto(`${base}?${q}`);
    await p.waitForFunction(() => window.carte?.pret, null, { timeout: 60000 });
    await p.waitForTimeout(1800);
    if (zoom) {               // wheel steps over the screen point of a world point
      const [x, y] = await p.evaluate(w => { const C = window.carte, V = C.cam.cam.position.constructor;
        let v = new V(...(Array.isArray(w) ? w : [0, 0, 0]));
        if (!Array.isArray(w)) {          // an object's name: the centre of its box, from the scene
          let o = null; C.s3.scene.traverse(x => { if (!o && x.name === w) o = x; });
          const lo = new V(1e9, 1e9, 1e9), hi = new V(-1e9, -1e9, -1e9);
          o.updateWorldMatrix(true, true);
          o.traverse(m => { if (m.geometry) { m.geometry.computeBoundingBox(); const bb = m.geometry.boundingBox;
            for (const c of [bb.min, bb.max]) { const q = c.clone().applyMatrix4(m.matrixWorld); lo.min(q); hi.max(q); } } });
          v = lo.add(hi).multiplyScalar(0.5);
        }
        v.project(C.cam.cam); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]; }, zoom[0]);
      // the map zooms on the screen's centre: first drag the point there (left button pans), then zoom
      await p.mouse.move(x, y); await p.mouse.down();
      for (let k = 1; k <= 30; k++) { await p.mouse.move(x + (800 - x) * k / 30, y + (500 - y) * k / 30); await p.waitForTimeout(16); }
      await p.mouse.up(); await p.waitForTimeout(400);
      await p.mouse.move(800, 500);
      for (let k = 0; k < zoom[1]; k++) { await p.mouse.wheel(0, -60); await p.waitForTimeout(60); }
      await p.waitForTimeout(1200);
    }
    await p.screenshot({ path: path.join(DOS[dos], `${nom}.png`) });
    if (el) {   // the element alone, with a margin of map around it
      const r = await p.locator(el).boundingBox(), m = 24;
      // a popover opens above its bar: take both
      const au = el === '.r3' ? '.r3-pop:not([hidden])' : el === '.pied' ? '#legende' : null;
      const r2 = au ? await p.locator(au).boundingBox().catch(() => null) : null;
      const x0 = Math.min(r.x, r2?.x ?? r.x) - m, y0 = Math.min(r.y, r2?.y ?? r.y) - m;
      const x1 = Math.max(r.x + r.width, r2 ? r2.x + r2.width : 0) + m, y1 = r.y + r.height + m;
      await p.screenshot({ path: path.join(DOS[dos], `${nom}-proche.png`),
        clip: { x: Math.max(0, x0), y: Math.max(0, y0), width: Math.min(1600, x1) - Math.max(0, x0), height: Math.min(1000, y1) - Math.max(0, y0) } });
    }
    console.log('capture', nom);
  }
}
if (seul === 'video' || seul === undefined) {
  // the map being handled: top view, switch to 3D, orbit, zoom, a click on a table, the service running
  // frames from Chrome's screencast, then a 30 fps video with the system ffmpeg
  const ctx = await b.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.goto(`${base}?vitesse=120&heure=20:05`);
  await p.waitForFunction(() => window.carte?.pret, null, { timeout: 60000 });
  await p.waitForTimeout(500);
  const cdp = await ctx.newCDPSession(p), images = [];
  cdp.on('Page.screencastFrame', async f => { images.push({ t: f.metadata.timestamp, d: f.data });
    await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {}); });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, everyNthFrame: 1 });
  await p.waitForTimeout(1500);
  await p.click('#vues button[data-vue="3d"]'); await p.waitForTimeout(1800);
  const glisser = async (x0, y0, x1, y1, bouton = 'left', pas = 40) => {
    await p.mouse.move(x0, y0); await p.mouse.down({ button: bouton });
    for (let k = 1; k <= pas; k++) { await p.mouse.move(x0 + (x1 - x0) * k / pas, y0 + (y1 - y0) * k / pas); await p.waitForTimeout(16); }
    await p.mouse.up({ button: bouton });
  };
  await glisser(900, 500, 1060, 515, 'right', 60); await p.waitForTimeout(500);
  await glisser(1060, 515, 890, 480, 'right', 60); await p.waitForTimeout(500);
  for (let k = 0; k < 8; k++) { await p.mouse.move(870, 560); await p.mouse.wheel(0, -50); await p.waitForTimeout(45); }
  await p.waitForTimeout(600);
  const pos = await p.evaluate(() => { const C = window.carte, g = C.G.get(15), v = g.centre.clone(); v.y = 0.75;
    v.project(C.cam.cam); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]; });
  await p.mouse.move(pos[0], pos[1]); await p.waitForTimeout(400); await p.mouse.click(pos[0], pos[1]);
  await p.waitForTimeout(2200);
  await p.click('.r3-menu[data-cle="systeme"] .r3-b'); await p.waitForTimeout(900);
  await p.click('.r3-menu[data-cle="systeme"] .r3-pop button[data-v="D"]'); await p.waitForTimeout(2000);
  await p.click('.r3-menu[data-cle="systeme"] .r3-b'); await p.waitForTimeout(700);
  await p.click('.r3-menu[data-cle="systeme"] .r3-pop button[data-v="C"]'); await p.waitForTimeout(800);
  await p.click('#fiche .fermer'); await p.waitForTimeout(400);
  await p.hover('.l-e[data-e="servie"]'); await p.waitForTimeout(1300);
  await p.hover('.l-e[data-e="commandee"]'); await p.waitForTimeout(1300);
  await p.mouse.move(870, 560); await p.waitForTimeout(600);
  await p.click('#outils button[data-action="recentrer"]'); await p.waitForTimeout(1200);
  await p.click('#vues button[data-vue="dessus"]'); await p.waitForTimeout(2200);
  await p.waitForTimeout(1200);
  await cdp.send('Page.stopScreencast');
  await ctx.close();
  const dos = path.join(OUT, '_images'); fs.mkdirSync(dos, { recursive: true });
  const debut = images[0].t, fin = images[images.length - 1].t;
  let k = 0, n = 0;
  for (let t = debut; t <= fin; t += 1 / 30) {          // resample to a steady 30 fps
    while (k + 1 < images.length && images[k + 1].t <= t) k++;
    fs.writeFileSync(path.join(dos, `${String(n++).padStart(5, '0')}.jpg`), Buffer.from(images[k].d, 'base64'));
  }
  console.log('video', n, 'images,', (fin - debut).toFixed(1), 's');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '30', '-i', path.join(dos, '%05d.jpg'), '-c:v', 'libx264',
    '-crf', '23', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path.join(OUT, 'manipulation.mp4')]);
  fs.rmSync(dos, { recursive: true, force: true });
  console.log('video', path.join(OUT, 'manipulation.mp4'));
}
await b.close();
serveur.kill();
