#!/usr/bin/env python3
"""Texte à envoyer à la voix ElevenLabs pour chaque scène : « vo » (ou « say ») avec le dictionnaire ressources/prononciation.json appliqué.
Les sous-titres restent ceux de « vo » (bonne orthographe) ; seule la voix entend la version phonétique (« POV » → « pé-o-vé »).

Usage : py -3.13 tools/prononce.py <dossier>/motion.json        -> une ligne par scène : « k<TAB>texte voix »
        py -3.13 tools/prononce.py --texte "Ton POV du soir"     -> le texte voix d'une phrase
"""
import json, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dico():
    return json.load(open(os.path.join(RACINE, "ressources", "prononciation.json"), encoding="utf-8")).get("remplacements", {})


def pour_voix(texte, d=None):
    d = d if d is not None else dico()
    # les expressions les plus longues d'abord (« la BR » avant « BR »), mots entiers seulement
    for k in sorted(d, key=len, reverse=True):
        # une clé en minuscules vaut aussi en début de phrase (« Team », « Snooze »)
        texte = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(k), d[k], texte, flags=re.I if k.islower() else 0)
    return texte


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--texte":
        print(pour_voix(sys.argv[2])); sys.exit(0)
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(2)
    d = dico()
    for k, s in enumerate(json.load(open(sys.argv[1], encoding="utf-8"))["scenes"]):
        t = s.get("say") or s.get("vo", "")
        if t:
            print("%d\t%s" % (k, pour_voix(t, d)))
