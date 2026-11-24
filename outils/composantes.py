# Dark regions of the plan (walls, columns, exterior), numbered, to sort them.
# usage: .venv/bin/python composantes.py <plan.png> <out.png> [seuil=60]
import sys, json
import cv2, numpy as np
src, out = sys.argv[1], sys.argv[2]
seuil = int(sys.argv[3]) if len(sys.argv) > 3 else 60
g = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
mask = (g < seuil).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
vis = (vis * 0.45).astype(np.uint8)
rng = np.random.default_rng(3)
info = []
for i in range(1, n):
    x, y, w, h, a = stats[i]
    if a < 150:
        continue
    col = rng.integers(80, 255, 3).tolist()
    vis[lab == i] = col
    info.append({'id': i, 'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h), 'aire': int(a)})
for d in info:
    cx, cy = d['x'] + d['w'] // 2, d['y'] + d['h'] // 2
    cv2.putText(vis, str(d['id']), (cx - 10, cy + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(vis, str(d['id']), (cx - 10, cy + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
cv2.imwrite(out, vis)
json.dump(info, open(out.rsplit('.', 1)[0] + '.json', 'w'), indent=0)
print(len(info), 'composantes')
