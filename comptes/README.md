# Comptes Instagram (multi-comptes)

Chaque dossier `comptes/<slug>/` = un compte : `theme.json` (couleurs, polices, pseudo, ID Instagram), `README.md` (ligne éditoriale), `journal.md`, `posts/<dossier>/spec.json` + médias.
Chaque compte a sa propre mise en page. CARROUSELS : champ `layout` du theme.json (défini dans `tools/layouts.py` : terminal, sport, messages, manifeste, fiche), rendu avec `python3 tools/korotech.py carrousel comptes/<slug>/posts/<dossier>/spec.json comptes/<slug>/posts/<dossier>` (le thème est détecté tout seul). REELS : uniquement le format motion design validé du compte, décrit dans `tools/MOTION.md` (fichier `motion.json`, rendu `python3 tools/motion.py <dossier>/motion.json <dossier>/reel.mp4`, voix `vo_<k>.mp3` dans le même dossier). Ne plus utiliser `korotech.py reel`. Ne pas réutiliser le layout d'un compte pour un autre.
URL publique : `https://izac07.github.io/korotech-media/comptes/<slug>/posts/<dossier>/<fichier>`.

## Règles communes
- Rythme (décision de Goat du 17/10/2026) : 2 posts par jour sur chaque compte dès le 19/10/2026 (les 2 créneaux du README) : 1 reel motion + 1 carrousel par jour, en alternant quel créneau a le reel d'un jour à l'autre. Soit 7 reels + 7 carrousels par semaine et par compte.
- Accroche forte, une seule idée par post, contenu exact et utile, aucun chiffre / test / témoignage inventé. Fin = action (enregistrer, partager, suivre, commenter si naturel ; jamais de promesse d'envoi en DM).
- Légende : accroche + bénéfice + appel à l'action + 5 à 7 hashtags de la niche (pas de hashtags génériques type #instagood).
- Pas de contenu identique entre comptes : chaque compte a ses sujets, son ton, son visuel.
- Reels : 40-45 s (100-120 mots de voix off), format motion de `tools/MOTION.md`, voix off ElevenLabs (scénario Make 9977445, champ `voix` = ID indiqué dans le README du compte), chemins `comptes/<slug>/posts/<dossier>/vo_<k>.mp3`.

## File d'attente
Même Google Sheet que Korotech, scénario 9971858 avec en plus `compte` = ID Instagram du compte (colonne K). ID des posts préfixés par le compte (ex. `LIA-C01`, `ZSF-R01`).
Comptes pas encore reliés à Make : produire les médias normalement, NE PAS les ajouter à la file ; mettre à jour `comptes/<slug>/a-publier.md` (Goat publie/programme à la main).
