// Renders a plan's sheet (an SVG with its own pixel size and a viewBox in mm) to a PNG at that size, and to a PDF
// at the sheet's size in mm, with Chrome.
// usage: node rendre_plan.mjs <in.svg> <out.png> <out.pdf>
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(process.env.PLAYWRIGHT_PKG || `${homedir()}/Desktop/Portfolio/tools/package.json`);
const { chromium } = require('playwright');
const [src, png, pdf] = process.argv.slice(2);
const svg = fs.readFileSync(src, 'utf8');
const tete = svg.slice(0, 400);
const width = Math.round(Number(tete.match(/width="([\d.]+)"/)[1]));
const height = Math.round(Number(tete.match(/height="([\d.]+)"/)[1]));
const vb = tete.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
await p.goto(pathToFileURL(path.resolve(src)).href);
await p.waitForTimeout(1200);
await p.screenshot({ path: png });
console.log('png', png, width, height);
if (pdf) {
  const mm = svg.replace(/width="[\d.]+" height="[\d.]+"/, `width="${vb[1]}mm" height="${vb[2]}mm"`);
  const q = await b.newPage({ viewport: { width: 1600, height: 1200 } });   // an HTML page (the first shows the SVG)
  await q.setContent(`<html><head><style>@page{size:${vb[1]}mm ${vb[2]}mm;margin:0}body{margin:0}</style></head><body>${mm}</body></html>`, { waitUntil: 'domcontentloaded' });
  await q.waitForTimeout(800);
  await q.pdf({ path: pdf, width: `${vb[1]}mm`, height: `${vb[2]}mm`, printBackground: true, pageRanges: '1' });
  console.log('pdf', pdf);
}
await b.close();
