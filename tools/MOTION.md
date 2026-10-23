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

## Chaîne de contrôle (depuis le 18/10/2026) — dans cet ordre
Python **3.12 minimum** (`motion.py` ne tourne pas en 3.11). Machine neuve / routine cloud : `source tools/setup.sh` puis utiliser `"$PY"` à la place de `python3`.
1. **Sujet** : `"$PY" tools/journal.py sujets --compte <handle>` puis `"$PY" tools/journal.py verifier --compte <handle> --sujet "…"` (alerte si sujet déjà traité).
2. **motion.json écrit** → `"$PY" tools/verifie.py <dossier>/motion.json` : 0 ERREUR obligatoire, corriger les ATTENTION. Un champ manquant n'est jamais anodin : le moteur afficherait le texte par défaut de l'exemple (ex. « STOP AUX 100 CRUNCHS »). Vérifie aussi 100-120 mots, longueurs, mots déclencheurs présents dans `vo`, règles du compte, `music_seed` jamais utilisé.
3. **Avant les voix** → `"$PY" tools/audit.py <dossier>/motion.json --estime --planche /tmp/audit.jpg` puis lire la planche (outil Read). Hook lisible ≤ 0,5 s, texte ≥ 30 px, rien sous les boutons d'Instagram (x > 960, y 1000-1750).
4. Voix (scénario 9977445) → rendu `"$PY" tools/motion.py …` : l'audit est relancé tout seul avec les vraies durées et s'affiche avant le rendu.
5. **Après ajout à la file** → `"$PY" tools/journal.py ajouter <dossier>/motion.json --date "AAAA-MM-JJ HH:MM" --pilier "<pilier du README>" --formule <pov|question|stop|secret|chiffre|avant-apres|mythe|liste|defi|histoire|demo|erreur> --sujet "…"` (remplit `journal-reels.csv` ET le journal.md du compte, et contrôle que les 2 reels du jour ne se ressemblent pas : pas le même pilier ET la même formule).
Bilan du dimanche : `"$PY" tools/bilan.py --ecrire` (tous les comptes, x fois la médiane, par pilier et par formule de hook).
Zone connue : les sous-titres de tous les layouts sont vers y = 1570-1800, dans la zone pseudo/légende d'Instagram (l'audit le signale) — à décider par Goat avant de les remonter.

| Compte | layout | voix |
|---|---|---|
| korotech_fr | `cheatsheet` | Brian |
| lia.entrepreneur | `claudeflow` (coulisses, par défaut) ou `iceberg` (mythes) | Brian |
| zerosallefit | `sportmotion` | Brian |
| coeurlucide__ | `nightchat` | Alice |
| mentaldacier2030 | `manifeste3d` | Brian |
| revenus_malins | `malin` (par défaut, validé le 18/10) ou `notion` (méthode en 5 étapes) | Brian |

Exemples validés et COMPLETS (à copier comme base ; ils passent `tools/verifie.py`) :
`posts/x04-3-ia-revisions/motion.json`, `comptes/lia-entrepreneur/posts/r06-mythe-prompt-magique/motion.json` (iceberg), `comptes/lia-entrepreneur/posts/r04-systeme-claude/motion.json` (claudeflow), `comptes/zerosallefit/posts/r03-circuit-jambes/motion.json`, `comptes/coeurlucide/posts/r03-reparer-dispute/motion.json`, `comptes/mentaldacier/posts/r03-reset-30j/motion.json`, `comptes/revenus-malin/posts/r04-budget-50-30-20/motion.json`.
Ne PAS copier `r02-iceberg` ni `r02-abdos-circuit` : ils n'ont pas les champs (ils s'appuient sur les textes par défaut du moteur).

---

## cheatsheet (Korotech) — « 3 outils / 3 astuces »
1. `hook` : `vo` ; optionnels `big` (défaut « 3 »), `title` (défaut « IA **GRATUITES** », ≤ 12 caractères, `**mot**` en dégradé) et `sub` (défaut « que presque personne n'utilise 👀 », ≤ 28 caractères). À remplir dès que le reel n'est pas « 3 IA gratuites » (ex. « 3 » / « **ASTUCES** » / « quand le prof t'a perdu 😵 »).
2. `pills` : `num` ("01"), `name`, `file` (nom de fichier déposé, ≤ 18 caractères), optionnel `ext` (étiquette du fichier, défaut « PDF »), `pills` (3 courts, avec emoji), `text`
3. `diagram` : `num`, `name`, `nodes` (3 mots), `text`
4. `search` : `num`, `name`, `q` (question tapée), `answers` (3 lignes courtes), `text`
5. `cta` : `ctas` (2 lignes)
Champ optionnel `say` sur chaque scène = texte à envoyer à ElevenLabs à la place de `vo` quand la prononciation pose problème (ex. « Notebook L M »). Les sous-titres suivent `vo`.

## claudeflow (LIA) — coulisses « Claude → file → publication »
Exemple validé : `comptes/lia-entrepreneur/posts/r04-systeme-claude/motion.json`.
1. `hook` : `title` (avec `<br>` et `**mot en vert**`, 2 lignes courtes), `sub` (tapé au clavier, ≤ 30 caractères)
2. `chat` : `tag` (ex. « ÉTAPE 1 · CLAUDE ÉCRIT »), `prompt` (la demande tapée, ≤ 70 caractères), `reply` (3 à 6 lignes courtes de réponse, `**…**` en vert), optionnels `window`, `who`
3. `table` : `tag`, `rows` = 3 à 6 lignes `[jour, heure, intitulé court, statut final]` avec statut `valider`, `publie` ou `refuse` ; optionnel `window`
4. `pipeline` : `tag`, `nodes` = 3 ou 4 `[NOM, sous-titre]`, `notif` (notification finale)
5. `cta` : `title` (avec `<br>` et `**…**`), `ctas` (2 lignes)
Le contenu montré doit être vrai chez Goat (vrais outils, vrais réglages) ; adapter `tag`/`rows`/`nodes` au sujet (un tuto peut avoir ÉTAPE 1/2/3 différentes).

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


## malin (Revenus Malins, format par défaut depuis le 18/10/2026) — structures qui se remplissent
Exemple validé : `comptes/revenus-malin/posts/r04-budget-50-30-20/motion.json`. Pas de visage. Nombre de scènes LIBRE (en général 5) ; on enchaîne les types suivants selon le sujet, une seule idée par reel :
- `hook` : `big` (gros titre, `<br>` et `**mot en jaune**`), `sub` (sous-titre)
- `list` (liste à trous qui se remplit) : `title` (`**mot surligné**`), `items` = 3 à 5 `[texte, précision]`, `slots` (nombre de lignes affichées, ≥ items : les vides créent la curiosité), `cue` (optionnel : mot de la voix off qui fait apparaître chaque ligne, ex. ["un","deux","trois"]), `note` (optionnel)
- `tier` (tier list S→F) : `title`, `rows` = {"S":[..],"A":[..],"B":[..],...} (étiquettes courtes), `note`
- `jars` (bocaux qui se remplissent, 2 à 4) : `title`, `jars` = [{"label","pct","amount"}], `cue`, `note`
- `math` (chiffres en cases qui défilent) : `title`, `cells` = 2 ou 3 `[libellé, "1 500 €", opérateur]` (opérateur "−", "+", "=" devant la 2e/3e case ; la dernière case est surlignée), `note`
- `cta` : `big`, `ctas` (2 lignes), `note`
Règles : information générale uniquement, jamais de promesse de rendement ni de conseil d'achat d'un placement précis ; pas de taux ou plafonds qui changent sans vérifier ; mettre « Information générale, pas un conseil personnalisé » dans la note du `cta` dès qu'on parle d'épargne/placements. Les chiffres d'exemple sont présentés comme des exemples.

## boucle (PILOTE, tous comptes) — boucle courte de 6 à 10 s, sans voix
Exemple : `tools/exemples/boucle-exemple/motion.json`. À tester sur 2-3 posts par semaine maximum, à côté des 40-45 s, puis comparer au bilan (x médiane).
Champs du haut : `pas` (secondes par mot, défaut 0.3), `tenue` (s de phrase complète, défaut 1.2), `couleurs` = 2 paires `[fond, texte]`, optionnels `police`, `taille` (px, défaut 120).
Scènes : 1 à 3 `{"type":"phrase","texte":"…"}`, 9 mots max par phrase (`**mot**` = souligné). Mécanique tirée d'une source mesurée : un mot par pas, le fond bascule à chaque pas, coupes sèches, texte visible dès la 1re image, la fin retombe sur la 1re couleur pour boucler. Musique + bruitages, pas de voix ni de sous-titres. Mêmes règles éditoriales que le compte (aucun chiffre inventé).

## Structure obligatoire de la voix (tous les comptes, depuis le 23/10/2026)
1. **Accroche** (1re phrase de la scène 0).
2. **Tout de suite après, dans la même scène 0 : « Enregistre cette vidéo, tu vas en avoir besoin. »** (ou une variante : « Enregistre-la pour ne pas l'oublier. »). `tools/verifie.py` met une ERREUR si la scène 0 ne contient pas « enregistre ».
3. Les conseils (scènes suivantes).
4. **Fin : le mot-clé** (« Commente <mot> pour recevoir <offre> »), voir ci-dessous. Ne pas redemander d'enregistrer à la fin : la dernière scène est réservée au mot-clé.
Garder 100-120 mots au total : raccourcir les conseils plutôt que l'accroche.

## Rétention et accroche (tous les comptes, depuis le 23/10/2026, tiré des cours La Fabrik)
**Accroche** : écrire 3 accroches avec 3 techniques différentes parmi les 6 (rendre curieux, montrer le résultat d'abord, ouvrir une boucle, bousculer une croyance, prévenir d'une erreur, visuel fort), garder la plus naturelle à l'oral.
- 1re phrase de la voix : **14 mots maximum**, et elle entre direct dans le sujet. Jamais « Salut », « Bonjour », « Aujourd'hui je… », « Dans cette vidéo… » (ERREUR de `verifie.py`).
- Le texte de la scène 0 est lisible dès la 1re image (déjà contrôlé par `audit.py`).

**Les 3 règles de rétention** :
1. **Boucle ouverte** : l'accroche pose une question ou une promesse dont la réponse arrive seulement à la fin (« le 3e est celui que personne ne fait »). Ne jamais livrer la réponse dans la scène 0.
2. **Un nombre annoncé, tenu exactement, le meilleur en dernier** : « 3 réglages » à l'écran = 3 éléments, pas 4. `verifie.py` signale (ATTENTION) un nombre du hook qui ne correspond pas au nombre d'éléments d'une liste (`carnet`, `malin`).
3. **Un changement à l'écran toutes les 2 à 3 s** : texte qui apparaît, objet, couleur, cadrage. Donc des scènes courtes : **30 mots de voix maximum par scène** (≈ 12 s), mieux 15-25 ; et **12 mots affichés au même moment** visés (ATTENTION au-delà de 25 sur une scène). Utiliser `cue` / l'apparition progressive des éléments plutôt qu'un bloc de texte fixe.

**Un seul changement testé par reel** : quand on essaie quelque chose de nouveau (format, accroche, durée, son), on ne change que ça, et on l'écrit dans la `note` de la file (« test : … ») pour le bilan.

## Mot-clé à commenter (tous les comptes, depuis le 23/10/2026)
Chaque reel se termine par le mot-clé de son compte (`ressources/mots-cles.json` : `mot`, `offre`, `lien`). La **dernière scène** l'affiche (ex. `ctas` : « 💬 COMMENTE « PLAN » ») et sa `vo` dit « Commente plan pour recevoir le plan 7 jours gratuit ». `tools/verifie.py` met une ERREUR s'il n'est pas à l'écran **ou si la voix ne dit pas « Commente <mot> pour recevoir <offre> »** (obligatoire, décision de Goat du 23/10/2026). Mot long (PROGRAMME, PROMPTS…) : écrire « 💬 COMMENTE PROGRAMME » sans guillemets, sinon la ligne passe sous les boutons d'Instagram. `duel3d` et `fable2d` ajoutent eux-mêmes la carte de fin. Légende : finir par « 💬 Commente <MOT> et je t'envoie <offre> en DM » ; jamais le lien.

## carnet (PILOTE du 23/10/2026, tous comptes) — carnet manuscrit, couleurs claires
Exemple : `comptes/mentaldacier/posts/x10-trois-non-negociables/motion.json`. Page de carnet à petits carreaux ; le texte s'écrit à la main au rythme de la voix (Caveat), `**mot**` = coup de surligneur (jaune / corail / menthe en rotation), cases qui se cochent, post-it, boutons dessinés ; chaque scène est une nouvelle page qui glisse. Ordre des scènes LIBRE (en général 5) :
- `hook` : `titre` (`<br>` possible, ≤ 2 lignes), `sous` (optionnel)
- `note` : `titre`, `lignes` (2 à 4 lignes courtes, ≤ 28 caractères, précédées d'une flèche)
- `liste` : `titre`, `items` (2 à 4 cases qui se cochent, ≤ 30 caractères)
- `postit` : `texte` (3 lignes courtes séparées par `
`), `titre` (optionnel)
- `cta` : `titre`, `ctas` (2 boutons : « 🔖 Enregistre », « 💬 Commente MOT » sans guillemets)
Champ optionnel `couleurs` : {papier, encre, bureau, grille, postit, acc, surligneurs: [3 couleurs]}. Voix et structure obligatoire comme les autres formats.
