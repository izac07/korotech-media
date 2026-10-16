#!/usr/bin/env python3
"""Régénère comptes/a-publier.html : posts des comptes NON reliés à Make (theme.json sans ig_id), à publier à la main.
Usage : python3 tools/a_publier.py   (n'affiche que les posts dont la date est aujourd'hui ou plus tard)"""
import json, glob, os, html, datetime
BASE = "https://izac07.github.io/korotech-media/"
today = datetime.date.today().isoformat()
cards = ""
for tf in sorted(glob.glob("comptes/*/theme.json")):
    th = json.load(open(tf)); slug = tf.split("/")[1]
    if th.get("ig_id"): continue
    metas = sorted((json.load(open(m)) | {"_d": os.path.dirname(m)} for m in glob.glob(f"comptes/{slug}/posts/*/meta.json")), key=lambda m: m["date"])
    metas = [m for m in metas if m["date"][:10] >= today]
    if not metas: continue
    cards += f"<h2>@{html.escape(th['handle'])}</h2>"
    for m in metas:
        d = m["_d"]
        if m["format"] == "Reel":
            media = f"<video src='{BASE}{d}/reel.mp4' controls playsinline></video><a class='dl' href='{BASE}{d}/reel.mp4' download>Télécharger la vidéo</a>"
        else:
            imgs = "".join(f"<img src='{BASE}{p}' loading='lazy'>" for p in sorted(glob.glob(f"{d}/slide_*.jpg")))
            media = f"<div class='strip'>{imgs}</div><p class='hint'>Appui long sur chaque image → Enregistrer (dans l'ordre).</p>"
        cards += (f"<div class='card'><div class='when'>{html.escape(m['date'])} · {m['format']} · {m['id']}</div><h3>{html.escape(m['titre'])}</h3>{media}"
                  f"<textarea readonly>{html.escape(m['legende'])}</textarea><button onclick=\"navigator.clipboard.writeText(this.previousElementSibling.value);this.textContent='Copié ✓'\">Copier la légende</button></div>")
page = f"""<!doctype html><html lang=fr><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Posts à publier</title>
<style>body{{font-family:system-ui,sans-serif;padding:16px;background:#f4f4f5;color:#111;max-width:720px;margin:auto}}h2{{margin-top:32px}}.card{{background:#fff;border-radius:16px;padding:16px;margin:16px 0;box-shadow:0 1px 4px #0001}}
.when{{font-size:13px;color:#666}}h3{{margin:6px 0 12px}}.strip{{display:flex;gap:8px;overflow-x:auto}}.strip img{{height:300px;border-radius:8px}}video{{width:100%;max-height:480px;border-radius:8px;background:#000}}
textarea{{width:100%;box-sizing:border-box;height:140px;margin-top:12px;font:14px system-ui;border-radius:8px;border:1px solid #ddd;padding:8px}}button,.dl{{display:inline-block;margin-top:8px;padding:10px 14px;border-radius:10px;border:0;background:#111;color:#fff;font-size:15px;text-decoration:none}}.hint{{font-size:13px;color:#666}}</style></head>
<body><h1>Posts à publier à la main</h1><p>Programme-les dans Instagram (Paramètres avancés → Programmer) à la date indiquée.</p>{cards or '<p>Rien à publier à la main 🎉</p>'}</body></html>"""
open("comptes/a-publier.html", "w").write(page)
print("ok")
