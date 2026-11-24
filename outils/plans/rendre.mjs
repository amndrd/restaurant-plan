// Renders an SVG to a PNG at its own size (3840 x 2160 for the plans), with Chrome.
// usage: node rendre.mjs <in.svg> <out.png>
import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const require = createRequire(process.env.PLAYWRIGHT_PKG || `${homedir()}/Desktop/Portfolio/tools/package.json`);
const { chromium } = require('playwright');
const [src, out] = process.argv.slice(2);
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width: 3840, height: 2160 }, deviceScaleFactor: 1 });
await p.goto(pathToFileURL(path.resolve(src)).href);
await p.waitForTimeout(600);
await p.screenshot({ path: out });
console.log('png', out);
await b.close();
