#!/usr/bin/env python3
"""Contrôle d'un motion.json AVANT de générer les voix (zéro crédit ElevenLabs gaspillé).

Usage : python3 tools/verifie.py <dossier>/motion.json [autre.json ...]
Code de sortie 1 s'il y a au moins une ERREUR (champ manquant, mauvais ordre de scènes...) ;
les ATTENTION (longueurs, mots, musique déjà utilisée...) n'empêchent pas de continuer mais sont à corriger.
Règles : tools/MOTION.md, comptes/README.md et le README de chaque compte.
"""
import json, os, re, sys, glob

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTS_MIN, MOTS_MAX = 100, 120

# Champs obligatoires par layout et par type de scène ; "ordre" = ordre imposé des 5 scènes (None = libre).
# Les champs suivis de "?" sont optionnels (seulement contrôlés s'ils sont là).
SCHEMA = {
    "cheatsheet": {"ordre": ["hook", "pills", "diagram", "search", "cta"], "types": {
        "hook": ["vo", "title?", "sub?", "big?"],
        "pills": ["vo", "num", "name", "file", "pills", "text"],
        "diagram": ["vo", "num", "name", "nodes", "text"],
        "search": ["vo", "num", "name", "q", "answers", "text"],
        "cta": ["vo", "ctas"]}},
    "claudeflow": {"ordre": ["hook", "chat", "table", "pipeline", "cta"], "types": {
        "hook": ["vo", "title", "sub"],
        "chat": ["vo", "tag", "prompt", "reply"],
        "table": ["vo", "tag", "rows"],
        "pipeline": ["vo", "tag", "nodes", "notif"],
        "cta": ["vo", "title", "ctas"]}},
    "iceberg": {"ordre": ["hook", "surface", "process", "logs", "cta"], "types": {
        "hook": ["vo", "cmd", "top", "bottom"],
        "surface": ["vo", "labels", "text"],
        "process": ["vo", "steps", "chaos", "ok", "text"],
        "logs": ["vo", "logs", "text"],
        "cta": ["vo", "task", "text"]}},
    "sportmotion": {"ordre": ["hook", "erreur", "solution", "pourquoi", "cta"], "types": {
        "hook": ["vo", "pose", "count", "title", "sub"],
        "erreur": ["vo", "pose", "myth", "stamp", "text"],
        "solution": ["vo", "ex", "poses", "effort", "rest", "total"],
        "pourquoi": ["vo", "title", "zones", "badges"],
        "cta": ["vo", "title", "ctas", "ticker"]}},
    "nightchat": {"ordre": ["lock", "msgs", "msgs2", "check", "cta"], "types": {
        "lock": ["vo", "notif"],
        "msgs": ["vo", "bubbles", "sent?", "ghost"],
        "msgs2": ["vo", "bubbles"],
        "check": ["vo", "title", "items"],
        "cta": ["vo", "last", "ctas"]}},
    "manifeste3d": {"ordre": ["hook", "avantapres", "weeks", "weeks", "cta"], "haut": ["counter", "timeline"], "types": {
        "hook": ["vo", "big", "unit", "line", "sub"],
        "avantapres": ["vo", "top", "bottom", "notifs", "kicker", "no", "yes", "card_word"],
        "weeks": ["vo", "weeks"],
        "cta": ["vo", "kicker", "big", "obj", "ctas"]}},
    "notion": {"ordre": ["hook", "steps12", "step3", "step45", "cta"], "haut": ["crumb"], "types": {
        "hook": ["vo", "icon", "title", "mark", "strike", "callout"],
        "steps12": ["vo", "steps", "tags", "quote", "quote_mark"],
        "step3": ["vo", "steps", "items"],
        "step45": ["vo", "steps", "progress", "callout"],
        "cta": ["vo", "title", "mark", "ctas"]}},
    "boucle": {"ordre": None, "types": {"phrase": ["texte"]}},  # PILOTE : format court sans voix, 1 à 3 phrases
    "malin": {"ordre": None, "types": {
        "hook": ["vo", "big", "sub"],
        "list": ["vo", "title", "items", "slots?"],
        "tier": ["vo", "title", "rows"],
        "jars": ["vo", "title", "jars"],
        "math": ["vo", "title", "cells"],
        "cta": ["vo", "big", "ctas"]}},
}
POSES = {"crunch", "planche", "deadbug", "lateral", "climber", "creuse", "squat", "pompe", "fente", "pont"}
LAYOUT_DU_COMPTE = {"korotech_fr": {"cheatsheet"}, "lia.entrepreneur": {"claudeflow", "iceberg"}, "zerosallefit": {"sportmotion"},
                    "coeurlucide__": {"nightchat"}, "mentaldacier2030": {"manifeste3d"}, "revenus_malins": {"malin", "notion"}}


def visible(s):
    """Texte tel qu'il s'affiche : sans **, <br> ni balises."""
    return re.sub(r"<[^>]+>", " ", str(s).replace("**", "")).strip()


def norm(s):
    return re.sub(r"[^a-z0-9àâäçéèêëîïôöùûüÿœ]+", " ", str(s).lower())


def verifier(path):
    err, att = [], []
    try:
        spec = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return ["JSON illisible : %s" % e], []
    lay = spec.get("layout")
    if lay not in SCHEMA:
        return ["layout « %s » inconnu (attendus : %s)" % (lay, ", ".join(SCHEMA))], []
    sch = SCHEMA[lay]
    sc = spec.get("scenes") or []
    for k in ["id", "layout", "music_seed", "handle", "scenes"] + sch.get("haut", []):
        if k not in spec:
            err.append("champ du haut manquant : %s" % k)
    handle = spec.get("handle", "")
    if handle in LAYOUT_DU_COMPTE and lay != "boucle" and lay not in LAYOUT_DU_COMPTE[handle]:
        err.append("le layout %s n'est pas celui de @%s (%s)" % (lay, handle, ", ".join(sorted(LAYOUT_DU_COMPTE[handle]))))
    theme = os.path.join(os.path.dirname(os.path.abspath(path)), "..", "..", "theme.json")
    if os.path.exists(theme):
        th = json.load(open(theme, encoding="utf-8")).get("handle")
        if th and handle and th != handle:
            err.append("handle « %s » différent du theme.json du compte (« %s »)" % (handle, th))

    # ordre et champs des scènes
    if sch["ordre"] is not None:
        types = [s.get("type") for s in sc]
        if types != sch["ordre"]:
            err.append("scènes %s, attendu %s" % (types, sch["ordre"]))
    for k, s in enumerate(sc):
        ty = s.get("type")
        champs = sch["types"].get(ty)
        if champs is None:
            err.append("scène %d : type « %s » inconnu pour %s" % (k, ty, lay)); continue
        for c in champs:
            if not c.endswith("?") and (c not in s or s[c] in ("", [], None)):
                err.append("scène %d (%s) : champ « %s » manquant ou vide (le moteur afficherait le texte par défaut de l'exemple)" % (k, ty, c))
        if lay == "cheatsheet" and ty == "hook" and not (s.get("title") and s.get("sub")):
            att.append("scène %d : hook sans title/sub, le défaut « 3 IA GRATUITES / que presque personne n'utilise » sera affiché" % k)

    # voix off : 100-120 mots, nombres en lettres (boucle : 1 à 3 phrases, 6 à 10 s, pas de voix)
    vo_all = " ".join(s.get("vo", "") for s in sc)
    n = len(vo_all.split())
    if lay == "boucle":
        nm = sum(len(s.get("texte", "").split()) for s in sc)
        duree = nm * float(spec.get("pas", 0.3)) + len(sc) * float(spec.get("tenue", 1.2))
        if not 1 <= len(sc) <= 3: err.append("boucle : 1 à 3 phrases")
        if not 6 <= duree <= 10: att.append("boucle : durée estimée %.1f s (cible 6-10 s)" % duree)
        for k, s in enumerate(sc):
            if len(s.get("texte", "").split()) > 9: att.append("scène %d : plus de 9 mots, la phrase ne tiendra pas en 3 lignes" % k)
    elif n < MOTS_MIN - 10 or n > MOTS_MAX + 10:
        err.append("voix off : %d mots (cible %d-%d, soit 40-45 s)" % (n, MOTS_MIN, MOTS_MAX))
    elif not MOTS_MIN <= n <= MOTS_MAX:
        att.append("voix off : %d mots (cible %d-%d)" % (n, MOTS_MIN, MOTS_MAX))
    for k, s in enumerate(sc):
        if re.search(r"\d", s.get("vo", "")) and not s.get("say"):
            att.append("scène %d : chiffres dans « vo » (écrire les nombres en lettres, ou ajouter « say »)" % k)

    # longueurs et contraintes propres aux layouts (tools/MOTION.md)
    def lim(k, champ, maxi, val=None):
        v = visible(val if val is not None else sc[k].get(champ, ""))
        if len(v) > maxi:
            att.append("scène %d : « %s » fait %d caractères (max %d) : %s" % (k, champ, len(v), maxi, v))

    for k, s in enumerate(sc):
        ty = s.get("type")
        if lay == "cheatsheet":
            if ty == "hook":
                if "title" in s: lim(k, "title", 12)
                if "sub" in s: lim(k, "sub", 28)
            if ty == "pills":
                lim(k, "file", 18)
                if len(s.get("pills", [])) != 3: err.append("scène %d : 3 pills attendues" % k)
            if ty == "diagram" and len(s.get("nodes", [])) != 3: err.append("scène %d : 3 nodes attendus" % k)
            if ty == "search" and len(s.get("answers", [])) != 3: err.append("scène %d : 3 answers attendues" % k)
            if ty == "cta" and len(s.get("ctas", [])) != 2: err.append("scène %d : 2 ctas attendues" % k)
        if lay == "claudeflow":
            if ty == "hook": lim(k, "sub", 30)
            if ty == "chat":
                lim(k, "prompt", 70)
                if not 3 <= len(s.get("reply", [])) <= 6: att.append("scène %d : reply = 3 à 6 lignes" % k)
            if ty == "table":
                rows = s.get("rows", [])
                if not 3 <= len(rows) <= 6: att.append("scène %d : rows = 3 à 6 lignes" % k)
                for r in rows:
                    if len(r) != 4 or r[3] not in ("valider", "publie", "refuse"):
                        err.append("scène %d : ligne de table invalide %s (4 cases, statut valider/publie/refuse)" % (k, r))
            if ty == "pipeline" and not 3 <= len(s.get("nodes", [])) <= 4: err.append("scène %d : 3 ou 4 nodes" % k)
        if lay == "iceberg":
            if "text" in s: lim(k, "text", 30)
            if ty == "surface" and len(s.get("labels", [])) != 3: err.append("scène %d : 3 labels attendus" % k)
            if ty == "process":
                for st in s.get("steps", []): lim(k, "steps", 12, st)
                lim(k, "chaos", 8)
            if ty == "logs":
                lg = s.get("logs", [])
                if not 4 <= len(lg) <= 7: att.append("scène %d : 4 à 7 logs" % k)
                for l in lg:
                    if len(l) != 2 or l[1] not in ("err", "ok", "info", "item"): err.append("scène %d : log invalide %s" % (k, l))
                    else: lim(k, "logs", 32, l[0])
        if lay == "sportmotion":
            for p in ([s.get("pose")] if s.get("pose") else []) + list(s.get("poses", [])):
                if p not in POSES: err.append("scène %d : pose « %s » inconnue (%s)" % (k, p, ", ".join(sorted(POSES))))
            if ty == "solution":
                if not 3 <= len(s.get("ex", [])) <= 5: att.append("scène %d : 3 à 5 exercices" % k)
                if len(s.get("ex", [])) != len(s.get("poses", [])): err.append("scène %d : autant de poses que d'exercices" % k)
            if ty == "pourquoi":
                if len(s.get("zones", [])) != 3: err.append("scène %d : 3 zones" % k)
                if len(s.get("badges", [])) != 3: err.append("scène %d : 3 badges" % k)
        if lay == "nightchat":
            if ty == "msgs" and len(s.get("bubbles", [])) != 2: err.append("scène %d : 2 bulles" % k)
            if ty == "msgs2" and len(s.get("bubbles", [])) != 3: err.append("scène %d : 3 bulles" % k)
            if ty == "check" and len(s.get("items", [])) != 3: err.append("scène %d : 3 items" % k)
        if lay == "manifeste3d":
            if ty == "avantapres":
                if len(s.get("notifs", [])) != 3: err.append("scène %d : 3 notifs" % k)
                cw = s.get("card_word", "")
                if cw and norm(cw).strip() not in norm(s.get("vo", "")):
                    err.append("scène %d : card_word « %s » absent de la voix off" % (k, cw))
            if ty == "weeks":
                if len(s.get("weeks", [])) != 2: err.append("scène %d : 2 cartes weeks" % k)
                w = norm(s.get("word", "semaine")).strip()
                if norm(s.get("vo", "")).split().count(w) + norm(s.get("vo", "")).split().count(w + "s") < 2:
                    err.append("scène %d : le mot « %s » doit apparaître 2 fois dans la voix off" % (k, w))
        if lay == "notion":
            if ty == "steps12" and len(s.get("steps", [])) != 2: err.append("scène %d : 2 étapes" % k)
            if ty == "step3" and len(s.get("items", [])) != 3: err.append("scène %d : 3 items" % k)
            if ty == "step45" and len(s.get("steps", [])) != 2: err.append("scène %d : 2 étapes" % k)
        if lay == "malin":
            if ty == "list":
                it = s.get("items", [])
                if not 3 <= len(it) <= 5: att.append("scène %d : 3 à 5 items" % k)
                if "slots" in s and s["slots"] < len(it): err.append("scène %d : slots doit être >= nombre d'items" % k)
            if ty == "jars" and not 2 <= len(s.get("jars", [])) <= 4: att.append("scène %d : 2 à 4 bocaux" % k)
            if ty == "math" and not 2 <= len(s.get("cells", [])) <= 3: err.append("scène %d : 2 ou 3 cases" % k)
        for c in s.get("cue", []) if isinstance(s.get("cue"), list) else []:
            if norm(c).strip() not in norm(s.get("vo", "")):
                err.append("scène %d : mot déclencheur « %s » absent de la voix off" % (k, c))
        if "ctas" in s and len(s["ctas"]) != 2:
            att.append("scène %d : 2 lignes de ctas attendues" % k)

    # règles éditoriales des comptes
    tout = norm(json.dumps(sc, ensure_ascii=False))
    if handle == "lia.entrepreneur" and re.search(r"\bcomment(e|es|ez|aire|aires)\b", tout):
        err.append("LIA : pas de « commente X » tant que la réponse DM n'est pas branchée")
    if handle == "revenus_malins":
        if re.search(r"\b(epargne|épargne|placement|placements|livret|lep|pea|assurance vie|bourse|etf)\b", tout):
            notes = norm(" ".join(str(s.get("note", "")) for s in sc if s.get("type") == "cta") + " " + json.dumps(
                [s.get("callout", "") for s in sc], ensure_ascii=False))
            if "information generale" not in notes and "information générale" not in notes:
                err.append("Revenus Malins : il faut « Information générale, pas un conseil personnalisé » dans la note du cta")
        if re.search(r"\b(crypto|trading|paris sportifs)\b", tout):
            err.append("Revenus Malins : crypto / trading / paris interdits")
    if handle == "zerosallefit":
        if re.search(r"\b(calories?|kcal|régime|regime|perte de poids)\b", tout):
            att.append("Zéro Salle : pas de nutrition précise ni de promesse de perte de poids")
        if not re.search(r"\b(facile|débutant|debutant|genoux|adapte|version)\b", tout):
            att.append("Zéro Salle : je ne vois pas de version plus facile (genoux au sol, version débutant...)")
    if handle == "coeurlucide__" and re.search(r"\b(pervers|narcissique|bipolaire|toxique pathologique|borderline)\b", tout):
        err.append("Cœur Lucide : pas de diagnostic psy")

    # musique : music_seed différent des autres reels
    seed = spec.get("music_seed")
    autres = []
    for f in glob.glob(os.path.join(RACINE, "**", "motion.json"), recursive=True):
        if os.path.abspath(f) == os.path.abspath(path): continue
        try:
            if json.load(open(f, encoding="utf-8")).get("music_seed") == seed: autres.append(os.path.relpath(f, RACINE))
        except Exception: pass
    if autres:
        att.append("music_seed %s déjà utilisé par %s" % (seed, ", ".join(autres[:3]) + (" ..." if len(autres) > 3 else "")))
    return err, att


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    total_err = 0
    for p in sys.argv[1:]:
        err, att = verifier(p)
        total_err += len(err)
        print("%s : %s" % (p, "OK" if not err and not att else "%d erreur(s), %d attention" % (len(err), len(att))))
        for e in err: print("  ERREUR    " + e)
        for a in att: print("  ATTENTION " + a)
    sys.exit(1 if total_err else 0)
