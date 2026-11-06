#!/usr/bin/env python3
"""Stories « lancement de Tenir » (Mental d'Acier, 06/11/2026) : la suite des stories « on construit l'app ensemble »
(02/11). Annonce, 3 écrans de l'app (captures réelles), ouverture du 16/11 + prix fondateur, liste d'attente.
Même charte que tools/stories_nnn.py ; zones vides pour les stickers Instagram (compte à rebours, lien, sondage).
Positionnement validé : « reprendre le contrôle », jamais « addiction », 18+ partout, rien d'explicite.
Usage : py -3.13 tools/stories_lancement.py   (écrit ressources/mentaldacier/stories/lancement-*.png)"""
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K
from stories_nnn import page, DOS, OR

CAP = os.path.join(os.path.dirname(DOS), "app-captures")


def capture(nom, largeur=600):
    """Capture réelle de l'app dans un cadre de téléphone sobre."""
    b64 = base64.b64encode(open(os.path.join(CAP, nom), "rb").read()).decode()
    return (f"<div style='margin:56px auto 0;width:{largeur}px;border:3px solid #2e2e33;border-radius:46px;overflow:hidden;"
            f"box-shadow:0 30px 80px rgba(0,0,0,.6)'><img src='data:image/png;base64,{b64}' style='display:block;width:100%'></div>")


def bloc(tag, titre, texte="", apres="", taille=104):
    t = f"<div style='margin-top:40px;font-size:42px;line-height:1.45;max-width:900px'>{texte}</div>" if texte else ""
    return page(f"""<div class='pad'>
 <div class='tag'>{tag}</div>
 <div class='t' style='margin-top:44px;font-size:{taille}px'>{titre}</div>
 {t}{apres}
</div>""")


VIS = {
 "lancement-1-annonce": bloc("ANNONCE", "Elle<br><em>arrive.</em>",
     "Depuis le début du NNN, je vous file un plan par jour en vidéo.<br><br>Alors j'ai construit l'app qui va avec. Elle s'appelle <b>Tenir</b>.",
     "<div class='main' style='margin-top:70px'>ça se passe dans les stories suivantes 👉</div>", taille=150),
 "lancement-2-mission": bloc("TENIR · 1/3", "Ta mission<br><em>du jour.</em>",
     "Chaque matin, un truc concret à faire. 5 à 15 minutes. Rien à réfléchir.", capture("1_aujourdhui.png", 560), taille=96),
 "lancement-3-serie": bloc("TENIR · 2/3", "Ta série.<br><em>Tes heures à risque.</em>",
     "Une croix par soir. Et l'app te montre quand et où tu craques, pour que tu le voies venir.", capture("2_serie.png", 560), taille=96),
 "lancement-4-chauffe": bloc("TENIR · 3/3", "Quand ça<br><em>chauffe.</em>",
     "Un bouton rouge. 6 étapes, un timer, zéro réflexion. Pour les soirs où la volonté suffit plus.", capture("3_ca_chauffe.png", 560), taille=96),
 "lancement-5-ouverture": bloc("OUVERTURE", "Le 16<br><em>novembre.</em>",
     "<b>Membre fondateur : 9,99 €/mois, bloqué à vie.</b><br><br>Tout est privé : pas de pseudo, rien de public, personne sait que tu l'utilises.",
     f"<div style='margin-top:44px;display:flex;align-items:center;gap:30px'><div style='font:400 190px/1 Anton;color:{OR}'>50</div>"
     "<div style='font:400 64px/1.05 Anton;text-transform:uppercase'>places<br>seulement</div></div>"
     "<div class='zone' style='height:280px;margin-top:40px'></div>", taille=150),
 "lancement-6-liste": page(f"""<div class='pad'>
 <div class='tag'>LISTE D'ATTENTE</div>
 <div class='t' style='margin-top:44px;font-size:110px'>Sois prévenu<br><em>en premier.</em></div>
 <div style='margin-top:40px;font-size:42px;line-height:1.45;max-width:900px'>Inscris-toi sur la liste : le 16, tu reçois l'accès avant tout le monde, et le prix fondateur avant que les places partent.</div>
 <div class='zone' style='height:260px;margin-top:60px'></div>
 <div style='position:absolute;left:0;right:0;bottom:90px;text-align:center'>
  <div class='main'>clique sur le lien 👆 · 18 ans et plus</div>
 </div>
</div>"""),
}

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**K.chromium_args()); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for nom, h in VIS.items():
            pg.set_content(h); pg.wait_for_timeout(250); pg.screenshot(path=os.path.join(DOS, nom + ".png"))
        b.close()
    print(len(VIS), "stories dans", DOS)
