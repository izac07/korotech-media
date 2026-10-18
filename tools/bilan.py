#!/usr/bin/env python3
"""Bilan hebdomadaire, tous comptes : chaque reel mesuré en « x fois la médiane » de son compte.

Usage : python3 tools/bilan.py [--depuis 2026-10-14] [--ecrire]
  --ecrire : écrit stats/bilan-AAAA-MM-JJ.md (sinon affiche seulement)

Entrées :
- stats/*.csv déposés par le scénario Make 9975091. 1re ligne « abonnes;N;posts;M;date;AAAA-MM-JJ HH:mm[;compte;handle] ».
  Sans champ « compte », le fichier est celui de korotech_fr (format historique).
- journal-reels.csv (tools/journal.py) pour relier chaque reel à son pilier et à sa formule de hook
  (rapprochement par compte + heure de publication, à 45 min près).
Règles : aucun chiffre extrapolé ; médiane calculée sur les reels de plus de 3 jours (les récents montent encore) ;
on ne compare que les posts publiés depuis --depuis (nouvelle ligne éditoriale).
"""
import csv, glob, os, sys, statistics
from datetime import datetime, timedelta, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARIS = timezone(timedelta(hours=2))  # heure d'été ; l'écart d'1 h l'hiver reste dans la tolérance de rapprochement
METRIQUES = ["views", "reach", "saved", "shares", "likes", "comments"]


def lire_stats(path):
    with open(path, encoding="utf-8") as f:
        lignes = f.read().splitlines()
    tete = lignes[0].split(";")
    meta = {tete[i]: tete[i + 1] for i in range(0, len(tete) - 1, 2)}
    if meta.get("compte", "x").isdigit() or "date" not in meta:
        raise ValueError("en-tête invalide (fichier de test)")
    posts = {}
    for row in csv.reader(lignes[2:], delimiter=";"):
        if len(row) < 8:
            continue
        pid, date, typ, media, lien, leg, met, val = row[:8]
        p = posts.setdefault(pid, {"id": pid, "date": date, "type": typ, "media": media, "lien": lien, "legende": leg})
        try:
            p[met] = int(float(val))
        except ValueError:
            pass
    return {"compte": meta.get("compte", "korotech_fr"), "abonnes": int(meta.get("abonnes", 0) or 0),
            "date": meta.get("date", ""), "posts": list(posts.values()), "fichier": os.path.relpath(path, RACINE)}


def par_compte():
    """{compte: [stats triées du plus ancien au plus récent]}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(RACINE, "stats", "**", "*.csv"), recursive=True)):
        try:
            s = lire_stats(f)
        except Exception:
            continue
        out.setdefault(s["compte"], []).append(s)
    for c in out:
        out[c].sort(key=lambda s: s["date"])
    return out


def journal():
    f = os.path.join(RACINE, "journal-reels.csv")
    if not os.path.exists(f):
        return []
    with open(f, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def relier(post, compte, jr):
    """Ligne du journal publiée à la même heure (± 45 min) sur le même compte."""
    try:
        t = datetime.strptime(post["date"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    best, ecart = None, timedelta(minutes=45)
    for l in jr:
        if l["compte"] != compte:
            continue
        try:
            tj = datetime.strptime(l["date"], "%Y-%m-%d %H:%M").replace(tzinfo=PARIS)
        except ValueError:
            continue
        if abs(tj - t) <= ecart:
            best, ecart = l, abs(tj - t)
    return best


def bilan(depuis):
    jr = journal()
    maintenant = datetime.now(timezone.utc)
    md = ["# Bilan du %s" % maintenant.astimezone(PARIS).strftime("%Y-%m-%d"), ""]
    for compte, hist in sorted(par_compte().items()):
        der = hist[-1]; prec = hist[-2] if len(hist) > 1 else None
        reels = [p for p in der["posts"] if p["type"] == "REELS" and p["date"][:10] >= depuis and "views" in p]
        md += ["## @%s" % compte, "",
               "Fichier : `%s` (%s). Abonnés : %d%s." % (der["fichier"], der["date"], der["abonnes"],
                   " (%+d depuis le %s)" % (der["abonnes"] - prec["abonnes"], prec["date"]) if prec else "")]
        if not reels:
            md += ["", "Aucun reel publié depuis le %s dans ce fichier." % depuis, ""]; continue
        anciens = [p["views"] for p in reels
                   if maintenant - datetime.strptime(p["date"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc) > timedelta(days=3)]
        base = anciens if len(anciens) >= 3 else [p["views"] for p in reels]
        med = statistics.median(base) or 1
        md += ["Médiane des vues : **%s** (sur %d reels%s)." % (med, len(base), " de plus de 3 jours" if base is anciens else ", trop peu de reels de plus de 3 jours : tous comptés"), ""]
        avant = {p["id"]: p for p in prec["posts"]} if prec else {}
        for p in reels:
            p["x"] = p["views"] / med
            p["j"] = relier(p, compte, jr)
            p["dv"] = p["views"] - avant[p["id"]]["views"] if p["id"] in avant and "views" in avant[p["id"]] else None
        md += ["| Publié | Reel | Vues | x médiane | Enreg. | Partages | Pilier / hook |", "|---|---|---|---|---|---|---|"]
        for p in sorted(reels, key=lambda p: -p["x"]):
            j = p["j"]
            nom = "%s %s" % (j["id"], j["sujet"][:45]) if j else p["legende"][:45]
            md.append("| %s | [%s](%s) | %d%s | %s%.1f | %d | %d | %s |" % (
                p["date"][:10], nom.replace("|", "/"), p["lien"], p["views"], " (%+d)" % p["dv"] if p["dv"] is not None else "",
                "🔥 " if p["x"] >= 3 else "", p["x"], p.get("saved", 0), p.get("shares", 0),
                "%s / %s" % (j["pilier"] or "?", j["formule"] or "?") if j else "non relié au journal"))
        tops = [p for p in reels if p["x"] >= 3]
        md += [""]
        if tops:
            md += ["**Surperformances (≥ 3x la médiane)** — à passer au skill analyse-reel pour en tirer la structure :"]
            md += ["- %s : %.1fx%s" % (p["lien"], p["x"], " ⚠️ ALERTE > 5x : proposer une suite / déclinaison" if p["x"] > 5 else "") for p in tops]
        else:
            md += ["Aucun reel à 3x la médiane ou plus cette fois."]
        for cle, nom in (("pilier", "pilier"), ("formule", "formule de hook")):
            groupes = {}
            for p in reels:
                if p["j"] and p["j"][cle]:
                    groupes.setdefault(p["j"][cle], []).append(p["x"])
            if groupes:
                md += ["", "Par %s (x médian, nombre de reels) : " % nom + " · ".join(
                    "%s %.1fx (%d)" % (g, statistics.median(v), len(v)) for g, v in sorted(groupes.items(), key=lambda kv: -statistics.median(kv[1])))]
        md += [""]
    return "\n".join(md) + "\n"


if __name__ == "__main__":
    depuis = sys.argv[sys.argv.index("--depuis") + 1] if "--depuis" in sys.argv else "2026-10-14"
    txt = bilan(depuis)
    if "--ecrire" in sys.argv:
        f = os.path.join(RACINE, "stats", "bilan-%s.md" % datetime.now(PARIS).strftime("%Y-%m-%d"))
        open(f, "w", encoding="utf-8").write(txt)
        print("écrit :", os.path.relpath(f, RACINE))
    print(txt)
