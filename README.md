<div align="center">

# FingerFlow

*ContrÃ´lez votre ordinateur d'un simple geste de la main*

**Luisoni Tom** â€¢ **Marchand Luc** â€¢ **Weber Jason**

---

</div>

## Description du projet

Notre projet consiste Ã  dÃ©velopper un programme Python utilisant MediaPipe pour la reconnaissance de la main en temps rÃ©el. GrÃ¢ce Ã  la dÃ©tection des points clÃ©s de la main (landmarks), l'utilisateur pourra interagir avec son ordinateur, en simulant des actions telles que :

- le dÃ©placement du curseur (comme une souris)
- les diffÃ©rents clics par gestes
- le dessin dans l'air avec un doigt

L'application exploitera la webcam pour capter les mouvements de la main et traduire ces gestes en commandes interactives. Ce projet combine des domaines variÃ©s tels que :

- la vision par ordinateur
- l'interaction homme-machine
- la crÃ©ativitÃ© numÃ©rique

Le programme sera exÃ©cutÃ© directement sous Windows, afin de garantir un accÃ¨s plus simple et plus fiable Ã  la camÃ©ra, contrairement Ã  l'environnement WSL, qui prÃ©sente certaines limitations Ã  ce niveau.

## Objectifs

Les objectifs suivants ont Ã©tÃ© parfaitement atteint :

- RÃ©ussir Ã  dÃ©tecter une main avec prÃ©cision Ã  l'aide de MediaPipe
- InterprÃ©ter les mouvements et gestes pour simuler des actions (dÃ©placement du curseur, clic, dessin)
- CrÃ©er une interface intuitive et fluide pour permettre une interaction naturelle
- Explorer les possibilitÃ©s de contrÃ´le sans contact dans un environnement desktop

---


### ContrÃ´les de base - Mode Normal (N)

1. **DÃ©placement du curseur**
   - Levez votre main face Ã  la webcam
   - Le curseur suivra le centre de votre paume

2. **Clic gauche**
   - Pincez avec votre pouce et votre index
   - Le clic s'exÃ©cutera automatiquement

3. **Clic droit**
   - Pincez avec votre pouce et votre majeur
   - Le clic droit s'exÃ©cutera automatiquement

4. **AccÃ©der au sÃ©lecteur de mode**
   - Fermez la main
   - Les touches **N**, **D**, **Z**, **S**, **P** permetent d'activer les diffÃ©rents modes

#### Modes disponibles :

- **Mode Normal (N)** â€” Mode par dÃ©faut
  - DÃ©placement du curseur et clics standard

- **Mode Dessin (D)**
   - Lance l'application Paint (mspaint.exe)
  - Permet de dessiner avec mouvements naturels de la main
  - Mouvements lissÃ©s pour une meilleure prÃ©cision

- **Mode Zoom (Z)**
  - Pincement pouce-index : Zoom avant (Ctrl++)
  - Pincement pouce-majeur : Zoom arriÃ¨re (Ctrl+-)
  - Parfait pour naviguer dans des documents ou des images

- **Mode Scroll (S)**
  - Pincement pouce-index : Scroll vers le bas
  - Pincement pouce-majeur : Scroll vers le haut
  - IdÃ©al pour parcourir des listes ou des pages web

- **Mode Pause (P)**
  - Le curseur arrÃªte de se dÃ©placer
  - Les clics sont dÃ©sactivÃ©s
  - IdÃ©al pour faire des pauses sans fermer le programme

En plus de ces modes, la touche **T** permet de basculer l'affichage de la fenÃªtre du mode "Always On Top" (toujours visible) Ã  "Hide" (cachÃ©e)

---

### Conseils d'utilisation

- **LuminositÃ©** : Assurez-vous que votre environnement est bien Ã©clairÃ© et pas Ã  contre jour, pour une meilleure dÃ©tection
- **Distance** : Maintenez votre main Ã  une distance de 30-60 cm de la webcam
- **StabilitÃ©** : Utilisez un support pour la webcam ou maintenez-la stable
- **Fond** : Un fond non chargÃ© amÃ©liore la qualitÃ© de la dÃ©tection
- **Performances** : Le programme optimise automatiquement la prioritÃ© du processus pour minimiser la latence

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

## DÃ©veloppeur

### PrÃ©requis
- Python 3.11 ou supÃ©rieur
- Une webcam fonctionnelle
- Windows (le programme est optimisÃ© pour Windows)

### Ã‰tapes d'installation

1. **Cloner le repository**
   ```bash
   git clone <url-du-repo>
   cd mini-projet-fingerflow
   ```

2. **Installer l'environnement virtuel et dÃ©pendances**
   
   Le projet utilise `uv` pour gÃ©rer les dÃ©pendances. Si vous n'avez pas `uv` installÃ© :
   ```bash
   # Installer Python 3.11 via uv
   uv python install 3.11
   ```

3. **Synchroniser les dÃ©pendances**
   ```bash
   uv sync
   ```

### Lancement du programme

#### Lancement de FingerFlow en temps rÃ©el

```bash
uv run fingerflow
```

Le programme dÃ©marrera avec la dÃ©tection de main activÃ©e et affichera le flux vidÃ©o avec les landmarks dÃ©tectÃ©s.

#### ArrÃªt du programme

Pour arrÃªter le programme, il suffit simplement de cliquer sur le bouton `Quit` de la fenÃªtre

---

### Gestion des dÃ©pendances

#### Ajouter une nouvelle dÃ©pendance

```bash
uv add <nom-du-package>
```

#### Mettre Ã  jour toutes les dÃ©pendances

```bash
uv sync
```

#### Lancer un script spÃ©cifique

```bash
uv run <script-ou-commande>
```

## CrÃ©ation d'un installateur Windows (x64)

### PrÃ©requis
- Windows 64-bit
- Inno Setup installÃ© (version standard)

### Ã‰tapes

1. **Installer les dÃ©pendances de build**
   ```bash
   uv sync --extra build
   ```

2. **GÃ©nÃ©rer l'exÃ©cutable**
   ```bash
   uv run pyinstaller packaging/fingerflow.spec
   ```

3. **GÃ©nÃ©rer l'installateur**
   - Ouvrir `packaging/installer.iss` dans Inno Setup puis cliquer sur **Compile**
   - Ou en ligne de commande :
     ```bash
     iscc packaging/installer.iss
     ```

L'installateur final est crÃ©Ã© dans `packaging/dist-installer/FingerFlow-Setup.exe`.
Il crÃ©e un raccourci bureau et utilise l'icÃ´ne `fingerflow/ui/Logo_fingerflow_V2.ico`.

## DÃ©pannage

**Le programme ne dÃ©marre pas :**
- VÃ©rifiez que Python 3.11 est installÃ© : `uv python list`
- VÃ©rifiez que la webcam est connectÃ©e et fonctionnelle
- RÃ©exÃ©cutez `uv sync` pour vous assurer que toutes les dÃ©pendances sont correctement installÃ©es

**La dÃ©tection de main ne fonctionne pas :**
- AmÃ©liorez l'Ã©clairage de votre environnement
- VÃ©rifiez que votre webcam fonctionne (testez-la avec une autre application)
- Assurez-vous que le modÃ¨le `hand_landmarker.task` est prÃ©sent dans le dossier `model/`

**Le curseur n'est pas prÃ©cis :**
- Ajustez la distance de votre main par rapport Ã  la webcam
- RÃ©duisez la luminositÃ© si elle est excessive


