# Comptes Instagram (multi-comptes)

Chaque dossier `comptes/<slug>/` = un compte : `theme.json` (couleurs, polices, pseudo, ID Instagram), `README.md` (ligne éditoriale), `journal.md`, `posts/<dossier>/spec.json` + médias.
Chaque compte a sa propre mise en page. CARROUSELS (plus utilisés depuis le 18/10/2026, gardé pour référence) : champ `layout` du theme.json (défini dans `tools/layouts.py` : terminal, sport, messages, manifeste, fiche), rendu avec `python3 tools/korotech.py carrousel comptes/<slug>/posts/<dossier>/spec.json comptes/<slug>/posts/<dossier>` (le thème est détecté tout seul). REELS : uniquement le format motion design validé du compte, décrit dans `tools/MOTION.md` (fichier `motion.json`, rendu `python3 tools/motion.py <dossier>/motion.json <dossier>/reel.mp4`, voix `vo_<k>.mp3` dans le même dossier). Ne plus utiliser `korotech.py reel`. Ne pas réutiliser le layout d'un compte pour un autre.
URL publique : `https://izac07.github.io/korotech-media/comptes/<slug>/posts/<dossier>/<fichier>`.

## Règles communes
- Rythme (décision de Goat du 18/10/2026) : 2 posts par jour sur chaque compte (les 2 créneaux du README), UNIQUEMENT DES REELS motion. Plus aucun carrousel. Soit 14 reels par semaine et par compte. Varier les sujets et les angles d'un reel à l'autre (les 2 reels d'une même journée ne doivent pas se ressembler).
- Accroche forte, une seule idée par post, contenu exact et utile, aucun chiffre / test / témoignage inventé. Fin = **mot-clé à commenter** du compte (décision du 23/10/2026, `ressources/mots-cles.json`) : la dernière scène l'affiche, la voix le dit (« Commente PLAN pour recevoir le plan 7 jours ») et la légende finit par « 💬 Commente <MOT> et je t'envoie <offre> en DM ». Goat envoie le lien en DM à la main (`ressources/messages-dm.md`) ; jamais le lien dans la légende.
- Légende : accroche + bénéfice + appel à l'action + 5 à 7 hashtags de la niche (pas de hashtags génériques type #instagood).
- Pas de contenu identique entre comptes : chaque compte a ses sujets, son ton, son visuel.
- Reels : 25-30 s (70-90 mots de voix off, revu le 25/10/2026), format motion de `tools/MOTION.md`, voix off ElevenLabs (scénario Make 9977445, champ `voix` = ID indiqué dans le README du compte), chemins `comptes/<slug>/posts/<dossier>/vo_<k>.mp3`.
- Contrôles obligatoires (depuis le 18/10/2026, détail dans `tools/MOTION.md` « Chaîne de contrôle ») : `tools/journal.py` (sujet pas déjà traité, 2 reels du jour différents), `tools/verifie.py` (0 erreur avant de payer les voix), `tools/audit.py --estime` (hook ≤ 0,5 s, zones sûres), puis `tools/journal.py ajouter` après l'ajout à la file. Bilan : `tools/bilan.py` (tous les comptes, x fois la médiane).

## File d'attente
Même Google Sheet que Korotech, scénario 9971858 avec en plus `compte` = ID Instagram du compte (colonne K). ID des posts préfixés par le compte (ex. `LIA-C01`, `ZSF-R01`).
Comptes pas encore reliés à Make : produire les médias normalement, NE PAS les ajouter à la file ; mettre à jour `comptes/<slug>/a-publier.md` (Goat publie/programme à la main).
