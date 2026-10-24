# Rebranding @lia.entrepreneur — PROPOSITION (24/10/2026, à valider par Goat)

Rien n'est encore appliqué au README du compte ni à la routine du lundi : on valide d'abord la vidéo test
`posts/x04-claude-monte-tes-reels/reel.mp4` (format `studio3d`).

## 1. Le positionnement
**« Claude au boulot »** : chaque reel montre Claude faire une vraie tâche d'entrepreneur, en vrai, chez Goat.
- Pour qui : freelances, indépendants, créateurs, gérants de TPE (25-45 ans) qui veulent gagner du temps avec Claude. Tutoiement.
- La promesse : « Je te montre ce que Claude fait pour mon business, et comment le refaire. »
- La preuve : le vrai système de Goat (6 comptes, 14 reels par semaine et par compte, écrits par Claude, montés en code, publiés par Make, avec veto). Jamais de résultat inventé.

## 2. L'identité visuelle
- **Un univers** : un petit bureau de nuit (ville par la fenêtre, horloge, tasse) où travaille **la mascotte Claude**, un cube orange au visage en pixels. Pas de logo Claude/Anthropic : seulement le nom et notre propre mascotte.
- **Couleurs** : nuit bleu-violet `#141a3a`, orange Claude `#ff7a3d` (la mascotte, les accents), jaune `#ffd23f` (étiquettes), vert `#2fd36b` (validé, « prêt à poster »), papier crème `#f4e7cf` (bandeaux).
- **Typo** : Anton (bandeaux, compteurs, tampons), Archivo Black (sous-titres en étiquettes), Inter (écrans).
- **Signature** : bandeau papier en haut, badge compteur (HEURES 0 → 5, ÉTAPES 1/3…), sous-titres en étiquettes orange et jaune, tampon vert + confettis à la fin.

## 3. Les formats (par ordre de priorité)
1. **`studio3d`** (le nouveau visage du compte) : 30-45 s, un problème → Claude fait → résultat, avec la mascotte et l'écran du bureau.
2. **Tuto en étapes** (`interface` + `etape` + écrans `punch`) : « ÉTAPE 2/6 », pour les tutos plus denses.
3. **Dialogue toi ↔ Claude** (`interface` + `duo`, 2 voix) : pour les questions que tout le monde pose à Claude.
Les deux derniers prennent les couleurs du rebranding (champ `couleurs`).

## 4. Les piliers (centrés sur Claude)
- **Claude fait à ta place** (40 %) : monter un reel, répondre aux clients, faire un devis, trier ses mails, préparer sa semaine.
- **Tutos Claude** (30 %) : projets, skills, connecteurs, tâches planifiées, Claude Code, les réflexes (/context, /compact…).
- **Coulisses de mon système** (20 %) : ce qui tourne chez Goat, ce que ça coûte, ce qui casse.
- **Erreurs et vérités** (10 %) : ce que Claude fait mal, pourquoi relire, les mythes.

## 5. La fin de chaque reel
- Le cadeau = **la chose montrée dans la vidéo** (le prompt, le skill, le modèle), avec un mot-clé propre au reel quand c'est possible (`mot_cle` dans le motion.json + message dans `ressources/messages-dm.md`).
- Par défaut : « Commente IA » → les 10 tâches à déléguer à Claude.

## 6. Le profil (à changer à la main dans l'app)
- Nom affiché : **L'IA Entrepreneur · Claude au boulot**
- Bio (proposition) :
  « Je te montre ce que Claude fait pour mon business 🧡
  14 reels/semaine écrits par Claude, montés en code
  💬 Commente IA sous un reel → je t'envoie mes 10 tâches à déléguer »
- Photo de profil : la mascotte cube orange sur fond nuit (je peux la générer en image).
- Reels épinglés : X03 (14 reels sans monter), X04 (Claude monte tes reels), X02 (Claude déborde).

## 7. Ce que je change après ta validation
- `comptes/lia-entrepreneur/README.md` : nouveau concept, piliers, formats, couleurs.
- La routine du lundi (LIA) : produire en `studio3d` (et tuto/dialogue en alternance), aux nouvelles couleurs.
- `theme.json` du compte : nouvelles couleurs pour les anciens formats.
