# Lists the pins of a public Pinterest "ideas" page or board (plain GET, the JSON embedded in the page).
# usage: python3 pinterest.py <url> [max]  -> one JSON line per pin: id, titre, image, lien
import json, re, sys, urllib.request
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
url = sys.argv[1]
mx = int(sys.argv[2]) if len(sys.argv) > 2 else 60
html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30).read().decode('utf-8', 'ignore')
blobs = re.findall(r'<script[^>]*id="__PWS_(?:INITIAL_PROPS|DATA)__"[^>]*>(.*?)</script>', html, re.S)
seen, out = set(), []
def walk(o):
    if isinstance(o, dict):
        im = o.get('images')
        if isinstance(im, dict) and o.get('id') and (im.get('orig') or im.get('736x')):
            pid = str(o['id'])
            if pid not in seen:
                seen.add(pid)
                img = (im.get('orig') or im.get('736x'))['url']
                titre = (o.get('grid_title') or o.get('title') or o.get('description') or o.get('auto_alt_text') or '').strip()
                out.append({'id': pid, 'titre': titre[:140], 'image': img, 'lien': o.get('link') or '',
                            'pin': f'https://www.pinterest.com/pin/{pid}/'})
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
for b in blobs:
    try:
        walk(json.loads(b))
    except Exception:
        pass
for p in out[:mx]:
    print(json.dumps(p, ensure_ascii=False))
