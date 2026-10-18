#!/usr/bin/env python3
"""Journal structuré des reels (tous les comptes) : journal-reels.csv à la racine du dépôt.

Colonnes : date;compte;id;layout;pilier;formule;sujet;hook   (séparateur « ; », date « AAAA-MM-JJ HH:MM »)
  pilier  = un pilier du README du compte (ex. « Études malin », « Coulisses du système »)
  formule = formule du hook, une de : FORMULES ci-dessous

Usage :
  python3 tools/journal.py ajouter <dossier>/motion.json --date "2026-10-20 12:15" --pilier "..." --formule question --sujet "..."
      ajoute la ligne au CSV ET au journal.md du compte (tableau lisible), refuse un id déjà présent
  python3 tools/journal.py verifier --compte korotech_fr [--date 2026-10-20] [--sujet "..."]
      2 reels du même jour trop proches (même pilier ET même formule, ou sujets qui se recoupent),
      ou sujet proposé déjà traité par le compte
  python3 tools/journal.py sujets --compte korotech_fr          liste des sujets déjà traités (à lire avant d'en choisir)
  python3 tools/journal.py reprendre                            (une fois) importe l'historique des journal.md
"""
import csv, json, os, re, sys, glob, unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(RACINE, "journal-reels.csv")
COLS = ["date", "compte", "id", "layout", "pilier", "formule", "sujet", "hook"]
FORMULES = ["pov", "question", "stop", "secret", "chiffre", "avant-apres", "mythe", "liste", "defi", "histoire", "demo", "erreur"]
# handle -> dossier du compte (journal.md lisible)
DOSSIERS = {"korotech_fr": "", "lia.entrepreneur": "comptes/lia-entrepreneur", "zerosallefit": "comptes/zerosallefit",
            "coeurlucide__": "comptes/coeurlucide", "mentaldacier2030": "comptes/mentaldacier", "revenus_malins": "comptes/revenus-malin"}
PREFIXES = {"LIA": "lia.entrepreneur", "ZSF": "zerosallefit", "CL": "coeurlucide__", "MDA": "mentaldacier2030", "RM": "revenus_malins"}
VIDES = {"le", "la", "les", "un", "une", "des", "de", "du", "ton", "ta", "tes", "ce", "ces", "pour", "avec", "sans", "qui", "que",
         "quoi", "dans", "sur", "pas", "plus", "est", "et", "ou", "en", "au", "aux", "ne", "se", "sa", "son", "par", "motion",
         "remplace", "carrousel", "carrousels", "reel", "reels", "comment", "fait", "faire", "quand", "tout", "tous"}


def lire():
    if not os.path.exists(FICHIER):
        return []
    with open(FICHIER, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def ecrire(lignes):
    with open(FICHIER, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter=";", lineterminator="\n")
        w.writeheader()
        for l in sorted(lignes, key=lambda x: (x["date"], x["compte"], x["id"])):
            w.writerow({k: l.get(k, "") for k in COLS})


def mots(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return {m for m in re.findall(r"[a-z0-9]+", s) if len(m) > 3 and m not in VIDES}


def proches(a, b):
    """Recoupement de deux sujets : part des mots significatifs communs (0 à 1)."""
    A, B = mots(a), mots(b)
    return len(A & B) / max(1, min(len(A), len(B))) if A and B else 0.0


def hook_de(spec):
    """Texte affiché par le hook (scène 0), selon le layout."""
    h = (spec.get("scenes") or [{}])[0]
    morceaux = [h.get(k, "") for k in ("big", "title", "unit", "line", "sub", "notif", "top", "cmd", "mark")]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", " ".join(str(m) for m in morceaux if m).replace("**", ""))).strip()


def ajouter(args):
    spec_path = args[0]
    opt = lambda k: args[args.index(k) + 1] if k in args else ""
    spec = json.load(open(spec_path, encoding="utf-8"))
    date, pilier, formule, sujet = opt("--date"), opt("--pilier"), opt("--formule").lower(), opt("--sujet")
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", date):
        sys.exit("--date au format « AAAA-MM-JJ HH:MM » obligatoire")
    if formule not in FORMULES:
        sys.exit("--formule doit être une de : " + ", ".join(FORMULES))
    if not pilier or not sujet:
        sys.exit("--pilier et --sujet obligatoires")
    lignes = lire()
    if any(l["id"] == spec["id"] for l in lignes):
        sys.exit("id %s déjà dans le journal" % spec["id"])
    ligne = {"date": date, "compte": spec.get("handle", ""), "id": spec["id"], "layout": spec.get("layout", ""),
             "pilier": pilier, "formule": formule, "sujet": sujet, "hook": hook_de(spec)}
    lignes.append(ligne); ecrire(lignes)
    # journal.md lisible du compte
    d = DOSSIERS.get(ligne["compte"])
    if d is not None:
        md = os.path.join(RACINE, d, "journal.md")
        if os.path.exists(md):
            txt = open(md, encoding="utf-8").read().rstrip("\n")
            cols = txt.splitlines()[2].count("|") - 1 if len(txt.splitlines()) > 2 else 4
            cell = [date, spec["id"], "Reel", "%s (%s, %s)" % (sujet, pilier, ligne["layout"])] + ["—"] * max(0, cols - 4)
            open(md, "w", encoding="utf-8").write(txt + "\n| " + " | ".join(cell) + " |\n")
    print("ajouté :", ";".join(ligne[k] for k in COLS))
    verifier(["--compte", ligne["compte"], "--date", date[:10]])


def verifier(args):
    opt = lambda k: args[args.index(k) + 1] if k in args else ""
    compte, jour, sujet = opt("--compte"), opt("--date"), opt("--sujet")
    lignes = [l for l in lire() if l["compte"] == compte]
    pb = []
    if sujet:
        for l in lignes:
            p = proches(sujet, l["sujet"])
            if p >= 0.5:
                pb.append("sujet proche d'un reel déjà fait (%d %%) : %s %s « %s »" % (p * 100, l["date"], l["id"], l["sujet"]))
    if jour:
        du_jour = [l for l in lignes if l["date"].startswith(jour)]
        for i in range(len(du_jour)):
            for j in range(i + 1, len(du_jour)):
                a, b = du_jour[i], du_jour[j]
                if a["pilier"] and a["pilier"] == b["pilier"] and a["formule"] and a["formule"] == b["formule"]:
                    pb.append("%s et %s le même jour : même pilier (%s) ET même formule de hook (%s)" % (a["id"], b["id"], a["pilier"], a["formule"]))
                if proches(a["sujet"], b["sujet"]) >= 0.5:
                    pb.append("%s et %s le même jour : sujets trop proches (« %s » / « %s »)" % (a["id"], b["id"], a["sujet"], b["sujet"]))
    print("variété @%s%s : %s" % (compte, " le " + jour if jour else "", "OK" if not pb else "%d point(s)" % len(pb)))
    for p in pb:
        print("  ATTENTION " + p)
    return pb


def sujets(args):
    compte = args[args.index("--compte") + 1]
    for l in lire():
        if l["compte"] == compte:
            print("%s  %-8s %-14s %-10s %s" % (l["date"], l["id"], l["pilier"] or "?", l["formule"] or "?", l["sujet"]))


def reprendre(args):
    """Importe les tableaux des journal.md (date | id | format | sujet ...) ; pilier/formule restent vides."""
    lignes = lire(); ids = {l["id"] for l in lignes}; n = 0
    for handle, d in DOSSIERS.items():
        md = os.path.join(RACINE, d, "journal.md")
        if not os.path.exists(md):
            continue
        for row in open(md, encoding="utf-8"):
            c = [x.strip() for x in row.strip().strip("|").split("|")]
            if len(c) < 4 or not re.match(r"^\d{4}-\d{2}-\d{2}", c[0]) or c[1] in ids:
                continue
            if not c[2].lower().startswith("reel") or "remplacé" in c[2].lower():
                continue  # seulement les reels réellement produits
            spec = glob.glob(os.path.join(RACINE, d, "posts", "*", "motion.json"))
            lay = ""
            for f in spec:
                try:
                    s = json.load(open(f, encoding="utf-8"))
                    if s.get("id") == c[1]: lay = s.get("layout", "")
                except Exception: pass
            lignes.append({"date": c[0][:16], "compte": handle, "id": c[1], "layout": lay, "pilier": "", "formule": "",
                           "sujet": re.sub(r"\s+—\s+motion.*$", "", c[3]), "hook": ""})
            ids.add(c[1]); n += 1
    ecrire(lignes)
    print("%d reels importés depuis les journal.md (pilier et formule à compléter si besoin)" % n)


if __name__ == "__main__":
    cmds = {"ajouter": ajouter, "verifier": verifier, "sujets": sujets, "reprendre": reprendre}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__); sys.exit(2)
    r = cmds[sys.argv[1]](sys.argv[2:])
    sys.exit(1 if isinstance(r, list) and r else 0)
