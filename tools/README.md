# Korotech — production automatique

Dépôt des médias publiés sur Instagram @korotech_fr. Tout ce qui est ici est public (GitHub Pages) : uniquement des visuels de posts, jamais de secrets.

URL publique d'un fichier : `https://izac07.github.io/korotech-media/<chemin>`

## Ligne éditoriale
- Niche : apprendre plus vite avec l'IA (révisions, langues, devoirs, organisation, orientation).
- Cibles : élèves/étudiants (tutoiement) et parents (vouvoiement), environ 1 post sur 3 pour les parents.
- Chaque post finit par une action : enregistrer, commenter un mot-clé en MAJUSCULES, partager ou suivre.
- Reels : texte animé + **voix off ElevenLabs « Alice »** sur TOUS les reels + musique lo-fi originale en fond (baissée automatiquement sous la voix).
- Carrousels : sans musique (l'API Instagram ne le permet pas).
- Rester exact : pas de chiffres ou d'affirmations inventés ; ajouter « l'IA peut se tromper » quand c'est pertinent.

## Rythme : 10 posts par jour (heure de Paris)
| Heure | Format | Cible |
|---|---|---|
| 07:15 | Reel | Élèves |
| 08:30 | Carrousel | Parents |
| 10:30 | Reel | Tous |
| 12:15 | Reel | Élèves |
| 13:30 | Carrousel | Élèves |
| 16:45 | Reel | Élèves |
| 18:00 | Carrousel | Élèves |
| 19:15 | Reel | Tous |
| 20:30 | Carrousel | Parents |
| 21:45 | Reel | Élèves |

## Outils
`python3 tools/korotech.py carrousel posts/<dossier>/spec.json posts/<dossier>` → `slide_XX.jpg` (1080×1350, JPEG obligatoire pour Instagram)
`python3 tools/korotech.py reel posts/<dossier>/spec.json posts/<dossier>/reel.mp4` → MP4 1080×1920 avec musique originale (variée par `music_seed`)

Dépendances : `pip install --break-system-packages playwright scipy numpy pillow && python3 -m playwright install chromium`, plus ffmpeg et les polices Poppins/Inter.

### Spec carrousel
```json
{"id":"C05","slides":[
 {"type":"cover","title":"**Mot en dégradé**<br>suite du titre","size":100,"sub":"Sous-titre"},
 {"type":"item","num":1,"when":"Étape 1","title":"Titre","card":"Prompt avec [placeholder]","card_label":"LE PROMPT"},
 {"type":"item","num":2,"when":"Étape 2","title":"Titre","body":"Texte avec **mots en dégradé**"},
 {"type":"cta","title":"Titre<br>**fin en dégradé**","size":96,"ctas":[["🔖","Enregistre ce post"],["💬","Commente **MOT**"]],"note":"Petite note"}]}
```
5 à 8 slides. `**...**` = dégradé, `[...]` = rose (placeholder), `<br>` = retour à la ligne.

### Spec reel (≈ 20-25 s)
```json
{"id":"R05","music_seed":12,"scenes":[
 {"type":"hook","lines":["Ligne 1","Ligne 2","**Ligne en dégradé**"]},
 {"type":"chat","label":"Le prompt","title":"Colle ce prompt","text":"Texte tapé en direct avec [placeholder]"},
 {"type":"list","label":"Pourquoi","title":"Titre","items":["Point **1**","Point 2","Point 3"]},
 {"type":"result","label":"Résultat","title":"Titre de la fiche","sections":[{"t":"Section","tx":"Texte"}]},
 {"type":"text","label":"Astuce","title":"Une phrase **forte**"},
 {"type":"cta","title":"Tu veux<br>**le prompt ?**","ctas":[["💬","Commente **MOT**"],["🔖","Enregistre"]]}]}
```
Chaque scène accepte `"dur"` (secondes). Hook : 3 lignes courtes max, ≤ 14 caractères par ligne.

### Voix off (tous les reels)
Chaque scène porte un champ `"vo"` : la phrase dite par Alice pendant cette scène (français oral, naturel, tutoiement pour les élèves / vouvoiement pour les parents ; 8 à 25 mots par scène ; écrire les nombres en lettres ; total ≈ 250-350 caractères par reel pour tenir le quota ElevenLabs).
Avant de générer la vidéo, pour chaque scène k qui a un `vo`, lancer le scénario Make **9977445** (« Korotech - Voix off ElevenLabs ») avec :
`texte` = la phrase, `chemin` = `posts/<dossier>/vo_<k>.mp3` (k = index de la scène, à partir de 0), `voix` = `Xb7hH8MSUJpSbSDYk0k2` (Alice).
Puis `git pull` : les `vo_<k>.mp3` arrivent dans le dossier du post. `tools/korotech.py reel` les détecte, allonge chaque scène pour caler la voix, et mixe la musique en dessous. S'il manque un fichier, le script s'arrête avec une erreur : relancer la génération de cette scène.
Si ElevenLabs refuse (quota épuisé), produire le reel SANS `vo` (musique seule) et le signaler à Goat.

## File d'attente
Google Sheet « Korotech - File d'attente Instagram ». On y ajoute une ligne via le scénario Make **9971858** (« Korotech - Ajouter à la file ») avec les entrées :
`id, date ("AAAA-MM-JJ HH:mm", heure de Paris), heure, format ("Reel" ou "Carrousel"), titre, legende, medias, statut ("À valider"), note`.
- Reel : `medias` = URL publique du MP4.
- Carrousel : `medias` = `{"files":[{"media_type":"IMAGE","image_url":"<url slide 1>"}, ...]}`.

Validation par défaut avec droit de veto : le scénario 9972048 publie toutes les 15 min (7h-22h30) les lignes « À valider » ou « Validé » dont l'heure est passée. Goat passe en « Refusé » ce qu'il ne veut pas publier. Statuts posés par le scénario : « En cours », « Publié », « Erreur ».

## Journal
`journal.md` liste chaque post produit (date, id, sujet). Le lire avant de choisir de nouveaux sujets pour ne pas se répéter.

## Statistiques et bilan hebdomadaire
Le scénario Make **9975091** (« Korotech - Stats ») récupère le nombre d'abonnés et, pour chaque post visible, les métriques views, reach, saved, shares, likes, comments. Il dépose un fichier `stats/AAAA-MM-JJ-HHmm.csv` dans ce dépôt (ligne 1 : abonnés, nombre de posts, date ; puis une ligne par post et par métrique). Les anciens posts du stylo (2024-2025) restent dans le fichier : ne comparer que les posts de la nouvelle ligne (à partir du 14/10/2026).

Chaque dimanche soir, la tâche « Korotech - bilan hebdo » lance ce scénario, compare avec le fichier de la semaine précédente, écrit `stats/bilan-AAAA-MM-JJ.md` et met à jour la section ci-dessous.

## Leçons des bilans (à appliquer par la tâche du soir)
- (vide pour l'instant — premier bilan le dimanche 18 octobre 2026)
