# Crop of a plan with a pixel grid, to read coordinates (original image pixels).
# usage: python3 grille.py <image> <x0> <y0> <x1> <y1> <out.png> [pas=50] [zoom=2]
import sys
from PIL import Image, ImageDraw, ImageFont
img, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
pas = int(sys.argv[7]) if len(sys.argv) > 7 else 50
zoom = float(sys.argv[8]) if len(sys.argv) > 8 else 2
im = Image.open(img).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize((int(im.width * zoom), int(im.height * zoom)), Image.LANCZOS)
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
except Exception:
    f = ImageFont.load_default()
for x in range((x0 // pas + 1) * pas, x1, pas):
    X = (x - x0) * zoom
    d.line([(X, 0), (X, im.height)], fill=(255, 0, 80) if x % (pas * 2) == 0 else (0, 200, 255), width=1)
    d.text((X + 2, 2), str(x), fill=(255, 230, 0), font=f)
for y in range((y0 // pas + 1) * pas, y1, pas):
    Y = (y - y0) * zoom
    d.line([(0, Y), (im.width, Y)], fill=(255, 0, 80) if y % (pas * 2) == 0 else (0, 200, 255), width=1)
    d.text((2, Y + 2), str(y), fill=(255, 230, 0), font=f)
im.save(out)
print(out, im.size)
