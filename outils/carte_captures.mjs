// Captures of the interactive map (carte/), for the step pages: each view, state system, numbering design and
// style, at Retina scale, plus a short video of the map being handled. Serves carte/ itself on a free port.
// usage: node outils/carte_captures.mjs [video]
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { spawn, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(process.env.PLAYWRIGHT_PKG || `${homedir()}/Desktop/Portfolio/tools/package.json`);
const { chromium } = require('playwright');

const R = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(R, 'rendus', '6-carte');
fs.mkdirSync(OUT, { recursive: true });
const port = 8800 + Math.floor(Math.random() * 100);
const serveur = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: path.join(R, 'carte'), stdio: 'ignore' });
await new Promise(r => setTimeout(r, 700));
const base = `http://127.0.0.1:${port}/`;

const PLANS = [   // name, address settings
  ['carte-dessus', 'vitesse=0'],
  ['carte-3d', 'vitesse=0&vue=3d'],
  ['carte-fiche', 'vitesse=0&vue=3d&fiche=6'],
  ['carte-reglages', 'vitesse=0&reglages=1'],
  ['etats-A-halo', 'vitesse=0&vue=3d&systeme=A'],
  ['etats-B-plateau', 'vitesse=0&vue=3d&systeme=B'],
  ['etats-C-places', 'vitesse=0&vue=3d&systeme=C'],
  ['etats-D-minuteur', 'vitesse=0&vue=3d&systeme=D'],
  ['etats-A-proche', 'vitesse=0&vue=3d&systeme=A&cam=-50,40,9,-0.6,0.6,1.8'],
  ['etats-C-proche', 'vitesse=0&vue=3d&systeme=C&cam=-50,40,9,-0.6,0.6,1.8'],
  ['etats-D-proche', 'vitesse=0&vue=3d&systeme=D&cam=-50,40,9,-0.6,0.6,1.8'],
  ...['1', '2', '3', '4', '5'].flatMap(n => [[`numeros-${n}-dessus`, `vitesse=0&systeme=0&numeros=${n}`],
    [`numeros-${n}-proche`, `vitesse=0&vue=3d&systeme=0&numeros=${n}&cam=-50,40,${n === '2' ? 3.2 : 8.5},${n === '2' ? '1.75,0.6,1.25' : '0.2,0.6,2.6'}`]]),
  ['style-fil-de-fer', 'vitesse=0&vue=3d&style=fil-de-fer'],
  ['style-transparent', 'vitesse=0&vue=3d&style=transparent&systeme=B'],
  ['style-blanc', 'vitesse=0&vue=3d&style=blanc&systeme=0'],
];

const b = await chromium.launch({ channel: 'chrome', headless: true });
const seul = process.argv[2];
if (seul !== 'video') {
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  for (const [nom, q] of PLANS) {
    await p.goto(`${base}?${q}`);
    await p.waitForFunction(() => window.carte?.pret, null, { timeout: 60000 });
    await p.waitForTimeout(1800);
    await p.screenshot({ path: path.join(OUT, `${nom}.png`) });
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
  const t0 = Date.now();
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
  await glisser(800, 560, 700, 500, 'left', 40); await p.waitForTimeout(600);
  const pos = await p.evaluate(() => { const C = window.carte, g = C.G.get(6), v = g.centre.clone(); v.y = 0.75;
    v.project(C.cam.cam); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]; });
  await p.mouse.move(pos[0], pos[1]); await p.waitForTimeout(400); await p.mouse.click(pos[0], pos[1]);
  await p.waitForTimeout(2500);
  await p.click('#protos summary'); await p.waitForTimeout(700);
  await p.selectOption('#systeme', 'D'); await p.waitForTimeout(2200);
  await p.selectOption('#systeme', 'C'); await p.waitForTimeout(1800);
  await p.selectOption('#systeme', 'A'); await p.waitForTimeout(600);
  await p.click('#protos summary'); await p.waitForTimeout(400);
  await p.click('#fiche .fermer'); await p.waitForTimeout(400);
  await p.click('#outils button[data-action="recentrer"]'); await p.waitForTimeout(1200);
  await p.click('#vues button[data-vue="dessus"]'); await p.waitForTimeout(2200);
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
