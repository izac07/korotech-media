# L'IA Entrepreneur · Claude au boulot — @lia.entrepreneur

- ID Instagram : 17841420788582578  ·  préfixe des posts : LIA
- Créneaux : 12:30 et 18:30 — 2 REELS par jour (décision de Goat du 18/10/2026 : plus aucun carrousel)
- Voix off : nPczCjzI2devNBz1zQrb (Brian). Dans les dialogues, Claude = Alice (Xb7hH8MSUJpSbSDYk0k2).
- Cible : freelances, indépendants, créateurs et gérants de TPE (25-45 ans) qui veulent gagner du temps avec Claude. Tutoiement.

## Rebranding du 24/10/2026 (validé par Goat) : « Claude au boulot »
Chaque reel montre **Claude faire une vraie tâche d'entrepreneur**, chez Goat, et comment le refaire. Détail : `rebranding.md`.
- La preuve, c'est le vrai système de Goat (6 comptes, 14 reels par semaine et par compte, écrits par Claude, montés en code, publiés par Make, avec veto). Jamais de résultat, de chiffre ou de témoignage inventé.
- La voix dit **« Claude »**, jamais « l'IA » (règle du 24/10/2026, contrôlée par `verifie.py`).
- Univers : un petit bureau de nuit où travaille **la mascotte Claude** (cube orange, visage en pixels). Pas de logo Claude/Anthropic : seulement le nom et notre mascotte.
- Couleurs : nuit `#141a3a`, orange `#ff7a3d`, jaune `#ffd23f`, vert `#2fd36b`, papier `#f4e7cf`, encre `#1b2147`.

## Format : 100 % studio3d (décision de Goat du 24/10/2026)
**Tous les reels LIA sont en `studio3d`** (voir tools/MOTION.md), comme `posts/x04-claude-monte-tes-reels/motion.json`. Pas de tuto, pas de dialogue, pas d'autre layout pour l'instant.
- 5-6 scènes, 30-45 s : problème (plan `large`, humeur `fatigue`, écran `bazar`, compteur) → Claude fait (plans `ecran` / `mascotte`, humeur `travail`, écrans `chat` / `montage` / `verif` / `export`) → résultat (`telephone`, `tampon`) → mot-clé (`carte`). Varier les plans, les écrans, les compteurs et les tampons d'un reel à l'autre.
- **Rendu sur le PC de Goat, pas dans le cloud** (carte graphique : ~3 min par reel contre ~25 min sans) : la routine du lundi écrit le motion.json, génère les voix et liste le reel dans `a-rendre/LIA-<date>.json` (statut `a_rendre`), sans rendre ni mettre en file. La tâche planifiée locale « Rendu 3D LIA » (lundi 8h, appli Claude ouverte sur le PC) lance `tools/rendre_lot.py`, regarde les images de contrôle, puis ajoute chaque reel à la file Make.

## Piliers
- **Claude fait à ta place** (40 %) : monter un reel, répondre à un client, faire un devis, trier ses mails, préparer sa semaine, relancer une facture.
- **Tutos Claude** (30 %) : projets, instructions, skills, connecteurs, tâches planifiées, Claude Code, les réflexes (/context, /compact, /clear, sous-agents).
- **Coulisses de mon système** (20 %) : ce qui tourne chez Goat, ce que ça coûte, ce qui casse et comment c'est réparé.
- **Erreurs et vérités** (10 %) : ce que Claude fait mal, pourquoi relire, les mythes.

## Fin de chaque reel
- Par défaut : « Commente IA pour recevoir les dix tâches à déléguer à Claude » (`ressources/mots-cles.json`).
- Quand la vidéo montre un prompt, un skill ou un modèle précis : le cadeau = cette chose, avec un mot-clé propre au reel (`"mot_cle"` dans le motion.json + message dans `ressources/messages-dm.md`, voir LIA-X03 / PROMPT). Ne créer un nouveau mot-clé que si la ressource existe vraiment (fichier écrit et en ligne).

## Règles spécifiques
- Pas de promesse de revenus ni de « deviens riche avec Claude ». Pas de chiffres d'abonnés/vues inventés : uniquement ce qui est vrai chez Goat.
- Toujours rappeler de relire / vérifier ce que produit Claude quand c'est pertinent.
- Ne jamais inventer d'études, de témoignages, ni de fonctions de Claude qui n'existent pas.

## Banque d'idées (rayer / retirer quand c'est fait)
- Claude répond à ton client mécontent (sans que tu t'énerves)
- Claude transforme un vocal de 2 min en devis propre
- Claude relance tes factures impayées (poliment)
- Claude trie 200 mails en 10 minutes : la méthode
- Claude prépare ton rendez-vous client
- Claude écrit ta page « À propos » en 10 minutes
- Claude résume une réunion et sort les actions
- Claude fait la FAQ de ta boutique
- Claude challenge ton idée : le prompt « consultant »
- Claude organise ta semaine en 3 piles (ce qui rapporte, ce qu'on délègue, ce qu'on supprime)
- Ma file d'attente : mon droit de veto avant publication (coulisses)
- Ce que me coûte vraiment ce système chaque mois (coulisses, chiffres réels seulement)
- Ce qui a cassé cette semaine, et comment Claude l'a réparé (coulisses)
- Le bilan du dimanche : Claude lit mes stats (coulisses)
- Créer une tâche planifiée avec Claude (tuto)
- Les instructions de projet que je donne à Claude (tuto)
- Claude perd le fil : /context, /compact, /clear (tuto, déjà fait en dialogue : refaire sous un autre angle)
- Les 3 erreurs qui rendent tes prompts nuls (erreurs)
- Mythe : Claude va remplacer les freelances (vérités)
- Pourquoi je relis encore tout : les vraies erreurs de Claude (vérités)
