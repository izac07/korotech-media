# Comptes Instagram (multi-comptes)

Chaque dossier `comptes/<slug>/` = un compte : `theme.json` (couleurs, polices, pseudo, ID Instagram), `README.md` (ligne éditoriale), `journal.md`, `posts/<dossier>/spec.json` + médias.
Le moteur est le même que Korotech : `python3 tools/korotech.py carrousel comptes/<slug>/posts/<dossier>/spec.json comptes/<slug>/posts/<dossier>` (le thème est détecté tout seul) et `... reel ... reel.mp4` (voix `vo_<k>.mp3` dans le même dossier).
URL publique : `https://izac07.github.io/korotech-media/comptes/<slug>/posts/<dossier>/<fichier>`.

## Règles communes
- Rythme : semaine 1 = 1 post/jour ; à partir de la semaine 2 = 2 posts/jour (créneaux dans le README du compte). Environ 4 carrousels pour 3 reels.
- Accroche forte, une seule idée par post, contenu exact et utile, aucun chiffre / test / témoignage inventé. Fin = action (enregistrer, partager, suivre, commenter si naturel ; jamais de promesse d'envoi en DM).
- Légende : accroche + bénéfice + appel à l'action + 5 à 7 hashtags de la niche (pas de hashtags génériques type #instagood).
- Pas de contenu identique entre comptes : chaque compte a ses sujets, son ton, son visuel.
- Reels : 12-20 s, voix off ElevenLabs (scénario Make 9977445, champ `voix` = ID indiqué dans le README du compte), chemins `comptes/<slug>/posts/<dossier>/vo_<k>.mp3`.

## File d'attente
Même Google Sheet que Korotech, scénario 9971858 avec en plus `compte` = ID Instagram du compte (colonne K). ID des posts préfixés par le compte (ex. `LIA-C01`, `ZSF-R01`).
Comptes pas encore reliés à Make : produire les médias normalement, NE PAS les ajouter à la file ; mettre à jour `comptes/<slug>/a-publier.md` (Goat publie/programme à la main).
