# Korotech — production automatique

Dépôt des médias publiés sur Instagram @korotech_fr. Tout ce qui est ici est public (GitHub Pages) : uniquement des visuels de posts, jamais de secrets.

URL publique d'un fichier : `https://izac07.github.io/korotech-media/<chemin>`

## Ligne éditoriale
- Compte : « L'IA, ton meilleur prof » — mais pas un compte scolaire. On mixe les études avec la vie étudiante et l'IA au quotidien.
- Cibles : surtout les 15-25 ans (tutoiement) ; environ 1 post sur 5 pour les parents (vouvoiement).
- **Les 5 piliers (répartition sur 10 posts/jour)** :
  1. **Études malin** (≈ 4/10) : réviser, s'organiser, langues, examens — toujours avec un angle émotion (stress, retard, flemme, contrôle demain).
  2. **Vie étudiante** (≈ 2/10) : job étudiant, entretien, CV, alternance, budget, logement, orientation, premier appart.
  3. **L'IA au quotidien / curiosité** (≈ 2/10) : ce que l'IA sait faire et que personne ne montre, astuces fun ou surprenantes (photo du frigo → recette, préparer un voyage, écrire un message délicat…).
  4. **Humour / POV relatable** (≈ 1/10, au moins 1 par jour) : situations vécues par les élèves/étudiants, qui débouchent sur une astuce.
  5. **Parents** (≈ 1/10).
- **Accroches** : jamais « voici une méthode ». Priorité à l'émotion, la situation vécue, la curiosité ou le défi : « POV : … », « Personne ne t'a dit que… », « Arrête de… », « Le truc que je fais quand… ». Hook ≤ 3 lignes courtes.
- **Varier la structure** : pas toujours « colle ce prompt ». Alterner : mini-histoire (problème → astuce → résultat), liste de 3, avant/après, mythe vs réalité, démonstration. Le prompt peut apparaître, mais ce n'est pas obligatoire.
- **Reels plus courts** : viser 12-20 s (4 scènes max), une seule idée par reel.
- Chaque post finit par une action : enregistrer, partager à un ami, suivre, ou commenter (le mot-clé seulement si c'est naturel ; on ne promet PAS d'envoyer quelque chose en DM).
- Reels : texte animé + **voix off ElevenLabs « Brian » (modèle Eleven v4)** sur TOUS les reels + musique lo-fi originale en fond (baissée automatiquement sous la voix).
- Carrousels : sans musique (l'API Instagram ne le permet pas). Le contenu complet (prompt, liste) est DANS le carrousel.
- Rester exact : pas de chiffres, résultats de « tests » ou anecdotes personnelles inventés. Ne jamais présenter un test comme réalisé s'il ne l'a pas été. Ajouter « l'IA peut se tromper » quand c'est pertinent.

## Rythme : 10 posts par jour (heure de Paris)
| Heure | Format | Pilier |
|---|---|---|
| 07:15 | Reel | Humour / POV |
| 08:30 | Carrousel | Études malin |
| 10:30 | Reel | IA au quotidien |
| 12:15 | Reel | Études malin |
| 13:30 | Carrousel | Vie étudiante |
| 16:45 | Reel | Études malin |
| 18:00 | Carrousel | IA au quotidien |
| 19:15 | Reel | Vie étudiante |
| 20:30 | Carrousel | Parents |
| 21:45 | Reel | Études malin |

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
Chaque scène porte un champ `"vo"` : la phrase dite par Brian pendant cette scène (français oral, naturel, tutoiement pour les élèves / vouvoiement pour les parents ; 8 à 25 mots par scène ; écrire les nombres en lettres ; total ≈ 250-350 caractères par reel pour tenir le quota ElevenLabs).
Avant de générer la vidéo, pour chaque scène k qui a un `vo`, lancer le scénario Make **9977445** (« Korotech - Voix off ElevenLabs ») avec :
`texte` = la phrase, `chemin` = `posts/<dossier>/vo_<k>.mp3` (k = index de la scène, à partir de 0), `voix` = `nPczCjzI2devNBz1zQrb` (Brian), `modele` = `eleven_v4` (ce sont aussi les valeurs par défaut du scénario). Make ne peut PAS écraser un fichier existant dans GitHub : toujours écrire vers un chemin nouveau (pour refaire une voix, supprimer d'abord l'ancien fichier du dépôt et pousser).
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
