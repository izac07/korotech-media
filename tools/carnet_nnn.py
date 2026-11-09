#!/usr/bin/env python3
"""PDF « Tenir le NNN » (Mental d'Acier, novembre 2026) en mise en page « carnet de bord » : papier crème, encre noire,
or des reels MDA, titres Anton, annotations manuscrites (Caveat). Le fond vient de ressources/mentaldacier/contenu-nnn.json.
Usage : python3 tools/carnet_nnn.py   (écrit ressources/mentaldacier/plan-30-jours-tenir-le-nnn.pdf)
        python3 tools/carnet_nnn.py --br   (version « 30 jours sans la BR », sans NNN ni dates, depuis contenu-br.json,
        écrit ressources/mentaldacier/plan-30-jours-sans-la-br.pdf ; ligne éditoriale du 07/11)"""
import json, os, re, sys, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

RAC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(RAC, "ressources", "mentaldacier", "contenu-nnn.json")
OUT = os.path.join(RAC, "ressources", "mentaldacier", "plan-30-jours-tenir-le-nnn.pdf")
OR, ENCRE, PAPIER = "#d9a441", "#141414", "#f1ece2"
# textes fixes de la mise en page : version NNN (novembre) et version générale « 30 jours sans la BR »
TXT = {"tag": "@MENTALDACIER2030 · CARNET GRATUIT · NOVEMBRE", "big": "NNN", "t1": "Le plan pour tenir<br><span>les 30 jours</span>",
       "pied": "TENIR LE NNN", "engage": "je tiens le NNN<br>du 1<sup>er</sup> au 30 novembre.",
       "recu": "Tu as reçu ce carnet en commentant NNN. Partage-le à un pote qui fait le mois avec toi.", "tenir": True}
if "--br" in sys.argv:
    SRC = os.path.join(RAC, "ressources", "mentaldacier", "contenu-br.json")
    OUT = os.path.join(RAC, "ressources", "mentaldacier", "plan-30-jours-sans-la-br.pdf")
    TXT = {"tag": "@MENTALDACIER2030 · CARNET GRATUIT", "big": "30", "t1": "Jours sans la BR<br><span>le plan pour tenir</span>",
           "pied": "30 JOURS SANS LA BR", "engage": "je tiens<br>30 jours sans la BR, du <span class='ln' style='width:30mm'></span><br>au <span class='ln' style='width:30mm'></span>.",
           "recu": "Partage ce carnet à un pote qui veut reprendre le contrôle avec toi.", "tenir": True}
# Page « Tenir » (les deux versions depuis le 09/11) : ouverture du 16/11, offre fondateur réelle (50 places), liste d'attente.
# Un lien par carnet pour savoir lequel amène des inscrits : ?src=pdf-nnn (carnet NNN) et ?src=pdf (carnet BR).
# À réécrire après l'ouverture (le 16/11, la liste d'attente devient l'inscription).
LIEN_TENIR = "https://tenirapp.com/?src=pdf" if "--br" in sys.argv else "https://tenirapp.com/?src=pdf-nnn"


def r(s):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", H.escape(s))


def bloc(c, h):
    i = [k for k, b in enumerate(c["blocs"]) if b.get("h", "").startswith(h)][0]
    return c["blocs"][i + 1:]


def premier(c, h, cle):
    return next(b[cle] for b in bloc(c, h) if cle in b)


def page(c):
    jour0 = premier(c, "Jour 0", "etapes")
    semaines = premier(c, "Les 4 semaines", "tableau")["lignes"]
    jours = premier(c, "Ton réflexe du jour", "etapes")
    urgence = premier(c, "Le plan d'urgence", "etapes")
    declic = premier(c, "Tes déclencheurs", "tableau")["lignes"]
    craque = premier(c, "Si tu craques", "ul")
    phrases = premier(c, "Les phrases", "ul")
    intro = r(c["intro"])
    noms = ["LE DÉMARRAGE", "LA TENTATION", "LE MILIEU", "LA LIGNE D'ARRIVÉE"]
    mains = ["à faire ce soir, pas demain", "moins c'est facile, moins tu craques", "relis tes règles du jour 0", "garde la même routine jusqu'au bout"]

    def carte(e):
        t = re.sub(r"^Jour \d+\s*—\s*", "", e["t"])
        return (f"<div class='jr'><div class='jn'>{int(e['num']):02d}</div><div class='jc'><div class='jt'>{r(t)}</div>"
                f"<div class='jd'>{r(e['d'])}</div></div><div class='ck'></div></div>")

    sem_html = ""
    for k, (lo, hi) in enumerate([(1, 7), (8, 14), (15, 21), (22, 30)]):
        sem = semaines[k]
        sem_html += (f"<section class='sem'><div class='bande'><span class='sn'>SEMAINE {k + 1}</span><span class='sl'>{noms[k]}</span>"
                     f"<span class='sj'>JOURS {lo:02d} → {hi:02d}</span></div>"
                     f"<div class='sinfo'><p><span class='lab'>Ce qui t'attend</span>{r(sem[1])}</p><p><span class='lab'>Ton focus</span>{r(sem[2])}</p>"
                     f"<div class='main'>{mains[k]}</div></div>"
                     f"<div class='grille'>{''.join(carte(e) for e in jours if lo <= int(e['num']) <= hi)}</div></section>")

    secs = [x + "</section>" for x in sem_html.split("</section>")[:4]]
    j0 = "".join(f"<div class='j0'><div class='j0l'>{e['num']}</div><div><div class='j0t'>{r(e['t'])}</div><div class='j0d'>{r(e['d'])}</div>"
                 + (f"<div class='mini'>version rapide : {r(e['facile'])}</div>" if e.get('facile') else "") + "</div></div>" for e in jour0)
    urg = "".join(f"<div class='u'><div class='un'>{i}</div><div><div class='ut'>{r(e['t'])}</div><div class='ud'>{r(e['d'])}</div></div></div>"
                  for i, e in enumerate(urgence, 1))
    dec = "".join(f"<div class='dc'><div class='dk'>{r(l[0])}</div><div class='dw'>{r(l[1])}</div><div class='da'><span>alors →</span> {r(l[2])}</div></div>" for l in declic)
    cr = "".join(f"<li>{r(x)}</li>" for x in craque)
    ph = "".join(f"<div class='ph'>{r(x.strip('«» '))}</div>" for x in phrases)
    cases = "".join(f"<div class='cs'><span>{d}</span></div>" for d in range(1, 31))
    lignes = "".join(f"<div class='li'><span>{d:02d}</span></div>" for d in range(1, 31))
    traits = "".join("<i></i>" for _ in range(30))
    tenir = page_tenir() if TXT.get("tenir") else ""
    fonts = K._font_faces(["Anton", "Caveat", "Space Grotesk", "JetBrains Mono"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}
body{{margin:0;font:500 9.6pt/1.5 'Space Grotesk',sans-serif;color:{ENCRE};background:{PAPIER}}}
b{{font-weight:700}}
.pg{{width:210mm;height:297mm;padding:15mm 15mm 13mm;position:relative;overflow:hidden;break-after:page;background:{PAPIER}}}
.pg.noir{{background:{ENCRE};color:#ece6da}}
.pied{{position:absolute;left:15mm;right:15mm;bottom:8mm;display:flex;justify-content:space-between;font:400 7pt 'JetBrains Mono';letter-spacing:1px;opacity:.55}}
.lab{{display:block;font:400 7pt 'JetBrains Mono';letter-spacing:1.5px;text-transform:uppercase;opacity:.6;margin-bottom:2px}}
.main{{font:700 15pt/1.1 Caveat;color:{OR};transform:rotate(-2deg)}}
h2{{font:400 34pt/.95 Anton;text-transform:uppercase;margin:0 0 4mm;letter-spacing:.5px}}
h2 em{{font-style:normal;color:{OR}}}
.chap{{font:400 7.5pt 'JetBrains Mono';letter-spacing:2px;opacity:.6;margin-bottom:2mm}}
/* couverture */
.cv{{display:flex;flex-direction:column;height:100%}}
.cv .tag{{font:400 8pt 'JetBrains Mono';letter-spacing:2px;color:{OR}}}
.cv .big{{font:400 168pt/.8 Anton;letter-spacing:-2px;margin:14mm 0 0;color:transparent;-webkit-text-stroke:2px #ece6da}}
.cv .t1{{font:400 44pt/.95 Anton;text-transform:uppercase;margin-top:6mm}}
.cv .t1 span{{color:{OR}}}
.cv .tally{{display:flex;gap:2.2mm;margin:9mm 0 5mm}}
.cv .tally i{{display:block;width:2.4mm;height:13mm;background:#ece6da;opacity:.9;border-radius:1px}}
.cv .tally i:nth-child(5n){{transform:rotate(-58deg) translate(-2mm,-1mm);background:{OR};width:2mm;margin-left:-6.5mm}}
.cv .st{{font-size:11pt;max-width:135mm;opacity:.85}}
.cv .sig{{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end}}
.cv .sig .m{{font:700 22pt Caveat;color:{OR}}}
.cv .sig .h{{font:400 8pt 'JetBrains Mono';letter-spacing:1.5px;text-align:right;opacity:.7}}
/* intro */
.lead{{font:500 12.5pt/1.5 'Space Grotesk';max-width:160mm;margin-bottom:7mm}}
.lead b{{background:linear-gradient(transparent 58%,{OR}88 58%)}}
.mode{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5mm;margin:6mm 0 9mm}}
.mode div{{border-top:3px solid {ENCRE};padding-top:3mm}}
.mode .n{{font:400 26pt Anton}}
.j0{{display:grid;grid-template-columns:12mm 1fr;gap:3mm;padding:3.2mm 0;border-bottom:1px dashed #14141455}}
.j0l{{font:400 22pt/1 Anton;color:{OR}}}
.j0t{{font-weight:700;font-size:10.8pt;margin-bottom:.8mm}}
.mini{{font:700 12.5pt/1.1 Caveat;color:#7a5a1c;margin-top:1mm}}
.regle{{margin-top:6mm;background:{ENCRE};color:#ece6da;padding:5mm 6mm;font:400 14pt/1.15 Anton;text-transform:uppercase;letter-spacing:.5px}}
.regle span{{color:{OR}}}
/* semaines */
.sem{{margin-bottom:5mm}}
.bande{{display:flex;align-items:baseline;gap:4mm;background:{ENCRE};color:#ece6da;padding:2.6mm 4mm}}
.sn{{font:400 8pt 'JetBrains Mono';letter-spacing:2px;color:{OR}}}
.sl{{font:400 19pt/1 Anton;text-transform:uppercase}}
.sj{{margin-left:auto;font:400 7.5pt 'JetBrains Mono';letter-spacing:1px;opacity:.7}}
.sinfo{{display:grid;grid-template-columns:1fr 1fr 44mm;gap:5mm;padding:3mm 0 2mm;align-items:center}}
.sinfo p{{margin:0;font-size:9pt}}
.grille{{display:grid;grid-template-columns:1fr 1fr;gap:2.4mm}}
.jr{{display:grid;grid-template-columns:14mm 1fr 6mm;gap:2.5mm;background:#fbf8f2;border:1px solid #14141426;padding:3.6mm 3.4mm;break-inside:avoid}}
.jn{{font:400 28pt/1 Anton;color:{OR}}}
.jt{{font-weight:700;font-size:10pt;margin-bottom:.6mm;text-transform:uppercase;letter-spacing:.2px}}
.jd{{font-size:9.2pt;line-height:1.45}}
.ck{{width:5mm;height:5mm;border:1.5px solid {ENCRE};margin-top:1mm}}
/* urgence */
.u{{display:grid;grid-template-columns:22mm 1fr;gap:4mm;padding:4mm 0;border-bottom:1px solid #ece6da2e}}
.un{{font:400 46pt/.85 Anton;color:{OR}}}
.ut{{font:400 17pt/1.05 Anton;text-transform:uppercase;margin-bottom:1.2mm}}
.ud{{font-size:10pt;opacity:.85}}
.capt{{font:700 16pt Caveat;color:{OR};margin:-2mm 0 4mm}}
/* déclencheurs */
.dc{{display:grid;grid-template-columns:38mm 1fr 1fr;gap:4mm;padding:3.4mm 0;border-bottom:1px dashed #14141455;font-size:9.2pt}}
.dk{{font:400 14pt/1.05 Anton;text-transform:uppercase}}
.dw{{opacity:.75}}
.da span{{font:700 13pt Caveat;color:#a2741f}}
ul.cr{{margin:2mm 0 0;padding:0;list-style:none;counter-reset:c}}
ul.cr li{{counter-increment:c;padding:2.4mm 0 2.4mm 11mm;position:relative;border-bottom:1px dashed #14141433}}
ul.cr li:before{{content:counter(c);position:absolute;left:0;top:1.4mm;font:400 17pt Anton;color:{OR}}}
.ph{{font:400 18pt/1.1 Anton;text-transform:uppercase;padding:2.2mm 0;border-bottom:1px solid #14141420}}
.ph:nth-child(odd){{color:#a2741f}}
.deux{{display:grid;grid-template-columns:1fr 1fr;gap:9mm}}
/* calendrier */
.cal{{display:grid;grid-template-columns:repeat(6,1fr);gap:2.6mm;margin:4mm 0 7mm}}
.cs{{height:21mm;border:2px solid {ENCRE};position:relative;background:#fbf8f2}}
.cs span{{position:absolute;top:1.2mm;left:1.8mm;font:400 12pt Anton}}
.notes{{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(15,auto);grid-auto-flow:column;column-gap:8mm}}
.li{{border-bottom:1px solid #14141440;height:5.6mm;font:400 7pt 'JetBrains Mono';display:flex;align-items:flex-end;padding-bottom:.6mm;opacity:.8}}
.contrat{{margin-top:10mm;border:2px solid {ENCRE};padding:6mm 7mm;background:#fbf8f2}}
.ct{{font:400 21pt/1.25 Anton;text-transform:uppercase;margin:2mm 0 5mm}}
.ct2{{font-size:10.5pt;margin:4mm 0}}
.ln{{display:inline-block;border-bottom:1.5px solid {ENCRE};height:5mm;vertical-align:bottom}}
.fin{{margin-top:6mm;font-size:9.4pt}}
.fin .m{{font:700 17pt Caveat;color:#a2741f}}
/* page Tenir */
.tn{{display:grid;grid-template-columns:44mm 44mm 1fr;gap:6mm;margin:5mm 0 7mm;align-items:start}}
.tcap img{{display:block;width:100%;border:2px solid #2e2e33;border-radius:5mm}}
.tcap span{{display:block;font:700 13pt/1.1 Caveat;color:{OR};margin-top:2mm;text-align:center}}
.tl{{padding:3mm 0;border-bottom:1px solid #ece6da2e;font-size:10.5pt}}
.tl b{{font:400 19pt/1 Anton;color:{OR};margin-right:1.5mm}}
.tcta{{display:block;background:{OR};color:{ENCRE};padding:5mm 7mm;text-decoration:none}}
.tu{{display:block;font:400 34pt/1 Anton;text-transform:uppercase;margin:1.5mm 0 2mm}}
.td{{display:block;font-size:10.5pt}}
</style></head><body>

<div class='pg noir'><div class='cv'>
 <div class='tag'>{TXT['tag']}</div>
 <div class='big'>{TXT['big']}</div>
 <div class='t1'>{TXT['t1']}</div>
 <div class='tally'>{traits}</div>
 <div class='st'>{r(c['sous_titre'])}</div>
 <div class='sig'><div class='m'>un jour à la fois.</div><div class='h'>30 JOURS<br>1 CHAMBRE PRÉPARÉE<br>0 EXCUSE</div></div>
</div></div>

<div class='pg'>
 <div class='chap'>00 · AVANT DE COMMENCER</div>
 <h2>Pourquoi la plupart <em>lâchent</em></h2>
 <div class='lead'>{intro}</div>
 <div class='mode'>
  <div><div class='n'>01</div>Tu rends la tentation <b>difficile d'accès</b>.</div>
  <div><div class='n'>02</div>Tu as <b>un réflexe prêt</b> pour chaque moment à risque.</div>
  <div><div class='n'>03</div>Tu <b>suis ta série</b>, une croix par soir.</div>
 </div>
 <div class='contrat'>
  <div class='chap'>TON ENGAGEMENT</div>
  <div class='ct'>Moi, <span class='ln' style='width:62mm'></span>, {TXT['engage']}</div>
  <div class='ct2'>Mon pourquoi : <span class='ln' style='width:128mm'></span></div>
  <div class='ct2'>Mon pote de confiance : <span class='ln' style='width:60mm'></span> &nbsp; Signé : <span class='ln' style='width:40mm'></span></div>
  <div class='main' style='margin-top:4mm'>écris-le pour de vrai. ça change tout.</div>
 </div>
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>

<div class='pg'>
 <div class='chap'>00 · JOUR 0</div>
 <h2>Jour 0 : <em>prépare le terrain</em></h2>
 <div class='main' style='margin:-2mm 0 2mm'>à faire avant ce soir</div>
 {j0}
 <div class='regle'>Ne compte pas sur ta volonté à 1 h du matin. <span>Compte sur ce que tu as préparé à 18 h.</span></div>
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>

<div class='pg'>
 <div class='chap'>01 · LE MOIS, JOUR PAR JOUR</div>
 <h2>Un réflexe <em>par jour</em></h2>
 <p style='margin:0 0 4mm;max-width:165mm'>Chaque matin, lis ton jour : une action de 5 à 15 minutes. Tu as raté un jour ? Fais-le le lendemain, le plan continue. Coche la case quand c'est fait.</p>
 {secs[0]}
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>
{''.join(f"<div class='pg'>{x}<div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div></div>" for x in secs[1:])}

<div class='pg noir'>
 <div class='chap' style='color:{OR};opacity:1'>02 · PLAN D'URGENCE</div>
 <h2>L'envie <em>monte.</em><br>Tu fais ça.</h2>
 <div class='capt'>fais une capture de cette page, garde-la sur ton tel</div>
 {urg}
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>

<div class='pg'>
 <div class='chap'>03 · TES DÉCLENCHEURS</div>
 <h2>Si ça arrive, <em>alors</em> tu fais ça</h2>
 {dec}
 <div class='deux' style='margin-top:8mm'>
  <div><div class='chap'>04 · SI TU CRAQUES</div><h2 style='font-size:24pt'>Ça peut <em>arriver</em></h2>
   <p style='margin:0'>Ce qui compte, c'est ce que tu fais juste après.</p><ul class='cr'>{cr}</ul>
   <div class='main' style='margin-top:4mm'>26 jours sur 30, c'est une victoire.</div></div>
  <div><div class='chap'>05 · À GARDER EN TÊTE</div>{ph}</div>
 </div>
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>

{tenir}
<div class='pg'>
 <div class='chap'>06 · TA SÉRIE</div>
 <h2>Une croix <em>par soir</em></h2>
 <div class='main' style='margin:-2mm 0 1mm'>et tu ne casses pas la série.</div>
 <div class='cal'>{cases}</div>
 <div class='chap'>CE QUI M'A AIDÉ / CE QUI A ÉTÉ DUR</div>
 <div class='notes'>{lignes}</div>
 <div class='fin'>{r(c['fin'])}<br><span class='m'>{TXT['recu']}</span></div>
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>
</body></html>"""


def page_tenir():
    """Page sombre : le carnet en version app, captures réelles de Tenir, lien cliquable vers la liste d'attente."""
    import base64
    cap = os.path.join(RAC, "ressources", "mentaldacier", "app-captures")
    def img(n):
        b = base64.b64encode(open(os.path.join(cap, n), "rb").read()).decode()
        return f"<img src='data:image/png;base64,{b}'>"
    return f"""<div class='pg noir'>
 <div class='chap' style='color:{OR};opacity:1'>07 · TENIR, L'APP</div>
 <h2>Ce carnet,<br><em>dans ta poche.</em></h2>
 <div class='lead' style='color:#ece6da;max-width:170mm'>Le <b style='background:none;color:{OR}'>16 novembre</b>, j'ouvre <b style='background:none;color:{OR}'>Tenir</b> : l'app qui fait ce carnet avec toi, chaque jour. Ta mission du matin, ta série, tes heures à risque, et un bouton rouge pour les soirs où ça chauffe.</div>
 <div class='tn'>
  <div class='tcap'>{img("1_aujourdhui.png")}<span>ta mission du jour</span></div>
  <div class='tcap'>{img("2_serie.png")}<span>ta série, tes heures à risque</span></div>
  <div class='tinfo'>
   <div class='tl'><span class='lab'>Membre fondateur</span><b>9,99 €/mois,</b> bloqué à vie</div>
   <div class='tl'><span class='lab'>Offre fondateur</span><b>50</b> places, pas une de plus</div>
   <div class='tl'><span class='lab'>Discrétion</span>Pas de pseudo, rien de public. Personne ne sait que tu l'utilises.</div>
  </div>
 </div>
 <a class='tcta' href='{LIEN_TENIR}'>
  <span class='lab' style='color:{ENCRE};opacity:.7'>Liste d'attente · 2 minutes, ton mail, c'est tout</span>
  <span class='tu'>tenirapp.com</span>
  <span class='td'>Le 16, tu reçois l'accès avant tout le monde, et le prix fondateur avant que les places partent.</span>
 </a>
 <div class='main' style='margin-top:4mm'>clique, ou tape l'adresse dans ton navigateur · 18 ans et plus</div>
 <div class='pied'><span>{TXT['pied']}</span><span>@MENTALDACIER2030</span></div>
</div>"""


def build():
    c = json.load(open(SRC, encoding="utf-8"))
    hp = os.path.join(os.path.dirname(OUT), "_carnet.html")
    open(hp, "w", encoding="utf-8").write(page(c))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(**K.chromium_args()); pg = b.new_page()
        pg.goto("file://" + hp); pg.wait_for_timeout(500)
        pg.pdf(path=OUT, format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    os.remove(hp)
    return OUT


if __name__ == "__main__":
    print(build())
