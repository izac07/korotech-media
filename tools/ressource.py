#!/usr/bin/env python3
"""Ressources gratuites envoyées en DM (mécanique « commente un mot-clé ») : un contenu.json -> un PDF A4 clair
aux couleurs du compte, publié sur GitHub Pages (https://izac07.github.io/korotech-media/ressources/<dossier>/<fichier>.pdf).
Usage : python3 tools/ressource.py ressources/<dossier>/contenu.json        (écrit le PDF à côté, nommé d'après "fichier")

contenu.json : {"fichier", "compte", "mot_cle", "titre", "sous_titre", "intro",
                "couleurs": {"accent", "fond_titre", "texte_titre", "police_titre"},
                "blocs": [ {"h": "titre de section"}, {"p": "paragraphe"}, {"ul": ["…"]},
                           {"etapes": [{"t": "titre", "d": "texte", "facile": "version plus facile (optionnel)"}]},
                           {"prompt": "texte à copier", "titre": "…"}, {"note": "encadré"},
                           {"tableau": {"colonnes": [...], "lignes": [[...], ...]}}, {"saut": true} ],
                "fin": "dernier paragraphe (ce qui arrive ensuite, sans prix)"}
Texte : **gras** autorisé ; le titre accepte du HTML (ex. <span class='acc'>mot en couleur</span>).
"""
import json, os, sys, re, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K


def rich(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", H.escape(s)).replace("\n", "<br>")


def page(c):
    col = c["couleurs"]; acc = col["accent"]
    out = []
    for b in c["blocs"]:
        if "h" in b: out.append(f"<h2>{rich(b['h'])}</h2>")
        elif "p" in b: out.append(f"<p>{rich(b['p'])}</p>")
        elif "ul" in b: out.append("<ul>" + "".join(f"<li>{rich(x)}</li>" for x in b["ul"]) + "</ul>")
        elif "etapes" in b:
            for i, e in enumerate(b["etapes"], 1):
                fac = f"<div class='fac'>Plus facile : {rich(e['facile'])}</div>" if e.get("facile") else ""
                out.append(f"<div class='et'><div class='n'>{e.get('num', i)}</div><div><div class='et-t'>{rich(e['t'])}</div><div>{rich(e['d'])}</div>{fac}</div></div>")
        elif "prompt" in b:
            t = f"<div class='pt-t'>{rich(b['titre'])}</div>" if b.get("titre") else ""
            out.append(f"<div class='pt'>{t}<div class='pt-x'>{rich(b['prompt'])}</div></div>")
        elif "note" in b: out.append(f"<div class='note'>{rich(b['note'])}</div>")
        elif "tableau" in b:
            tb = b["tableau"]
            th = "".join(f"<th>{rich(x)}</th>" for x in tb["colonnes"])
            tr = "".join("<tr>" + "".join(f"<td>{rich(x)}</td>" for x in l) + "</tr>" for l in tb["lignes"])
            out.append(f"<table><tr>{th}</tr>{tr}</table>")
        elif b.get("saut"): out.append("<div class='saut'></div>")
    fonts = K._font_faces(["Inter", col.get("police_titre", "Archivo Black")])
    pt = col.get("police_titre", "Archivo Black")
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
@page{{size:A4;margin:16mm 16mm 18mm}}
body{{font:600 10.5pt/1.55 Inter,sans-serif;color:#1d1d1f;margin:0}}
.cover{{background:{col['fond_titre']};color:{col['texte_titre']};border-radius:14px;padding:26px 28px 24px;margin-bottom:18px}}
.cover .k{{font:700 9pt Inter;letter-spacing:2px;text-transform:uppercase;opacity:.75}}
.cover h1{{font:400 25pt/1.12 '{pt}';margin:10px 0 8px;{'font-weight:800;' if pt != 'Archivo Black' else ''}}}
.cover .s{{font:600 11.5pt/1.4 Inter;opacity:.9}}
.cover .acc{{color:{acc}}}
.intro{{font-size:11pt;margin:0 0 6px}}
h2{{font:800 14pt Inter;color:{acc};margin:20px 0 8px;border-bottom:2px solid {acc}33;padding-bottom:4px;break-after:avoid}}
p{{margin:6px 0}} ul{{margin:6px 0 6px 18px;padding:0}} li{{margin:3px 0}}
.et{{display:flex;gap:12px;margin:10px 0;break-inside:avoid}}
.et .n{{flex:none;width:30px;height:30px;border-radius:50%;background:{acc};color:#fff;font:800 12pt/30px Inter;text-align:center}}
.et-t{{font-weight:800;font-size:11.5pt}}
.fac{{font-size:9.5pt;color:#5b5b60;margin-top:2px}}
.pt{{background:#f4f4f6;border-left:4px solid {acc};border-radius:8px;padding:10px 12px;margin:8px 0;break-inside:avoid}}
.pt-t{{font-weight:800;margin-bottom:4px}} .pt-x{{font-family:'Inter';font-size:10pt;color:#2b2b30}}
.note{{background:{acc}14;border:1px solid {acc}55;border-radius:8px;padding:10px 12px;margin:10px 0;break-inside:avoid}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:10pt;break-inside:avoid}}
th{{background:{acc};color:#fff;text-align:left;padding:6px 8px}} td{{border:1px solid #d8d8dc;padding:7px 8px;height:16px}}
.saut{{break-after:page}}
.fin{{margin-top:22px;padding-top:12px;border-top:1px solid #ddd;font-size:10pt;color:#444}}
.fin b{{color:{acc}}}
</style></head><body>
<div class='cover'><div class='k'>@{H.escape(c['compte'])} · ressource gratuite</div><h1>{c['titre']}</h1><div class='s'>{rich(c['sous_titre'])}</div></div>
<p class='intro'>{rich(c['intro'])}</p>
{''.join(out)}
<div class='fin'>{rich(c['fin'])}<br><br>Tu as reçu ce guide en commentant <b>{H.escape(c['mot_cle'])}</b> sous un reel de <b>@{H.escape(c['compte'])}</b>. Partage-le à quelqu'un à qui il peut servir.</div>
</body></html>"""


def build(path):
    c = json.load(open(path, encoding="utf-8"))
    d = os.path.dirname(os.path.abspath(path))
    hp = os.path.join(d, "_page.html"); open(hp, "w", encoding="utf-8").write(page(c))
    out = os.path.join(d, c["fichier"] + ".pdf")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**K.chromium_args()); pg = b.new_page()
        pg.goto("file://" + hp); pg.wait_for_timeout(300)
        pg.pdf(path=out, format="A4", print_background=True, margin={"top": "16mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
        b.close()
    os.remove(hp)
    return out


def apercu(path, png):
    """Capture PNG de la page (contrôle visuel sans lecteur PDF)."""
    c = json.load(open(path, encoding="utf-8"))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**K.chromium_args()); pg = b.new_page(viewport={"width": 794, "height": 1123})
        pg.set_content(page(c)); pg.wait_for_timeout(300); pg.screenshot(path=png, full_page=True); b.close()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--apercu":
        apercu(sys.argv[2], sys.argv[3])
    else:
        for a in sys.argv[1:]:
            print(build(a))
