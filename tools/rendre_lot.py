#!/usr/bin/env python3
"""Rendu par lot des reels 3D (studio3d) sur le PC de Goat, avec la carte graphique (~3 min par reel au lieu de ~25 dans le cloud).

La routine cloud écrit les reels (motion.json + voix) et les liste dans a-rendre/<COMPTE>-<AAAA-MM-JJ>.json sans les rendre ;
la tâche planifiée locale « Rendu 3D LIA » lance ce script, vérifie les images, puis ajoute chaque reel à la file Make.

Usage : py -3.13 tools/rendre_lot.py            -> rend tous les reels « a_rendre » de a-rendre/*.json, pousse, affiche le bilan
        py -3.13 tools/rendre_lot.py --liste    -> affiche seulement ce qui reste à faire
Fichier a-rendre/*.json : {"compte", "ig_id", "reels": [{"id", "dossier", "date": "AAAA-MM-JJ HH:mm", "heure", "titre", "legende",
                           "note", "statut": "a_rendre" | "rendu" | "en_file" | "erreur", "erreur"?}]}
"""
import glob, json, os, subprocess, sys, time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def lots():
    return sorted(glob.glob(os.path.join(RACINE, "a-rendre", "*.json")))


def sh(*a, **kw):
    return subprocess.run(list(a), cwd=RACINE, text=True, capture_output=True, **kw)


def rendre(r):
    d = os.path.join(RACINE, r["dossier"]); spec = os.path.join(d, "motion.json"); out = os.path.join(d, "reel.mp4")
    v = sh(PY, "tools/verifie.py", spec)
    if v.returncode != 0:
        return "verifie.py : " + v.stdout.strip()[-400:]
    manquantes = [k for k, _ in enumerate(json.load(open(spec, encoding="utf-8"))["scenes"]) if not os.path.exists(os.path.join(d, f"vo_{k}.mp3"))]
    if manquantes:
        return f"voix manquantes : scènes {manquantes}"
    t0 = time.time(); m = sh(PY, "tools/motion.py", spec, out, env={**os.environ, "PYTHONUTF8": "1"})
    if m.returncode != 0 or not os.path.exists(out):
        return "motion.py : " + (m.stderr or m.stdout).strip()[-400:]
    os.makedirs(os.path.join(d, "controle"), exist_ok=True)
    for i, t in enumerate((1, 12, 25)):   # 3 images à regarder avant la mise en file
        sh("ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", out, "-frames:v", "1", "-vf", "scale=360:-1", os.path.join(d, "controle", f"img{i}.jpg"))
    r["duree_rendu_s"] = round(time.time() - t0)
    return None


def main():
    if "--liste" in sys.argv:
        for f in lots():
            L = json.load(open(f, encoding="utf-8"))
            for r in L["reels"]:
                print(os.path.basename(f), r["id"], r["date"], r["statut"])
        return
    sh("git", "pull", "-q")
    faits = []
    for f in lots():
        L = json.load(open(f, encoding="utf-8"))
        for r in L["reels"]:
            if r.get("statut") != "a_rendre":
                continue
            print(f"rendu {r['id']} ({r['dossier']})…", flush=True)
            e = rendre(r)
            r["statut"], r["erreur"] = ("erreur", e) if e else ("rendu", None)
            print("  ->", r["statut"], e or f"{r.get('duree_rendu_s')} s", flush=True)
            json.dump(L, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            if not e:
                faits.append(r["dossier"])
    if faits:
        sh("git", "add", "a-rendre", *[os.path.join(x, "reel.mp4") for x in faits])
        sh("git", "commit", "-q", "-m", f"Rendu 3D local (carte graphique) : {len(faits)} reel(s)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        sh("git", "pull", "--rebase", "-q"); p = sh("git", "push", "-q")
        print("push :", "ok" if p.returncode == 0 else p.stderr.strip())
    else:
        sh("git", "add", "a-rendre"); sh("git", "commit", "-q", "-m", "a-rendre : statuts"); sh("git", "push", "-q")
    print(f"BILAN : {len(faits)} reel(s) rendu(s)")


if __name__ == "__main__":
    main()
