#!/usr/bin/env python3
"""Stories Instagram du NNN (Mental d'Acier, novembre 2026), 1080x1920, aux couleurs du carnet PDF (noir, crème, or).
Chaque visuel laisse une zone libre pour le sticker à poser dans Instagram (sondage, curseur, question, « À vous »).
Usage : python3 tools/stories_nnn.py   (écrit ressources/mentaldacier/stories/*.png)"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

RAC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOS = os.path.join(RAC, "ressources", "mentaldacier", "stories")
OR, ENCRE, PAPIER, CLAIR = "#d9a441", "#141414", "#f1ece2", "#ece6da"


def img(nom):
    return "data:image/png;base64," + base64.b64encode(open(os.path.join(DOS, nom), "rb").read()).decode()


def page(corps, fond=ENCRE):
    fonts = K._font_faces(["Anton", "Caveat", "Space Grotesk", "JetBrains Mono"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;overflow:hidden;background:{fond};color:{CLAIR if fond == ENCRE else ENCRE};font:500 34px/1.4 'Space Grotesk';position:relative}}
.pad{{position:absolute;inset:150px 80px 170px}}
.tag{{font:400 26px 'JetBrains Mono';letter-spacing:5px;color:{OR}}}
.big{{font:400 200px/.86 Anton;text-transform:uppercase;letter-spacing:-2px}}
.t{{font:400 92px/1 Anton;text-transform:uppercase}}
.t em{{font-style:normal;color:{OR}}}
.main{{font:700 58px/1.05 Caveat;color:{OR};transform:rotate(-2deg)}}
.zone{{font-size:0;color:transparent}}  /* espace laissé libre pour le sticker Instagram, rien de visible */
.sig{{position:absolute;left:80px;right:80px;bottom:90px;display:flex;justify-content:space-between;font:400 24px 'JetBrains Mono';letter-spacing:3px;opacity:.6}}
.tally{{display:flex;gap:16px;flex-wrap:wrap;width:820px}}
.tally i{{display:block;width:16px;height:86px;background:{CLAIR}22;border-radius:3px}}
.tally i.on{{background:{OR}}}
.cap{{border:6px solid {CLAIR};box-shadow:0 30px 60px #0008;transform:rotate(-3deg)}}
.cta{{background:{OR};color:{ENCRE};font:400 86px/1 Anton;text-transform:uppercase;padding:26px 40px;display:inline-block}}
</style></head><body>{corps}<div class='sig'><span>@MENTALDACIER2030</span><span>NNN 2026</span></div></body></html>"""


def checkin(j):
    traits = "".join(f"<i class='{'on' if k < j else ''}'></i>" for k in range(30))
    return page(f"""<div class='pad'>
 <div class='tag'>CHECK-IN · {j:02d}/30</div>
 <div class='big' style='margin-top:40px'>NNN<br><span style='color:{OR}'>JOUR {j}</span></div>
 <div class='tally' style='margin-top:60px'>{traits}</div>
 <div class='t' style='margin-top:80px;font-size:84px'>T'as tenu<br><em>hier ?</em></div>
 <div class='zone' style='height:300px;margin-top:50px'>SONDAGE ICI</div>
 <div class='main' style='margin-top:40px'>une croix par soir. on tient ensemble.</div>
</div>""")


def guide(cap, titre, sous):
    return page(f"""<div class='pad'>
 <div class='tag'>GUIDE GRATUIT · 10 PAGES</div>
 <div class='t' style='margin-top:30px'>{titre}</div>
 <div style='margin:20px 0 0;font-size:36px;opacity:.85'>{sous}</div>
 <div style='margin:70px auto 0;width:540px'><img class='cap' src='{img(cap)}' style='width:540px'></div>
 <div style='position:absolute;left:0;right:0;bottom:60px;text-align:center'>
  <div class='cta'>Réponds « NNN »</div>
  <div class='main' style='margin-top:30px'>et je te l'envoie en DM 📩</div>
 </div>
</div>""")


def pote():
    return page(f"""<div class='pad'>
 <div class='tag'>NNN · À DEUX C'EST PLUS FACILE</div>
 <div class='big' style='margin-top:60px;font-size:150px;line-height:1'>Envoie<br>ça à ton<br><span style='color:{OR}'>pote</span></div>
 <div style='margin-top:60px;font-size:40px;max-width:820px'>Celui qui fait le NNN avec toi. Chaque soir, vous vous envoyez votre numéro de jour. <b>Juste un chiffre.</b></div>
 <div class='zone' style='height:260px;margin-top:70px'>MENTIONNE TON POTE ICI</div>
 <div class='main' style='margin-top:50px'>celui qui craque paie le grec 🥙</div>
</div>""")


def soir():
    return page(f"""<div class='pad'>
 <div class='tag'>22 H · LE MOMENT À RISQUE</div>
 <div class='t' style='margin-top:40px;font-size:120px'>Soirée<br><em>difficile ?</em></div>
 <div style='margin-top:60px;font:400 64px/1.25 Anton;text-transform:uppercase'>
  <div>1. Tel au salon</div><div>2. Sors de la pièce</div><div style='color:{OR}'>3. 10 pompes</div></div>
 <div class='zone' style='height:280px;margin-top:70px'>CURSEUR 🔥 OU QUESTION ICI</div>
 <div class='main' style='margin-top:40px'>l'envie, c'est une vague. elle passe.</div>
</div>""")


def a_vous():
    return page(f"""<div class='pad'>
 <div class='tag'>STICKER « À VOUS »</div>
 <div class='t' style='margin-top:40px;font-size:110px'>Montre<br>que tu <em>tiens</em></div>
 <div style='margin-top:40px;font-size:40px;max-width:820px'>Poste ta story avec le sticker, écris ton jour, et passe le relais.</div>
 <div class='zone' style='height:420px;margin-top:80px'>STICKER « À VOUS » : NNN, JOUR X 💪</div>
 <div class='main' style='margin-top:50px'>le mois où c'est toi qui décides.</div>
</div>""", fond=ENCRE)


def build():
    from playwright.sync_api import sync_playwright
    vis = {f"checkin-jour-{j:02d}": checkin(j) for j in range(1, 31)}
    vis |= {"guide-couverture": guide("_pdf_p1.png", "Le plan pour tenir<br><em>les 30 jours</em>", "Jour 0, un réflexe par jour, plan d'urgence, calendrier."),
            "guide-urgence": guide("_pdf_p8.png", "Ton plan<br><em>d'urgence</em>", "Quand l'envie monte : 6 étapes, sans réfléchir."),
            "guide-calendrier": guide("_pdf_p10.png", "30 cases.<br><em>une croix par soir.</em>", "Imprime-le, colle-le près de ton lit."),
            "envoie-a-ton-pote": pote(), "soir-22h": soir(), "a-vous": a_vous()}
    with sync_playwright() as p:
        b = p.chromium.launch(**K.chromium_args()); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for nom, h in vis.items():
            pg.set_content(h); pg.wait_for_timeout(150)
            pg.screenshot(path=os.path.join(DOS, nom + ".png"))
        b.close()
    return len(vis)


if __name__ == "__main__":
    print(build(), "stories dans", DOS)
