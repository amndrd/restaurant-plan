// Renders an SVG to a PNG at its own size (read from its width and height), with Chrome.
// usage: node rendre.mjs <in.svg> <out.png>
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(process.env.PLAYWRIGHT_PKG || `${homedir()}/Desktop/Portfolio/tools/package.json`);
const { chromium } = require('playwright');
const [src, out] = process.argv.slice(2);
const tete = fs.readFileSync(src, 'utf8').slice(0, 600);
const width = Math.round(Number(tete.match(/width="([\d.]+)"/)[1]));
const height = Math.round(Number(tete.match(/height="([\d.]+)"/)[1]));
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
await p.goto(pathToFileURL(path.resolve(src)).href);
await p.waitForTimeout(800);
await p.screenshot({ path: out });
console.log('png', out, width, height);
await b.close();
