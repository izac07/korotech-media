# Monter tes vidéos avec Claude : le skill + le guide de style

Cadeau du mot-clé **MONTAGE** (reel LIA-X06). C'est le principe exact de mon système : Claude Code écrit le montage en code (coupes, sous-titres, musique) au lieu de passer des heures sur une timeline.

## Ce qu'il te faut
- **Claude Code** (dans l'application Claude pour ordinateur, onglet Code).
- **ffmpeg** installé sur ton ordinateur (outil gratuit de montage en ligne de commande ; Claude peut t'aider à l'installer).
- Un dossier par vidéo avec tes rushs, tes images et ta voix off.

## 1. Ton guide de style (à copier dans `guide-style.md`, puis à adapter)
```
# Guide de style de mes vidéos
- Format : vertical 1080x1920, 30 images/s, 25 à 40 s.
- Accroche : le sujet est dit dans la 1re seconde, texte lisible dès la 1re image.
- Une coupe par phrase de la voix off. Jamais plus de 3 s sans changement à l'écran.
- Sous-titres : mot par mot, police grasse, 2 à 4 mots à l'écran, mot important en couleur.
- Couleurs de ma marque : fond #……, accent #……, texte #……
- Musique : sous la voix (-18 dB), coupée pendant l'accroche si elle gêne.
- Fin : rappel du mot-clé à commenter, à l'écran ET à l'oral.
```

## 2. Le skill de montage (à copier dans `.claude/skills/montage-video/SKILL.md`)
```
---
name: montage-video
description: Monte une vidéo verticale à partir des rushs, images et voix off du dossier, en suivant guide-style.md. À utiliser quand je dis « monte la vidéo ».
---
1. Lis guide-style.md et la liste des fichiers du dossier (rushs, images, voix).
2. Transcris la voix off avec les temps de chaque mot (ou utilise le script fourni).
3. Fais un plan de montage : pour chaque phrase, quel rush ou quelle image, et quel texte affiché. Montre-le-moi avant de rendre.
4. Monte en code avec ffmpeg : recadrage 9:16, coupes, sous-titres mot par mot, musique sous la voix.
5. Regarde 3 images de la vidéo finale (début, milieu, fin) et corrige ce qui déborde ou se lit mal.
6. Donne-moi le fichier final et la liste de ce que tu as fait.
```

## 3. La phrase à envoyer
> Monte la vidéo en suivant mon guide de style.

## Pour retoucher
Redemande simplement : « rends l'intro plus rapide », « les sous-titres plus gros », « coupe le silence à 0:12 ». Il refait le rendu.

Relis toujours la vidéo avant de la publier.
