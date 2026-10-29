# Reels « motion design » (formats validés par Goat le 16-17/10/2026)

Tous les reels de tous les comptes se font avec ce moteur. Plus de `tools/korotech.py reel` pour les reels.

```
python3 tools/motion.py <dossier>/motion.json <dossier>/reel.mp4
```

- Les voix doivent exister AVANT le rendu : `<dossier>/vo_0.mp3`, `vo_1.mp3`… (une par scène, même ordre que `scenes`).
- La durée de chaque scène = durée de sa voix + 0,9 s. Cible : **25 à 30 s au total**, soit **70 à 90 mots de voix off** au total (revu le 25/10/2026, voir « Structure obligatoire de la voix »).
- Les sous-titres mot à mot, la musique (`music_seed`, différent à chaque reel) et les bruitages sont automatiques.
- Toujours **5 scènes**, dans l'ordre indiqué pour le layout. Tous les champs texte sont obligatoires sauf mention contraire. Textes courts : ils sont affichés en gros.
- `**mot**` = mise en valeur (couleur / bandeau selon le layout).
- Euros : écris `100 €` normalement (l'espace insécable est ajouté).
- Vérifie visuellement 3 images du MP4 (ffmpeg -ss … -frames:v 1) : texte qui déborde ou chevauche → raccourcis le texte.
- Champs communs : `"id"`, `"layout"`, `"music_seed"`, `"handle"` (pseudo sans @), `"scenes"`.

## Chaîne de contrôle (depuis le 18/10/2026) — dans cet ordre
Python **3.12 minimum** (`motion.py` ne tourne pas en 3.11). Machine neuve / routine cloud : `source tools/setup.sh` puis utiliser `"$PY"` à la place de `python3`.
1. **Sujet** : `"$PY" tools/journal.py sujets --compte <handle>` puis `"$PY" tools/journal.py verifier --compte <handle> --sujet "…"` (alerte si sujet déjà traité).
2. **motion.json écrit** → `"$PY" tools/verifie.py <dossier>/motion.json` : 0 ERREUR obligatoire, corriger les ATTENTION. Un champ manquant n'est jamais anodin : le moteur afficherait le texte par défaut de l'exemple (ex. « STOP AUX 100 CRUNCHS »). Vérifie aussi 70-90 mots, longueurs, mots déclencheurs présents dans `vo`, règles du compte, `music_seed` jamais utilisé.
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
Exemple : `tools/exemples/boucle-exemple/motion.json`. À tester sur 2-3 posts par semaine maximum, à côté des reels de 25-30 s, puis comparer au bilan (x médiane).
Champs du haut : `pas` (secondes par mot, défaut 0.3), `tenue` (s de phrase complète, défaut 1.2), `couleurs` = 2 paires `[fond, texte]`, optionnels `police`, `taille` (px, défaut 120).
Scènes : 1 à 3 `{"type":"phrase","texte":"…"}`, 9 mots max par phrase (`**mot**` = souligné). Mécanique tirée d'une source mesurée : un mot par pas, le fond bascule à chaque pas, coupes sèches, texte visible dès la 1re image, la fin retombe sur la 1re couleur pour boucler. Musique + bruitages, pas de voix ni de sous-titres. Mêmes règles éditoriales que le compte (aucun chiffre inventé).

## Structure obligatoire de la voix (tous les comptes, revue le 25/10/2026)
Pourquoi elle a changé : courbe de rétention de MDA-X13 (1 003 vues, 11 enregistrements) : 75 % des gens encore là à 3 s, **30 % à 6 s**, pile pendant « Enregistre cette vidéo, et garde ces trois règles » dit juste après l'accroche ; après 6 s la courbe est presque plate. Le spectateur attend la réponse à l'accroche : lui demander d'enregistrer à ce moment-là le fait partir.
1. **Accroche** (1re phrase de la scène 0, 14 mots max).
2. **Tout de suite le 1er conseil / la 1re info concrète**, sans phrase d'annonce (« voici 3 règles », « garde bien ça »). La scène 0 fait **18 mots de voix au plus** pour que le plan change vers 3-4 s.
3. **Après le 1er conseil, en scène 1 ou 2 : « Enregistre cette vidéo »** dans une phrase courte qui relance (« Enregistre-la, la suite est pire. », « Enregistre, tu en auras besoin vers 23 h. »). `tools/verifie.py` met une ERREUR si « enregistre » est en scène 0 (hors dialogue) ou absent des scènes 1-2.
4. Les autres conseils (le meilleur en dernier).
5. **Fin : le mot-clé** (« Commente <mot> pour recevoir <offre> »), voir ci-dessous. Ne pas redemander d'enregistrer à la fin : la dernière scène est réservée au mot-clé.
Viser **70-90 mots au total (~25-30 s)** : la fin retient peu de monde, mieux vaut 2-3 conseils forts que 5. Dialogue toi ↔ Claude : la question en scène 0, la réponse commence en scène 1 et « enregistre » vient en scène 1 ou 2.

## Écriture parlée et fluide (Mental d'Acier depuis le 27/10/2026, règles travaillées avec Gemini, validées par Goat)
Pourquoi : Goat a regardé les reels X20-X43 : « l'enchaînement des phrases n'est pas fluide ». Les scripts empilaient des phrases-chocs sans lien (« Commence plus petit que tu crois. Prévois une version minimum… La régularité bat l'intensité. ») : ça sonne récité, pas parlé.
1. **Cause → conséquence → solution**, et chaque phrase s'accroche à la précédente par un lien oral (« parce que », « alors », « du coup », « comme ça », « le truc, c'est que »). Test : si on enlève une phrase, la suivante ne veut plus rien dire.
2. **Parler de ce que vit le spectateur**, pas de vérités générales : pas « L'organisation excessive bloque l'action », mais « Ton cerveau adore s'organiser, parce que ça a l'air de bosser sans rien risquer ».
3. **Le punch reste dans les 6 premiers mots** (image drôle ou piquante : « Ton chargeur dort mieux que toi », « Tu cours un marathon en claquettes »), puis la phrase enchaîne sans coupure sur la cause ou le conseil.
4. **« Enregistre ça » + à quoi ça sert, à la fin du conseil** : « Enregistre ça pour tes mauvais jours », « …avant ton prochain coup de flemme ». Jamais seul, jamais au milieu d'une idée.
5. **Le bloc 3 explique pourquoi ça marche avec du bon sens** (« Éloigner la tentation, c'est plus simple que compter sur ta volonté quand t'es crevé »), **zéro pseudo-science** (« recâbler le cerveau », dopamine, hormones).
6. **La question d'interaction vient en dernier, juste avant le mot-clé**, comme une relance de conversation : « Et toi, honnêtement… », « Dis-moi… ». Une seule question, pas de morale après.
7. Une seule phrase-choc par reel, au plus. Plus de citations empilées.
Gabarit (70-90 mots) : scène 0 = punch + cause (≤ 18 mots) · scène 1 = conseil concret + « Enregistre ça pour… » · scène 2 = pourquoi ça marche + question · scène 3 = mot-clé.
Exemple validé : « Ton lit t'a encore eu ce matin ? Tu relances le réveil trois fois et tu émerges en retard. / Pose ton réveil de l'autre côté de la pièce et prépare tes fringues la veille. Ça t'oblige à te lever direct sans réfléchir. Enregistre ça pour casser la mauvaise habitude. / En supprimant la réflexion au réveil, tu évites le débat qui te renvoie sous la couette. Tu relances le réveil combien de fois, d'habitude ? »
Gemini refuse les sujets à double sens (« la BR ») : il a servi à fixer ces règles, c'est Claude qui écrit les scripts.
**Format long (Mental d'Acier, 29/10/2026, validé par Goat)** : ~120-135 mots, 40-45 s, structure dans comptes/mentaldacier/ma-marque.md. Exemple « Deux heures du mat » : « Deux heures du mat, t'es encore sur ton tel… et c'est pas pour réviser. / Enregistre la vidéo et reste jusqu'au troisième truc, c'est lui qui marche vraiment. Mais d'abord, dis-moi en commentaire à quelle heure tu l'as lâché hier. / Le premier, c'est ton chargeur : tant qu'il est à côté du lit, t'as juste à tendre le bras. Du coup, ce soir, il dort ailleurs. / Le deuxième, c'est ton réveil : si c'est ton tel qui te réveille, c'est lui que tu regardes en premier. Prends un vrai réveil, et c'est réglé. / Avant le troisième, commente PLAN, et je t'envoie le plan 7 jours gratuit pour arrêter de procrastiner. / Et le troisième, celui que personne fait : tu décides avant. Genre, "si je suis encore dessus à minuit, dix pompes direct". Allez, dis-moi… là, il est quelle heure chez toi ? »
**Langage de la cible (29/10/2026)** : écrire dans la langue orale de l'audience du compte (Mental d'Acier : 18-30 ans, voir ma-marque.md « Langage de la cible ») ; le familier voulu n'est pas une faute. **Relecture** : verifie.py passe chaque « vo » dans LanguageTool et signale les fautes possibles (ATTENTION, en ignorant le registre familier et les mots de ressources/prononciation.json). **Prononciation** : le texte envoyé au scénario voix est celui de `tools/prononce.py <motion.json>` (dictionnaire ressources/prononciation.json), jamais « vo » brut ; les sous-titres gardent « vo ».

## Dire « Claude », pas « l'IA » (tous les comptes, décision de Goat du 24/10/2026)
Quand la voix parle de l'assistant qu'on utilise, elle dit **« Claude »** : « mets ton cours dans Claude », « demande à Claude », « Claude te fait les fiches ». Jamais « l'IA », « une IA », « l'intelligence artificielle » dans ce sens. Même chose à l'écran (titres, interrupteurs « Toi → Claude », chat). Seule exception : une comparaison de plusieurs outils (« 3 IA gratuites ») où « IA » désigne une catégorie ; on écrit alors le nom de chaque outil. `tools/verifie.py` met une ERREUR si une `vo` contient « l'IA » ou « l'intelligence artificielle », une ATTENTION pour « une IA ». Attention aux exemples de Claude : ne lui prêter que ce qu'il sait vraiment faire (aucune fonction inventée).

## Rétention et accroche (tous les comptes, depuis le 23/10/2026, tiré des cours La Fabrik)
**Accroche** : écrire 3 accroches avec 3 techniques différentes parmi les 6 (rendre curieux, montrer le résultat d'abord, ouvrir une boucle, bousculer une croyance, prévenir d'une erreur, visuel fort), garder la plus naturelle à l'oral.
- 1re phrase de la voix : **14 mots maximum**, et elle entre direct dans le sujet. Jamais « Salut », « Bonjour », « Aujourd'hui je… », « Dans cette vidéo… » (ERREUR de `verifie.py`).
- Le texte de la scène 0 est lisible dès la 1re image (déjà contrôlé par `audit.py`).

**Les 3 règles de rétention** :
1. **Boucle ouverte** : l'accroche pose une question ou une promesse dont la réponse arrive seulement à la fin (« le 3e est celui que personne ne fait »). Ne jamais livrer la réponse dans la scène 0.
2. **Un nombre annoncé, tenu exactement, le meilleur en dernier** : « 3 réglages » à l'écran = 3 éléments, pas 4. `verifie.py` signale (ATTENTION) un nombre du hook qui ne correspond pas au nombre d'éléments d'une liste (`carnet`, `malin`).
3. **Un changement à l'écran toutes les 2 à 3 s** : texte qui apparaît, objet, couleur, cadrage. Donc des scènes courtes : **30 mots de voix maximum par scène** (≈ 12 s), mieux 15-25 ; et **12 mots affichés au même moment** visés (ATTENTION au-delà de 25 sur une scène). Utiliser `cue` / l'apparition progressive des éléments plutôt qu'un bloc de texte fixe.

**Un seul changement testé par reel** : quand on essaie quelque chose de nouveau (format, accroche, durée, son), on ne change que ça, et on l'écrit dans la `note` de la file (« test : … ») pour le bilan.

## Déclencheur d'interaction (tous les comptes, décision de Goat du 25/10/2026)
Pourquoi : les commentaires, partages et identifications disent à Instagram de pousser un reel ; or le mot-clé de fin n'est vu que par 5-10 % des spectateurs (courbe de MDA-X13), d'où 0 commentaire PLAN sur 1 300 vues.
Chaque reel contient **UN déclencheur d'interaction posé au milieu** (scène 2 ou 3, jamais seulement à la fin), **écrit en gros à l'écran** (bandeau ou écran) et **dit par la voix en une phrase courte**, puis **repris en 1re ou 2e ligne de la légende**. Choisir celui qui colle au sujet :
1. **Choisir son camp** : « Team réveil à 6 h ou team snooze ? Commente 1 ou 2. » (zéro effort, le plus de réponses)
2. **Donner son score** : « Tu as tenu combien de secondes ? Écris ton temps. » (défis, chronos)
3. **Identifier quelqu'un** : « Identifie le pote qui fait ça tous les soirs 😂 » (partages, nouveaux spectateurs)
4. **Avouer** : « Sois honnête : ton record de snooze ? » (marche très bien avec l'humour)
5. **Débattre** : une phrase qui bouscule un peu (« Le sport le matin, c'est surcoté »), sans insulter ni viser une personne.
Le mot-clé (section suivante) reste dans la dernière scène : le déclencheur fait réagir, le mot-clé apporte le cadeau. Une seule question par reel (pas de déclencheur + 3 autres questions). Noter le déclencheur choisi dans la `note` de la file (« interaction : score ») pour comparer au bilan.

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

## interface (PILOTE du 23/10/2026, tous comptes) — cartes d'appli animées, fond pastel
Exemple : `posts/x06-pov-partiel-demain/motion.json`. Style « outil IA » : fond pastel qui bouge, une carte blanche par scène, une seule couleur d'accent, compteur de scènes en haut, sous-titres mot à mot (mot en cours en couleur). Un élément apparaît toutes les 1 à 2 s. Ordre des scènes LIBRE ; `titre` optionnel partout (`**mot**` = accent, `<br>` possible) :
- `hook` : `titre`, `sous` (pastille), `notif` optionnel = [icône, appli, texte] (notification de téléphone)
- `toggles` : `carte`, `carte_sous`, `items` (libellés ; `["Comprendre", false]` = reste « Toi ») : les interrupteurs basculent de « Toi » à « Claude » un par un
- `chat` : `messages` = [["moi"|"ia", texte]] tapés en direct
- `grille` : `cartes` (4 tuiles colorées qui apparaissent)
- `compteur` : `valeur` (chiffre réel uniquement), `label`, `lignes` = [[tag, texte]]
- `cta` : `titre`, `ctas` (2 boutons, le 2e en couleur)
Champ optionnel `couleurs` : {fond, encre, acc, tuiles: [4], blobs: [3], de: "Toi", a: "Claude"}.

### interface + dialogue (PILOTE du 24/10/2026) — « toi ↔ Claude », 2 voix
Exemple : `comptes/lia-entrepreneur/posts/x02-claude-deborde/motion.json` (aux couleurs de LIA, fond sombre). Construction tirée d'un reel à environ 200 000 vues (titouan.ia), RÉÉCRITE avec nos mots (jamais copier un script mot pour mot) :
1. L'accroche = une question que tout le monde pose à Claude, avec ses mots (« Claude… pourquoi tu perds le fil au bout d'une heure ? »).
2. Claude répond à la 1re personne, puis « Enregistre cette vidéo… t'as rien à noter, tout est à la fin » (la scène 1 peut porter le « enregistre »).
3. Une image qu'on comprend tout de suite (scène `jauge` : un bocal qui se remplit).
4. Chaque partie est ouverte par une question courte de « toi » (« Et si tu tournes en rond ? ») : c'est ce qui fait tenir 50 à 80 s.
5. Carte récap (`grille`), puis le mot-clé.
Scènes en plus : `duo` {qui: "moi"|"claude", bulle (phrase courte affichée, `**mot**`, `<br>`)} : deux personnages, celui qui parle bouge la bouche ; `jauge` {labels, de, a, unite?, titre?}.
Chaque scène a `qui` (voix) : **moi = Brian (nPczCjzI2devNBz1zQrb), claude = Alice (Xb7hH8MSUJpSbSDYk0k2)**. Dialogue : 120 à 200 mots de voix.
Thème sombre / couleurs d'un compte : `couleurs` accepte aussi carte, carte_encre, ligne, ligne2, doux, sur (texte sur l'accent), bulle, tuile_encre, bord, acc_texte, police, espacement, peau, cheveux, pull, mascotte, noms. `fond` accepte un fond CSS complet (dégradés, quadrillage).

### interface + tuto en étapes (PILOTE du 24/10/2026)
Exemple : `comptes/lia-entrepreneur/posts/x03-14-reels-sans-monter/motion.json`. Tiré de deux reels qui ont fait plus de commentaires que de likes (3 200 et 10 400 commentaires) :
- `"etape": "2/6"` sur n'importe quelle scène → en-tête « ÉTAPE 2 / 6 » + barre en segments (les étapes faites sont pleines).
- Scène `punch` {titre, sous?} : écran plein cadre sur la couleur d'accent (« 14 reels par semaine. », « C'est tout. »). Une en accroche, une avant la fin.
- `couleurs.sous_titres` : taille des sous-titres en px (64 conseillé, défaut 52).
- `de` / `a` sur une scène `toggles` : libellés des interrupteurs pour cette scène (« Refusé » → « Validé »).
- **Le cadeau = la chose exacte montrée dans la vidéo** (le prompt, le skill). Mot-clé propre au reel : champ `"mot_cle": {"mot", "offre", "lien"}` (remplace celui de `ressources/mots-cles.json` pour ce reel ; `verifie.py` le contrôle) + ajouter le message DM dans `ressources/messages-dm.md`.

## studio3d (PILOTE du 24/10/2026, rebranding L'IA Entrepreneur) — petite scène 3D low poly
Moteur : `tools/studio3d.py` (appelé par `motion.py`, layout `"studio3d"`). Exemple : `comptes/lia-entrepreneur/posts/x04-claude-monte-tes-reels/motion.json`.
Bureau de nuit (ville, horloge qui s'emballe pendant le « bazar »), mascotte cube orange « Claude », écran qui change selon la scène, téléphone pour la fin ; la caméra glisse d'un plan à l'autre. Habillage : bandeau papier en haut, badge compteur, sous-titres en étiquettes orange et jaune (un mot à la fois), tampon vert + confettis, carte de fin.
Scènes : `type` = plan (`large` | `ecran` | `mascotte` | `telephone`), `vo`, `bandeau` (court, majuscules automatiques), optionnels :
`ecran` {type: `bazar` | `chat` (messages) | `montage` | `verif` (lignes) | `export`, titre}, `compteur` {label, de, a, fmt « #/3 »}, `humeur` (`fatigue` | `normal` | `travail` | `content`), `tampon` (« PRÊT À POSTER »), `carte` [ligne 1, ligne 2] (carte de fin du mot-clé).
Histoire conseillée en 5-6 scènes, 30-45 s : problème (large, fatigue, bazar, compteur) → étapes où Claude fait (ecran / mascotte) → résultat (telephone, tampon) → mot-clé (carte).
studio3d v3 (24/10/2026) : three.js 0.186.1 en modules (`tools/assets/three186/`, chargés en data: URLs ; tone mapping Neutral, occlusion ambiante GTAO, éclairage d'environnement RoomEnvironment, matériaux standard), vrais modèles CC0 du Kenney Furniture Kit (`tools/assets/modeles/`, licence dans le dossier : bureau, chaise, clavier, souris, lampe, plantes, bibliothèque), ombres douces, lueur (bloom), profondeur de champ, mascotte arrondie qui s'écrase en sautant, poussière dans la lumière de la lampe. Rendu : ~3 min pour 37 s avec la carte graphique du PC de Goat (d3d11, choisi automatiquement sous Windows par korotech.gl_args), ~25 min sans carte graphique (SwiftShader, routines cloud ; mode allégé automatique : pas de flou, ombres simples).
Variante Mental d'Acier (format principal du compte depuis le 25/10/2026) : décor `chambre_mda`, `couleurs.personnage: "humain"` (pas de mascotte), `lumiere` nuit → aube, écrans `liste` / `calendrier` / `timer` sur le tableau au mur, ton humoristique à double sens (voir `comptes/mentaldacier/ma-marque.md`). Copier `comptes/mentaldacier/posts/x14-3d-jour1-sans-br/motion.json` (couleurs comprises). Les reels studio3d de LIA et de MDA sont rendus sur le PC de Goat via `a-rendre/` + `tools/rendre_lot.py`, jamais dans le cloud.
