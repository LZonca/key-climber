# KeyScale - Jeu de Réflexes

KeyScale est un jeu de réflexes en Python où vous devez appuyer sur les touches correspondant aux lettres qui apparaissent à l'écran tout en évitant la lave qui monte.

## Caractéristiques

- Deux modes de jeu : graphique (avec Pygame) et CLI (interface en ligne de commande)
- Trois niveaux de difficulté : facile, moyen et difficile
- Système de score avec classement en ligne sur keyscale.lzonca.fr
- Interface utilisateur améliorée avec animations et effets visuels
- Mode tutoriel pour apprendre à jouer
- Un laTeX pour la documentation
- Un diagramme UML de classe

## Installation

```bash
git clone https://github.com/LZonca/KeyScale.git
cd KeyScale
```

## Lancement

Pour lancer le jeu en mode graphique :
```bash
python Main.py
```

Pour lancer le jeu en mode CLI :
```bash
python CLI/cli_main.py
```

## Commandes

- Appuyez sur les touches correspondant aux lettres pour éliminer les obstacles
- ESC : Pause
- N : Changer de nom
- M : Retour au menu principal
- T : Paramètres
- Q : Quitter

## Paramètres

Vous pouvez ajuster :
- Volume de la musique du menu
- Volume de la musique du jeu
- Volume des effets sonores
- Taille de la police
- Taille des obstacles

## Scores

Les meilleurs scores sont sauvegardés en ligne et consultables sur keyscale.lzonca.fr. Une synchronisation est effectuée automatiquement lorsqu'une connexion internet est disponible.