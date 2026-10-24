#!/usr/bin/env python3
"""Audit visuel d'un reel motion, sans rendre la vidéo.

Usage : python3 tools/audit.py <dossier>/motion.json [--estime] [--planche fichier.jpg]
  --estime  : durées estimées depuis le nombre de mots (à utiliser AVANT de générer les voix)
  --planche : enregistre une planche des instants contrôlés (à regarder avec l'outil Read)
Lancé aussi automatiquement par tools/motion.py avant chaque rendu (avertit, ne bloque pas).

Contrôles, à chaque instant (début / milieu / fin de chaque scène) :
- texte de moins de 30 px ;
- texte dans les zones masquées par Instagram : 200 px du haut (barre « Reels »), sous y = 1500 (pseudo, légende),
  colonne de droite x > 960 entre y = 1000 et 1750 (boutons j'aime / commentaire / partage) ;
- texte qui sort de l'écran ;
- hook : premier instant où un texte est lisible (taille >= 48 px, opacité >= 0,5, dans l'écran) — cible <= 0,5 s.
Les sous-titres (classe .cap) sont contrôlés à part : ils peuvent chevaucher le contenu, pas les zones masquées.
"""
import os, sys, json, subprocess, tempfile, shutil

HAUT, BAS, BORD, PETIT = 200, 1500, 20, 30  # < 30 px : illisible sur téléphone (les « chromes » d'interface type heure/batterie font 30-38 px)
COL_X, COL_Y0, COL_Y1 = 960, 1000, 1750
HOOK_MAX = 0.5

JS = r"""(args) => {
  const [HAUT, BAS, BORD, PETIT, COL_X, COL_Y0, COL_Y1] = args;
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const vus = new Set();
  while (w.nextNode()) {
    const n = w.currentNode; if (!n.nodeValue.trim()) continue;
    const e = n.parentElement; if (!e || vus.has(e) || e.closest('script,style')) continue; vus.add(e);
    let op = 1, cache = false;
    for (let p = e; p && p !== document.documentElement; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.display === 'none' || cs.visibility === 'hidden') { cache = true; break; }
      op *= parseFloat(cs.opacity);
    }
    if (cache || op < 0.5) continue;
    const r = document.createRange(); r.selectNodeContents(n); const b = r.getBoundingClientRect();
    if (b.width < 2 || b.height < 2) continue;
    const fs = parseFloat(getComputedStyle(e).fontSize);
    const txt = n.nodeValue.trim().slice(0, 40);
    const cap = !!e.closest('.cap,.capw,.caps,[class*=cap]');
    out.push({txt, fs, l: b.left, r: b.right, t: b.top, b: b.bottom, cap});
  }
  return out;
}"""


def instants(starts, total):
    pts = []
    ends = starts[1:] + [total]
    for a, b in zip(starts, ends):
        pts += [a + 0.15, (a + b) / 2, max(a, b - 0.45)]
    return sorted(set(round(t, 2) for t in pts if t < total))


def auditer(html_path, starts, total, planche=None):
    """Renvoie {"problemes": [...], "hook": seconde ou None}."""
    from playwright.sync_api import sync_playwright
    pb, hook = [], None
    tmp = tempfile.mkdtemp() if planche else None
    with sync_playwright() as p:
        gl = "WebGLRenderer" in open(html_path, encoding="utf-8").read()
        kw = {"args": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]} if gl else {}
        if os.environ.get("PW_CHROMIUM"):
            kw["executable_path"] = os.environ["PW_CHROMIUM"]  # Chromium préinstallé (voir tools/setup.sh)
        b = p.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto("file://" + os.path.abspath(html_path)); pg.wait_for_function("typeof window.render==='function'", timeout=120000); pg.wait_for_timeout(300)
        args = [HAUT, BAS, BORD, PETIT, COL_X, COL_Y0, COL_Y1]
        # hook : premier instant avec un texte lisible (hors sous-titres)
        t = 0.0
        while t <= min(3.0, (starts[1] if len(starts) > 1 else total)):
            pg.evaluate("t => render(t)", t)
            if any((not x["cap"]) and x["fs"] >= 48 and 0 <= x["t"] < 1920 and 0 <= x["l"] < 1080 for x in pg.evaluate(JS, args)):
                hook = round(t, 1); break
            t += 0.1
        for i, t in enumerate(instants(starts, total)):
            pg.evaluate("t => render(t)", t)
            for x in pg.evaluate(JS, args):
                if x["t"] > 1920 or x["b"] < 0 or x["l"] > 1080 or x["r"] < 0:
                    continue  # entièrement hors écran : élément pas encore entré (invisible)
                if x["r"] - x["l"] > 1080:
                    continue  # bandeau défilant plus large que l'écran (voulu)
                ou = "%.1f s « %s »" % (t, "sous-titres" if x["cap"] else x["txt"])
                if x["fs"] < PETIT:
                    pb.append(("petit", "texte de %d px (min %d) : %s" % (x["fs"], PETIT, ou)))
                if x["l"] < -BORD or x["r"] > 1080 + BORD:
                    pb.append(("ecran", "texte coupé par le bord de l'écran (x %d-%d) : %s" % (x["l"], x["r"], ou)))
                if x["t"] < HAUT and x["fs"] >= 40:
                    pb.append(("haut", "texte sous la barre du haut d'Instagram (y %d < %d) : %s" % (x["t"], HAUT, ou)))
                if x["b"] > BAS:
                    pb.append(("bas", "texte dans la zone du pseudo/légende (y %d > %d) : %s" % (x["b"], BAS, ou)))
                if x["r"] > COL_X and x["b"] > COL_Y0 and x["t"] < COL_Y1:
                    pb.append(("droite", "texte sous les boutons d'Instagram (x %d > %d) : %s" % (x["r"], COL_X, ou)))
            if tmp:
                pg.screenshot(path=os.path.join(tmp, "a_%02d.jpg" % i), type="jpeg", quality=70)
        b.close()
    if tmp:
        n = len(os.listdir(tmp))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "a_%02d.jpg"),
                        "-vf", "scale=270:480,tile=5x%d" % ((n + 4) // 5), "-frames:v", "1", planche], check=True)
        shutil.rmtree(tmp)
    # dédoublonnage : un même problème (même type, même texte) n'est listé qu'une fois, avec le nombre d'instants
    compte, ordre = {}, []
    for k, m in pb:
        cle = (k, m.split("« ")[-1])
        if cle not in compte:
            compte[cle] = [m, 0]; ordre.append(cle)
        compte[cle][1] += 1
    uniq = [compte[c][0] + (" (x%d instants)" % compte[c][1] if compte[c][1] > 1 else "") for c in ordre]
    return {"problemes": uniq, "hook": hook}


def afficher(res, nom=""):
    h = res["hook"]
    lignes = []
    if h is None:
        lignes.append("ATTENTION hook : aucun texte lisible pendant les 3 premières secondes")
    elif h > HOOK_MAX:
        lignes.append("ATTENTION hook : premier texte lisible à %.1f s (cible <= %.1f s, sinon le pouce passe)" % (h, HOOK_MAX))
    lignes += ["ATTENTION " + m for m in res["problemes"]]
    print("audit %s : %s" % (nom, "OK (hook lisible à %.1f s)" % h if not lignes else "%d point(s)" % len(lignes)))
    for l in lignes:
        print("  " + l)
    return lignes


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import motion as M
    spec_path = sys.argv[1]
    planche = sys.argv[sys.argv.index("--planche") + 1] if "--planche" in sys.argv else None
    tmp = tempfile.mkdtemp()
    try:
        spec, page, hp, starts, durs, total, voice = M.prepare(spec_path, tmp, estime="--estime" in sys.argv)
        lignes = afficher(auditer(hp, starts, total, planche), spec_path)
        if planche:
            print("planche :", planche)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if lignes else 0)
