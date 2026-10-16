# Reels « motion design » (formats validés par Goat le 16-17/10/2026)

Tous les reels de tous les comptes se font avec ce moteur. Plus de `tools/korotech.py reel` pour les reels.

```
python3 tools/motion.py <dossier>/motion.json <dossier>/reel.mp4
```

- Les voix doivent exister AVANT le rendu : `<dossier>/vo_0.mp3`, `vo_1.mp3`… (une par scène, même ordre que `scenes`).
- La durée de chaque scène = durée de sa voix + 0,9 s. Cible : **40 à 45 s au total**, soit **100 à 120 mots de voix off** au total sur les 5 scènes.
- Les sous-titres mot à mot, la musique (`music_seed`, différent à chaque reel) et les bruitages sont automatiques.
- Toujours **5 scènes**, dans l'ordre indiqué pour le layout. Tous les champs texte sont obligatoires sauf mention contraire. Textes courts : ils sont affichés en gros.
- `**mot**` = mise en valeur (couleur / bandeau selon le layout).
- Euros : écris `100 €` normalement (l'espace insécable est ajouté).
- Vérifie visuellement 3 images du MP4 (ffmpeg -ss … -frames:v 1) : texte qui déborde ou chevauche → raccourcis le texte.
- Champs communs : `"id"`, `"layout"`, `"music_seed"`, `"handle"` (pseudo sans @), `"scenes"`.

| Compte | layout | voix |
|---|---|---|
| korotech_fr | `cheatsheet` | Brian |
| lia.entrepreneur | `iceberg` | Brian |
| zerosallefit | `sportmotion` | Brian |
| coeurlucide__ | `nightchat` | Alice |
| mentaldacier2030 | `manifeste3d` | Brian |
| revenus_malin | `notion` | Brian |

Exemples validés (à copier comme base) :
`posts/x04-3-ia-revisions/motion.json`, `comptes/lia-entrepreneur/posts/r02-iceberg/motion.json`, `comptes/zerosallefit/posts/r02-abdos-circuit/motion.json`, `comptes/coeurlucide/posts/r02-message-valeur/motion.json`, `comptes/mentaldacier/posts/r03-reset-30j/motion.json`, `comptes/revenus-malin/posts/r02-premiers-100/motion.json`.

---

## cheatsheet (Korotech) — « 3 outils / 3 astuces »
1. `hook` : `vo`
2. `pills` : `num` ("01"), `name`, `file` (nom de fichier déposé), `pills` (3 courts, avec emoji), `text`
3. `diagram` : `num`, `name`, `nodes` (3 mots), `text`
4. `search` : `num`, `name`, `q` (question tapée), `answers` (3 lignes courtes), `text`
5. `cta` : `ctas` (2 lignes)
Champ optionnel `say` sur chaque scène = texte à envoyer à ElevenLabs à la place de `vo` quand la prononciation pose problème (ex. « Notebook L M »). Les sous-titres suivent `vo`.

## iceberg (LIA) — « ce qu'on te montre / ce qu'on te cache »
1. `hook` : `cmd` (commande tapée, ex. `./reveler --iceberg`), `top` (ex. « ce qu'on te montre »), `bottom` (ex. « ce qu'on te cache »)
2. `surface` : `labels` (3 promesses courtes, elles reçoivent un tampon [FAUX]), `text`
3. `process` : `steps` (3 blocs très courts, ≤ 12 caractères), `chaos` (mot du chaos, idéalement ≤ 8 caractères), `ok` (ex. « process clair »), `text`
4. `logs` : `logs` = liste de 4 à 7 `[texte, type]` avec type `err` (rouge, [x]), `ok` (vert), `info` (blanc), `item` (jaune, « + »). Textes ≤ 32 caractères. `text`
5. `cta` : `task` (ex. « 1 TÂCHE RÉPÉTITIVE »), `text`
`text` = phrase courte en bas d'écran (≤ 30 caractères).

## sportmotion (Zéro Salle) — « erreur → solution → pourquoi »
Poses disponibles : `crunch`, `planche`, `deadbug`, `lateral`, `climber`, `creuse`, `squat`, `pompe`, `fente`, `pont`.
1. `hook` : `pose`, `count` (nombre qui défile, ex. 100), `title` (ex. « STOP AUX **100 CRUNCHS** »), `sub` (ex. « ⏱ 5 MIN À LA PLACE »)
2. `erreur` : `pose`, `myth` (idée reçue entre « »), `stamp` (ex. MYTHE / FAUX), `text` (2 lignes avec `<br>`, ex. « LONG · NUQUE ·<br>**ZÉRO FONTE LOCALE** »), `neck` (optionnel, cercle rouge sur la nuque)
3. `solution` : `ex` (3 à 5 noms d'exercices en MAJUSCULES), `poses` (même nombre, pose de chaque exercice), `effort` (« 45 s »), `rest` (« 15 s »), `total` (« 5:00 »)
4. `pourquoi` : `title` (avec `<br>`), `zones` (3 mots : zones travaillées), `badges` (3 consignes de sécurité/technique courtes)
5. `cta` : `title` (avec `<br>`), `ctas` (2 lignes avec emoji), `ticker` (bandeau défilant)
Pas de promesse médicale ni de « fonte localisée ».

## nightchat (Cœur Lucide) — POV iPhone la nuit
1. `lock` : `notif` (texte de la notification sur l'écran verrouillé)
2. `msgs` : `bubbles` (2 messages), `sent` (ton message resté sans réponse, ex. « Tu es dispo ? »), `ghost` (ex. « Vu 22:14 »)
3. `msgs2` : `bubbles` (3 messages)
4. `check` : `title`, `items` (3 petites actions)
5. `cta` : `last` (dernier message), `ctas` (2 lignes)
Voix Alice. Pas de diagnostic psy.

## manifeste3d (Mental d'Acier) — défi/plan en N jours, avant/après 3D
Champs du haut : `counter` = `{"label":"JOUR","short":"J","max":30}` (compteur en haut à droite) et `timeline` = 4 étiquettes de la frise (ex. `["S1","S2","S3","S4"]` ou `["J1-5","J6-10","J11-15","J16-21"]`).
1. `hook` : `big` (« 30 »), `unit` (« JOURS »), `line` (`**texte en bandeau blanc**<br>suite`), `sub` (petite ligne // …)
2. `avantapres` (perso au lit avec son téléphone en haut, pompes en bas) : `top` (« AVANT · J1 »), `bottom` (« OBJECTIF · J30 »), `notifs` (3 notifications), `kicker` (ex. « précision »), `no` (idée fausse, barrée), `yes` (la vraie idée), `card_word` (mot de la voix off où la carte apparaît, ex. « précision » — ce mot DOIT être dans `vo`)
3. `weeks` : `weeks` = 2 cartes `[titre, ligne 1, ligne 2 ou ""]`, `word` (optionnel, défaut « semaine » : mot de la voix off qui fait apparaître chaque carte, il doit apparaître 2 fois dans `vo`)
4. `weeks` : idem (cartes 3 et 4)
5. `cta` : `kicker` (« JOUR »), `big` (« 30 »), `obj` (avec `**mot souligné**`), `ctas` (2 lignes)
Rendu 3D plus lent (≈ 2× un autre layout). Pas de « détox dopamine » ni de promesse médicale.

## notion (Revenus Malins) — page Notion « méthode en 5 étapes »
Champ du haut : `crumb` (fil d'Ariane, ex. « Revenus Malins / Méthode « premiers 100 € » »).
1. `hook` : `icon` (emoji), `title`, `mark` (morceau du titre surligné), `strike` (fausse promesse barrée), `callout` (encadré ⚠️)
2. `steps12` : `steps` (2 : « Étape 1 — … », « Étape 2 — … »), `tags` (2 à 4 mots), `quote` (exemple concret entre « »), `quote_mark` (morceau surligné)
3. `step3` : `steps` (1), `items` (3 lignes avec emoji, la souris les survole)
4. `step45` : `steps` (2), `progress` = `{"label":"Objectif 100 €","n":7,"step":15,"suffix":" €","note":"≈ 7 ventes × 15 €"}` (barre qui se remplit n fois de `step`), `callout` (encadré 🔗, ex. sources officielles / déclaration)
5. `cta` : `title`, `mark`, `ctas` (2 lignes)
Objectifs modestes et réalistes, jamais de revenu garanti ; rappeler de déclarer ses revenus quand c'est pertinent.
