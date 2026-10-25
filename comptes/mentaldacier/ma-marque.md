# Ma marque — Mental d'Acier (@mentaldacier2030)

Fiche lue par les skills (createur-reel, legende-instagram, usine-contenu…) avant d'écrire. Source de vérité détaillée : `README.md` du compte, `tools/MOTION.md` et `ressources/mots-cles.json`.

## Business
- **Ce que c'est :** un compte Instagram (reels) sur la discipline et les habitudes, sans dépendre de la motivation.
- **Promesse :** construire de la discipline et des habitudes qui tiennent, une petite étape à la fois.
- **Produit payant prévu :** planner + défi 30 jours (9-19 €). Pas encore en vente : ne jamais citer de prix ni de lien d'achat.
- **Objectif actuel :** grandir (vues, abonnés) et récolter des contacts via la ressource gratuite.

## Client idéal
- 18-30 ans, étudiants ou jeunes actifs, qui veulent plus de discipline pour leurs études, le sport ou leurs projets.
- Ce qu'il vit : il repousse, scrolle, commence le lundi et lâche au bout de 3 jours, se compare aux autres.
- Ce qu'il veut : une méthode simple qui marche même les jours sans envie, et se sentir fier de lui.

## Voix (nouvelle DA depuis le 25/10/2026 : humour à double sens)
- **Tutoiement**, ton **drôle, complice et direct**, phrases courtes : le grand frère qui te charrie, puis te donne la vraie méthode.
- **Accroche à double sens ou en argot** (« Ce que tu fais à 22 h… », « Jour 1 sans la BR »), puis **chute qui ramène à la discipline**. Le spectateur sourit, se reconnaît, commente.
- **Toujours codé, jamais explicite** : aucun mot sexuel, aucune drogue nommée, rien de vulgaire à l'écran ni dans la voix (sinon Instagram coupe la diffusion). L'argot connu des 16-25 ans est OK (« la BR », « l'onglet privé », « scroller jusqu'à 3 h »).
- Le fond reste sérieux : un conseil concret par scène, exigeant mais bienveillant, on ne culpabilise jamais et on ne fait pas la morale.
- Pourquoi : MDA-X13 (« Ce que tu fais à 22 h », 3D sombre) = ~900 vues en une journée et un commentaire blagueur (« Il est 4h20 chez moi 😂 »), record du compte (avant : 200 max).
- Phrases-repères du compte : « Fait vaut mieux que parfait. », « Juste 2 minutes. », « Ce n'est pas une question de volonté, c'est une question d'environnement. »

## Mots et idées interdits
- Culte de la souffrance et injonctions toxiques : « dormir 4 h », « no excuses », « no pain no gain », « si tu échoues c'est que tu ne veux pas assez ».
- « Détox dopamine » / « vider sa dopamine » : on parle de « réduire les plaisirs faciles ».
- Conseils de santé mentale : si détresse, inviter à en parler à un proche ou à un professionnel.
- Chiffres, études, témoignages ou résultats inventés ; promesses de transformation garantie.
- Promesses santé non prouvées (« +X % de testostérone », « superpouvoirs », « ton cerveau se reprogramme en 7 jours ») : on parle de ce qu'on remarque (sommeil, temps récupéré, parole tenue), pas de biologie.
- Humour qui humilie (le physique, les filles/les mecs, l'orientation) : on rit de la situation, jamais d'une personne.
- Le hashtag #nofap et les mots explicites (dans la voix, à l'écran et dans la légende).
- Citations attribuées si l'auteur n'est pas certain (sinon formulation originale, sans nom).
- Tics d'écriture « IA » à éviter : « Dans un monde où… », « Plongeons dans… », « Il est important de noter que… », « En conclusion », « booster », « game changer », listes d'emojis à chaque ligne.

## Mot-clé et ressource gratuite
- **Mot-clé à commenter : PLAN**
- **Ressource :** « Le plan 7 jours pour arrêter de repousser » (PDF gratuit) : https://izac07.github.io/korotech-media/ressources/mentaldacier/plan-7-jours-arreter-de-repousser.pdf
- Envoyée **en DM** par Goat (message prêt dans `ressources/messages-dm.md`). **Jamais le lien dans la légende.**

## Structure obligatoire de chaque reel (voix)
1. **Accroche** (une phrase qui arrête le pouce).
2. **Tout de suite le 1er conseil** (pas de « voici 3 règles ») ; scène 0 = 18 mots max, changement de plan vers 3 s.
3. **Puis, en scène 1 ou 2 : « Enregistre cette vidéo »** dans une phrase courte qui relance. Jamais juste après l'accroche : sur X13, 75 % des gens étaient là à 3 s et 30 % à 6 s, pile pendant ce « Enregistre ».
4. **Les autres conseils** (une idée nouvelle par phrase, le meilleur en dernier). Total 70-90 mots, ~25-30 s.
5. **Fin : « Commente plan pour recevoir le plan 7 jours gratuit. »** (écran + voix)

Légende : accroche (le double sens peut y rester), bénéfice, « 🔖 Enregistre… », puis « 💬 Commente PLAN et je t'envoie le plan 7 jours gratuit en DM. », et 5 hashtags max (#mentaldacier #discipline #routinedusoir #selfcontrol #procrastination…).

## Formats
- **Format principal depuis le 25/10/2026 : studio3d « chambre sombre »** (layout `studio3d`, décor `chambre_mda`, personnage humain gris, lumière nuit → aube, habillage noir / blanc / or, voix Brian). 70-90 mots, 4-5 scènes, ~25-30 s (X13 et X14 suivent encore l'ancienne structure : copier leurs couleurs et décors, pas leur scène 0). Exemples complets : `posts/x13-3d-22h/motion.json` (~900 vues) et `posts/x14-3d-jour1-sans-br/motion.json`. Rendu sur le PC de Goat (carte graphique) : la routine cloud l'écrit et le liste dans `a-rendre/MDA-<date>.json`.
  - Scènes : `large` (accroche, souvent au lit avec `humeur: telephone`, `lumiere: nuit`), `mascotte` (plan sur le personnage), `ecran` (tableau au mur : `liste` {titre, lignes}, `calendrier` {jours, jusqua}, `timer` {exo, secondes}), fin en `lumiere: aube` avec `humeur` `sport` puis `content` + `carte` du mot-clé. `tampon` pour une victoire (« 7 / 7 »).
  - Humeurs du personnage : `telephone` / `fatigue` / `dort` / `triste` (au lit), `normal` (debout), `sport` (pompes), `content` (bras levés).
- Anciens formats (ne plus produire sauf demande de Goat) : `manifeste3d`, duel 3D (`tools/duel3d.py`), fable 2D, carnet.

## Piliers (nouvelle DA)
- POV du soir / habitudes cachées, à double sens (téléphone au lit, BR, onglet privé, scroll à 3 h, réveil repoussé) — 40 %
- « Jour 1 sans… » / défis en N jours, racontés avec humour — 25 %
- Méthodes anti-procrastination avec une chute drôle (« je commence lundi », motivation de 3 jours) — 20 %
- Phrases fortes / vérités qui piquent — 15 %

## Banque d'accroches à double sens (rayer quand c'est fait)
- ~~Ce que tu fais à 22 h décide de ta journée~~ (X13) · ~~Jour 1 sans la BR~~ (X14)
- Il est 4 h 20 et tu es encore dessus. (→ le téléphone)
- Ce que tu fais au lit après minuit te ruine. (→ scroller)
- Tu le fais tous les soirs en cachette. (→ repousser le réveil de 5 minutes)
- Ta mère sait ce que tu fais à 23 h ? (→ des vidéos de motivation au lieu d'agir)
- Tu tiens combien de temps, toi ? (→ sans regarder ton téléphone)
- 3 minutes. C'est tout ce que ça prend. (→ démarrer une tâche, règle des 2-3 minutes)
- L'onglet privé ne protège pas de ça. (→ le temps perdu)
- Tu finis toujours trop vite. (→ tes habitudes, abandonnées au jour 3)
- Jour 3 sans la BR : ton cerveau négocie. (suite de X14)
- Jour 30 sans la BR : ce qui a changé. (suite, sans promesse santé)
- Elle t'a laissé en vu. Ton réveil aussi. (→ le snooze)
- Tu le touches 150 fois par jour. (→ le téléphone ; chiffre = exemple, pas une étude)
- Ton lit t'a encore eu ce matin. (→ se lever à la 1re sonnerie)
- Tout le monde le fait, personne n'en parle. (→ procrastiner en « s'organisant »)
- Lundi, promis, tu arrêtes. (→ le piège du « je commence lundi »)
- Tu as encore craqué hier soir. (→ comment reprendre sans tout lâcher)
- Je sais ce que tu as fait dans ta chambre. (→ rien, et c'est le problème)
- La salle de bain à 2 h du matin, sérieux ? (→ le téléphone aux toilettes)
- Seul dans ta chambre, tu es un autre homme. (→ la discipline quand personne ne regarde)

## Publication
- 2 reels par jour au maximum (créneaux 07:30 et 21:30), espacés d'au moins 6 h. Pas de rafale.
- Rien n'est publié sans passer par la file Make (veto de Goat) ou sans son accord explicite.
