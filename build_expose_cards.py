#!/usr/bin/env python3
"""Build EXPOSED cards for every remaining Telegram destination."""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.expanduser("~/workspace/telegramscammers-site")
OUT = os.path.join(BASE, "assets", "expose-all")
os.makedirs(OUT, exist_ok=True)

accounts = json.load(open(os.path.join(BASE, "accounts.json")))
previews = json.load(open(os.path.expanduser("~/workspace/afterhour-telegram-sweep/previews-20261013.json")))
admin = {}
try:
    for line in open(os.path.expanduser("~/workspace/afterhour-telegram-sweep/admin-intel-20261013.md")):
        if "→" in line and "@" in line:
            parts = line.split("→")
            admin[parts[0].strip("- ").strip()] = parts[1].split("(")[0].strip()
except FileNotFoundError:
    pass

COVERED = {'gammasphere47','crestedgeroom','nexacointrade','bincofreealert',
           'de_gainers_free_circle','clintonstock1','f_trad_free_channel',
           'mrquickerfreealert','qwackersol','stockwise01','trexfreecircle',
           'xyrofxfreegains508'}

# handle -> set of afterhour usernames
seen = {}
links = {}
for a in accounts:
    for link in a.get("telegram_links", []):
        h = link.rsplit("/", 1)[-1]
        seen.setdefault(h, set()).add(a.get("username"))
        links[h] = link

def font(size, bold=True):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
              "/usr/share/fonts/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

F_TITLE = font(64); F_BIG = font(44); F_MED = font(34); F_SMALL = font(28)

W, H = 1080, 1350
def card(handle, sources, idx, total):
    img = Image.new("RGB", (W, H), "black")
    d = ImageDraw.Draw(img)
    # red banner
    d.rectangle([0, 0, W, 150], fill=(178, 34, 34))
    d.text((40, 38), "EXPOSED", font=F_TITLE, fill="white")
    d.text((W-40, 55), f"{idx}/{total}", font=F_MED, fill="white", anchor="ra")
    y = 200
    is_private = handle.startswith("+")
    label = "PRIVATE INVITE CHANNEL" if is_private else "t.me/" + handle
    for line in textwrap.wrap(label, 28):
        d.text((40, y), line, font=F_BIG, fill=(255, 200, 60)); y += 60
    y += 10
    pv = previews.get(handle, {}) if isinstance(previews.get(handle), dict) else {}
    title = (pv.get("title") or "").strip()
    if title and not is_private:
        for line in textwrap.wrap(title, 32)[:2]:
            d.text((40, y), line, font=F_MED, fill="white"); y += 48
        y += 8
    # sources box
    d.rectangle([30, y, W-30, y+90+40*min(4, max(1, (len(sources)+1)//2))], outline=(178,34,34), width=4)
    y += 25
    d.text((50, y), "FUNNELED FROM AfterHour BY:", font=F_SMALL, fill=(255,120,120)); y += 42
    src = ", ".join(sorted(sources))
    for line in textwrap.wrap(src, 34)[:4]:
        d.text((50, y), line, font=F_MED, fill="white"); y += 44
    y += 60
    # admin
    adm = admin.get(handle)
    if adm:
        d.rectangle([30, y, W-30, y+130], fill=(20, 60, 20))
        d.text((50, y+12), "CHANNEL'S OWN PAGE NAMES:", font=F_SMALL, fill=(150,255,150))
        d.text((50, y+52), adm, font=F_BIG, fill=(80, 255, 80))
        y += 160
    desc = (pv.get("description") or "").replace("&amp;", "&")
    desc = " ".join(desc.split())
    if desc and not is_private:
        d.text((40, y), "CHANNEL DESCRIPTION:", font=F_SMALL, fill=(170,170,170)); y += 40
        for line in textwrap.wrap(desc, 40)[:6]:
            d.text((40, y), line, font=F_SMALL, fill=(200,200,200)); y += 38
        y += 20
    if is_private:
        d.text((40, y), "Private invite link — contents hidden.", font=F_MED, fill=(170,170,170)); y += 50
        d.text((40, y), "The AfterHour accounts above", font=F_SMALL, fill=(170,170,170)); y += 38
        d.text((40, y), "are the public funnel trail.", font=F_SMALL, fill=(170,170,170)); y += 60
    # footer
    d.rectangle([0, H-110, W, H], fill=(178, 34, 34))
    d.text((40, H-80), "telegramscammers.com", font=F_BIG, fill="white")
    d.text((W-40, H-72), "full database", font=F_SMALL, fill="white", anchor="ra")
    return img

jobs = [(h, sorted(s)) for h, s in sorted(seen.items()) if h not in COVERED]
total = len(jobs)
paths = []
for i, (h, s) in enumerate(jobs, 1):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in h)
    p = os.path.join(OUT, f"expose-{i:02d}-{safe}.png")
    card(h, s, i, total).save(p)
    paths.append((p, h, s))
    print(i, h, "->", ", ".join(s[:4]))

json.dump([{"path": p, "handle": h, "sources": s} for p, h, s in paths],
          open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print("TOTAL:", total)
