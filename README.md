<div align="center">

# FingerFlow

*Contrôlez votre ordinateur d'un simple geste de la main*

**Luisoni Tom** • **Marchand Luc** • **Weber Jason**

---

</div>

## Description du projet

Notre projet consiste à développer un programme Python utilisant MediaPipe pour la reconnaissance de la main en temps réel. Grâce à la détection des points clés de la main (landmarks), l'utilisateur pourra interagir avec son ordinateur, en simulant des actions telles que :

- le déplacement du curseur (comme une souris)
- les différents clics par gestes
- le dessin dans l'air avec un doigt

L'application exploitera la webcam pour capter les mouvements de la main et traduire ces gestes en commandes interactives. Ce projet combine des domaines variés tels que :

- la vision par ordinateur
- l'interaction homme-machine
- la créativité numérique

Le programme sera exécuté directement sous Windows, afin de garantir un accès plus simple et plus fiable à la caméra, contrairement à l'environnement WSL, qui présente certaines limitations à ce niveau.

## Objectifs

Les objectifs suivants ont été parfaitement atteint :

- Réussir à détecter une main avec précision à l'aide de MediaPipe
- Interpréter les mouvements et gestes pour simuler des actions (déplacement du curseur, clic, dessin)
- Créer une interface intuitive et fluide pour permettre une interaction naturelle
- Explorer les possibilités de contrôle sans contact dans un environnement desktop

---


### Contrôles de base - Mode Normal (N)

1. **Déplacement du curseur**
   - Levez votre main face à la webcam
   - Le curseur suivra le centre de votre paume

2. **Clic gauche**
   - Pincez avec votre pouce et votre index
   - Le clic s'exécutera automatiquement

3. **Clic droit**
   - Pincez avec votre pouce et votre majeur
   - Le clic droit s'exécutera automatiquement

4. **Accéder au sélecteur de mode**
   - Fermez la main
   - Les touches **N**, **D**, **Z**, **S**, **P** permetent d'activer les différents modes

#### Modes disponibles :

- **Mode Normal (N)** — Mode par défaut
  - Déplacement du curseur et clics standard

- **Mode Dessin (D)**
   - Lance l'application Paint (mspaint.exe)
  - Permet de dessiner avec mouvements naturels de la main
  - Mouvements lissés pour une meilleure précision

- **Mode Zoom (Z)**
  - Pincement pouce-index : Zoom avant (Ctrl++)
  - Pincement pouce-majeur : Zoom arrière (Ctrl+-)
  - Parfait pour naviguer dans des documents ou des images

- **Mode Scroll (S)**
  - Pincement pouce-index : Scroll vers le bas
  - Pincement pouce-majeur : Scroll vers le haut
  - Idéal pour parcourir des listes ou des pages web

- **Mode Pause (P)**
  - Le curseur arrête de se déplacer
  - Les clics sont désactivés
  - Idéal pour faire des pauses sans fermer le programme

En plus de ces modes, la touche **T** permet de basculer l'affichage de la fenêtre du mode "Always On Top" (toujours visible) à "Hide" (cachée)

---

### Conseils d'utilisation

- **Luminosité** : Assurez-vous que votre environnement est bien éclairé et pas à contre jour, pour une meilleure détection
- **Distance** : Maintenez votre main à une distance de 30-60 cm de la webcam
- **Stabilité** : Utilisez un support pour la webcam ou maintenez-la stable
- **Fond** : Un fond non chargé améliore la qualité de la détection
- **Performances** : Le programme optimise automatiquement la priorité du processus pour minimiser la latence

---
---
---

## Installation

1. Ouvrir l'onglet **Releases** sur GitHub
2. Telecharger `FingerFlow-Setup.exe` (version Windows)
3. Lancer l'installateur et suivre l'assistant
4. Demarrer l'app via le raccourci bureau

---
---
---

## Développeur

### Prérequis
- Python 3.11 ou supérieur
- Une webcam fonctionnelle
- Windows (le programme est optimisé pour Windows)

### Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone <url-du-repo>
   cd mini-projet-fingerflow
   ```

2. **Installer l'environnement virtuel et dépendances**
   
   Le projet utilise `uv` pour gérer les dépendances. Si vous n'avez pas `uv` installé :
   ```bash
   # Installer Python 3.11 via uv
   uv python install 3.11
   ```

3. **Synchroniser les dépendances**
   ```bash
   uv sync
   ```

### Lancement du programme

#### Lancement de FingerFlow en temps réel

```bash
uv run fingerflow
```

Le programme démarrera avec la détection de main activée et affichera le flux vidéo avec les landmarks détectés.

#### Arrêt du programme

Pour arrêter le programme, il suffit simplement de cliquer sur le bouton `Quit` de la fenêtre

---

### Gestion des dépendances

#### Ajouter une nouvelle dépendance

```bash
uv add <nom-du-package>
```

#### Mettre à jour toutes les dépendances

```bash
uv sync
```

#### Lancer un script spécifique

```bash
uv run <script-ou-commande>
```

## Création d'un installateur Windows (x64)

### Prérequis
- Windows 64-bit
- Inno Setup installé (version standard)

### Étapes

1. **Installer les dépendances de build**
   ```bash
   uv sync --extra build
   ```

2. **Générer l'exécutable**
   ```bash
   uv run pyinstaller packaging/fingerflow.spec
   ```

3. **Générer l'installateur**
   - Ouvrir `packaging/installer.iss` dans Inno Setup puis cliquer sur **Compile**
   - Ou en ligne de commande :
     ```bash
     iscc packaging/installer.iss
     ```

L'installateur final est créé dans `packaging/dist-installer/FingerFlow-Setup.exe`.
Il crée un raccourci bureau et utilise l'icône `fingerflow/ui/Logo_fingerflow_V2.ico`.

## Dépannage

**Le programme ne démarre pas :**
- Vérifiez que Python 3.11 est installé : `uv python list`
- Vérifiez que la webcam est connectée et fonctionnelle
- Réexécutez `uv sync` pour vous assurer que toutes les dépendances sont correctement installées

**La détection de main ne fonctionne pas :**
- Améliorez l'éclairage de votre environnement
- Vérifiez que votre webcam fonctionne (testez-la avec une autre application)
- Assurez-vous que le modèle `hand_landmarker.task` est présent dans le dossier `model/`

**Le curseur n'est pas précis :**
- Ajustez la distance de votre main par rapport à la webcam
- Réduisez la luminosité si elle est excessive

