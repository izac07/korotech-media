#!/usr/bin/env python3
"""Contrôle d'un motion.json AVANT de générer les voix (zéro crédit ElevenLabs gaspillé).

Usage : python3 tools/verifie.py <dossier>/motion.json [autre.json ...]
Code de sortie 1 s'il y a au moins une ERREUR (champ manquant, mauvais ordre de scènes...) ;
les ATTENTION (longueurs, mots, musique déjà utilisée...) n'empêchent pas de continuer mais sont à corriger.
Règles : tools/MOTION.md, comptes/README.md et le README de chaque compte.
"""
import json, os, re, sys, glob

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTS_MIN, MOTS_MAX = 70, 90  # revu le 25/10/2026 (courbe de rétention MDA-X13) : ~25-30 s

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
        "msgs": ["vo", "bubbles", "sent?", "ghost", "question?"],
        "msgs2": ["vo", "bubbles", "question?"],
        "check": ["vo", "title", "items", "question?"],
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
    "boucle": {"ordre": None, "types": {"phrase": ["texte"]}},
    "carnet": {"ordre": None, "types": {"hook": ["vo", "titre", "sous?"], "note": ["vo", "titre", "lignes"], "liste": ["vo", "titre", "items"],
        "postit": ["vo", "texte", "titre?"], "cta": ["vo", "titre", "ctas"]}},  # PILOTE 23/10/2026 : carnet manuscrit, tous comptes  # PILOTE : format court sans voix, 1 à 3 phrases
    "interface": {"ordre": None, "types": {"hook": ["vo", "titre", "sous?", "notif?"], "toggles": ["vo", "carte", "items", "titre?"], "chat": ["vo", "messages", "titre?"],
        "grille": ["vo", "cartes", "titre?"], "compteur": ["vo", "valeur", "label", "lignes?", "titre?"], "cta": ["vo", "titre", "ctas"],
        "duo": ["vo", "qui", "bulle"], "punch": ["vo", "titre", "sous?"], "jauge": ["vo", "labels", "a", "de?", "unite?", "titre?"]}},  # PILOTE 23/10/2026 : cartes d'appli, tous comptes
    "anatomie3d": {"ordre": None, "types": {p: ["vo", "exercice?", "reps?", "muscle?", "jour?", "bandeau?", "question?", "carte?", "badge?", "source?", "compteur?"] for p in ("large", "face", "cote", "muscle", "orbite")}},  # PILOTE 25/10/2026 : mannequin + muscle lumineux (Zéro Salle) ; badge/source/compteur depuis le 27/10
    "studio3d": {"ordre": None, "types": {p: ["vo", "bandeau", "ecran?", "compteur?", "humeur?", "tampon?", "carte?", "qui?", "bocal?", "lumiere?"] for p in ("large", "ecran", "mascotte", "telephone", "toi")}},  # PILOTE 24/10/2026 : scène 3D (LIA)
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
    if handle in LAYOUT_DU_COMPTE and lay not in ("boucle", "carnet", "interface", "studio3d", "anatomie3d") and lay not in LAYOUT_DU_COMPTE[handle]:
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

    # voix off : 70-90 mots, nombres en lettres (boucle : 1 à 3 phrases, 6 à 10 s, pas de voix)
    vo_all = " ".join(s.get("vo", "") for s in sc)
    n = len(vo_all.split())
    if lay == "boucle":
        nm = sum(len(s.get("texte", "").split()) for s in sc)
        duree = nm * float(spec.get("pas", 0.3)) + len(sc) * float(spec.get("tenue", 1.2))
        if not 1 <= len(sc) <= 3: err.append("boucle : 1 à 3 phrases")
        if not 6 <= duree <= 10: att.append("boucle : durée estimée %.1f s (cible 6-10 s)" % duree)
        for k, s in enumerate(sc):
            if len(s.get("texte", "").split()) > 9: att.append("scène %d : plus de 9 mots, la phrase ne tiendra pas en 3 lignes" % k)
    elif any(s.get("type") == "duo" or s.get("qui") == "claude" for s in sc):  # format dialogue (interface duo, ou studio3d avec qui) (questions qui relancent) : plus long, 50-80 s
        if not 120 <= n <= 200:
            err.append("dialogue : %d mots de voix (cible 120-200, soit 50-80 s)" % n)
        for k, s in enumerate(sc):
            if s.get("qui") not in ("moi", "claude"):
                err.append("scène %d : « qui » doit valoir « moi » ou « claude » (choisit la voix)" % k)
    elif spec.get("handle") == "mentaldacier2030" and not 100 <= n <= 150:  # format long 40-45 s (décision de Goat du 29/10/2026)
        (err if not 90 <= n <= 160 else att).append("voix off : %d mots (Mental d'Acier, format long : cible 110-140, soit 40-45 s)" % n)
    elif spec.get("handle") == "mentaldacier2030":
        pass
    elif n < MOTS_MIN - 10 or n > MOTS_MAX + 10:
        err.append("voix off : %d mots (cible %d-%d, soit 25-30 s)" % (n, MOTS_MIN, MOTS_MAX))
    elif not MOTS_MIN <= n <= MOTS_MAX:
        att.append("voix off : %d mots (cible %d-%d)" % (n, MOTS_MIN, MOTS_MAX))
    # pas d'ordre isolé : « Enregistre ça. » / « Commente PLAN. » seuls ne sont pas fluides (Goat, 29/10/2026)
    for k, s in enumerate(sc):
        for ph in re.split(r"(?<=[.!?…])\s+", s.get("vo", "")):
            if re.fullmatch(r"(enregistre|commente)\b[^,;:]{0,25}[.!]?", ph.strip().lower()):
                att.append("scène %d : « %s » est un ordre isolé ; l'accrocher à la phrase d'avant avec une raison (« …et enregistre la vidéo pour pas l'oublier »)" % (k, ph.strip()))
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
    # (LIA : l'interdiction de « commente X » est levée depuis le 23/10/2026, Goat répond en DM à la main)
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

    # structure (règle revue le 25/10/2026) : accroche, PREMIER CONSEIL tout de suite, puis « Enregistre cette vidéo » en scène 1 ou 2.
    # Courbe de MDA-X13 : 75 % encore là à 3 s, 30 % à 6 s, pile pendant « Enregistre cette vidéo » dit juste après l'accroche.
    if lay != "boucle" and sc and sc[0].get("vo") and not spec.get("sans_mot_cle"):
        dit = lambda s: re.search(r"\benregistre", norm(s.get("say") or s.get("vo", "")))
        dialogue = sc[0].get("type") == "duo" or bool(sc[0].get("qui"))
        if dit(sc[0]) and not dialogue:
            err.append("scène 0 : « Enregistre » est trop tôt (les spectateurs partent entre 3 et 6 s) ; donne d'abord le 1er conseil, puis dis « Enregistre » en scène 1 ou 2")
        elif not any(dit(s) for s in sc[:3]):
            err.append("scènes 1-2 : après le 1er conseil, la voix doit dire « Enregistre cette vidéo » (ex. « … Enregistre-la, la suite est encore mieux. »)")
        if not dialogue and len((sc[0].get("say") or sc[0]["vo"]).split()) > 18:
            att.append("scène 0 : %d mots de voix ; viser 18 au plus pour changer de plan vers 3-4 s" % len((sc[0].get("say") or sc[0]["vo"]).split()))

    # dire « Claude » et pas « l'IA » (décision de Goat du 24/10/2026)
    for k, s in enumerate(sc):
        v = (s.get("say") or s.get("vo", "")).lower().replace("’", "'")
        if re.search(r"\bl'ia\b|\bl'intelligence artificielle\b", v):
            err.append("scène %d : la voix dit « l'IA » ; dire « Claude » (« mets ton cours dans Claude », « demande à Claude »)" % k)
        elif re.search(r"\bune ia\b", v):
            att.append("scène %d : « une IA » dans la voix ; dire « Claude » sauf comparaison de plusieurs outils" % k)

    # rétention et accroche (tools/MOTION.md, 23/10/2026)
    if lay != "boucle" and sc and sc[0].get("vo"):
        vo0 = (sc[0].get("say") or sc[0]["vo"]).strip()
        phrase1 = re.split(r"(?<=[.!?…])\s+", vo0)[0]
        if len(phrase1.split()) > 14:
            att.append("scène 0 : 1re phrase de %d mots (14 max) : %s" % (len(phrase1.split()), phrase1))
        if re.match(r"(salut|bonjour|hello|coucou|aujourd ?hui|dans cette vid[ée]o)\b", vo0.lower().replace("'", " ")):
            err.append("scène 0 : la voix commence par une introduction (« %s ») ; entrer direct dans le sujet" % phrase1)
        for k, s in enumerate(sc):
            nv = len((s.get("say") or s.get("vo", "")).split())
            if nv > 30:
                att.append("scène %d : %d mots de voix (30 max, sinon l'écran reste trop longtemps sans changement)" % (k, nv))
            ne = len(visible(" ".join(str(v) for c, v in s.items() if c not in ("vo", "say", "type", "cue", "ctas", "pose", "poses", "note"))
                             .replace("[", " ").replace("]", " ")).split())
            if ne > 25:
                att.append("scène %d : %d mots affichés (viser 12 au même moment)" % (k, ne))
        if lay in ("carnet", "malin", "interface"):
            m = re.search(r"\b([2-9]|10)\b", visible(json.dumps({c: v for c, v in sc[0].items() if c not in ("vo", "say")}, ensure_ascii=False)))
            listes = [len(s["items"]) for s in sc if isinstance(s.get("items"), list) and s.get("type") in ("liste", "list")]
            if m and listes and int(m.group(1)) not in listes:
                att.append("le hook annonce %s mais les listes ont %s éléments : tenir le nombre annoncé" % (m.group(1), listes))

    # mot-clé à commenter (ressources/mots-cles.json) : le dernier écran l'affiche et la voix le dit
    mc_f = os.path.join(RACINE, "ressources", "mots-cles.json")
    if os.path.exists(mc_f) and lay != "boucle" and sc and not spec.get("sans_mot_cle"):
        mc = spec.get("mot_cle") or json.load(open(mc_f, encoding="utf-8")).get(handle)  # mot_cle : cadeau propre à ce reel (ex. le prompt montré)
        if mc:
            mot = mc["mot"].lower()
            fin = sc[-1]
            ecran = norm(visible(json.dumps([{k: v for k, v in s.items() if k not in ("vo", "say")} for s in (sc if handle == "mentaldacier2030" else [fin])], ensure_ascii=False)))
            if not re.search(r"\b%s\b" % re.escape(mot), ecran):
                err.append("dernière scène : le mot-clé « %s » doit être affiché (ex. ctas « 💬 COMMENTE « %s » »)" % (mc["mot"], mc["mot"]))
            vo_fin = norm(fin.get("say") or fin.get("vo", ""))
            # Mental d'Acier (format long) : le mot-clé est dit juste avant le 3e conseil, donc dans n'importe quelle scène
            if handle == "mentaldacier2030":
                vo_fin = norm(" ".join(s.get("say") or s.get("vo", "") for s in sc))
            if any(s.get("vo") for s in sc) and not (re.search(r"\bcommente\b", vo_fin) and re.search(r"\b%s\b" % re.escape(mot), vo_fin)):
                err.append("dernière scène : la voix doit dire « Commente %s pour recevoir %s » (décision de Goat du 23/10/2026)" % (mot, mc["offre"]))

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
    att += fautes(sc)
    return err, att


# Relecture orthographe/grammaire (demande de Goat du 29/10/2026 : « il y a beaucoup de fautes dans le script ») avec LanguageTool.
# Le registre familier est VOULU (cible 18-30 ans : « t'as », « c'est quoi », « c'est pas ») : ces règles-là sont ignorées,
# ainsi que les mots anglais/argot du compte (ressources/prononciation.json). Sans réseau, la relecture est sautée sans bloquer.
FAMILIER = {"BARBARISME_TU", "C_EST_QUOI", "P_V_PAS", "QUOI_FAIRE", "POSER_UNE_QUESTION", "PAS_DE_VIRGULE", "VIRG_NON_TROUVEE",
            "PLACE_DE_LA_VIRGULE", "FRENCH_WHITESPACE", "ESPACE_ENTRE_POINT_ET_GUILLEMET", "APOS_TYP", "UPPERCASE_SENTENCE_START"}


def fautes(sc):
    import urllib.request, urllib.parse
    if os.environ.get("SANS_RELECTURE"):
        return []
    try:
        mots_ok = {m.lower() for m in json.load(open(os.path.join(RACINE, "ressources", "prononciation.json"), encoding="utf-8")).get("mots_admis", [])}
    except Exception:
        mots_ok = set()
    out = []
    for k, s in enumerate(sc):
        t = s.get("vo", "")
        if not t:
            continue
        try:
            data = urllib.parse.urlencode({"text": t, "language": "fr"}).encode()
            r = json.load(urllib.request.urlopen("https://api.languagetool.org/v2/check", data, timeout=12))
        except Exception:
            return ["relecture LanguageTool impossible (pas de réseau ?) : relire les fautes à la main"]
        for m in r.get("matches", []):
            o, l = m["offset"], m["length"]
            mot = t[o:o + l]
            if m["rule"]["id"] in FAMILIER or mot.lower() in mots_ok:
                continue
            prop = ", ".join(x["value"] for x in m.get("replacements", [])[:2])
            out.append("scène %d : faute possible « %s » (%s)%s" % (k, mot, m["message"][:70], " → " + prop if prop else ""))
    return out


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
