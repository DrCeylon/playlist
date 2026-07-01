# Publication du wiki GitHub

Ce dossier contient la documentation wiki complète en français.

## Publier sur le wiki GitHub

Le wiki GitHub est un dépôt Git séparé. Pour publier :

```bash
# 1. Cloner le wiki (une seule fois — skip si playlist.wiki existe déjà)
git clone https://github.com/DrCeylon/playlist.wiki.git

# 2. Copier les fichiers depuis la racine du dépôt playlist
#    (tu dois être dans le dossier qui CONTIENT wiki/, pas dans wiki/ lui-même)
cd /chemin/vers/playlist
cp wiki/*.md playlist.wiki/

# 3. Pousser
cd playlist.wiki
git add .
git commit -m "Mise à jour wiki — Phase 4.6 Resonance + visuels"
git push origin master
```

**Si `playlist.wiki` existe déjà** (pas besoin de re-cloner) :

```bash
cd /chemin/vers/playlist
cp wiki/*.md playlist.wiki/
cd playlist.wiki
git add .
git commit -m "Mise à jour wiki — Phase 4.6 Resonance + visuels"
git push origin master
```

**Important :** récupère d'abord la dernière version du wiki dans le repo principal :

```bash
cd /chemin/vers/playlist
git pull origin main
```

## Structure des pages

| Fichier | Page wiki |
|---------|-----------|
| `Home.md` | Page d'accueil |
| `_Sidebar.md` | Navigation latérale |
| `Vision-et-Objectif.md` | **Vision et objectif** (page centrale) |
| `A-propos.md` | À propos |
| `Guide-de-demarrage.md` | Guide de démarrage |
| `Workflow-complet.md` | Workflow complet |
| `Format-JSON-Playlist.md` | Format JSON |
| `Commandes-et-Options.md` | Référence CLI |
| `Architecture-Technique.md` | Architecture |
| `Playlist-Orlando-Pool-Party.md` | Playlist Orlando |
| `Phase-2-Generation.md` | Phase 2 — génération |
| **`Phase-4-Interface-Resonance.md`** | **Phase 4 — app macOS Resonance** |
| `MusicKit-Experimental.md` | MusicKit |
| `Feuille-de-route-iOS.md` | iOS & cross-platform |
| `Principes-Produit.md` | Principes |
| `Depannage-et-FAQ.md` | Dépannage |

## Dernière mise à jour (juillet 2026)

Reflet des merges :
- Phases 2–3 : gateway providers, intégration Apple Music E2E
- Phase 4.1–4.4 : contrats UI, bridge, thèmes, shell macOS SwiftUI
- Phase 4.5 : builder playlist (formulaire + preview)
- Phase 4.6 : bridge runtime Python, import UX, premiers visuels textuels

## Mise à jour

Quand le code évolue, mets à jour les pages concernées dans `wiki/` puis repousse vers le dépôt wiki.

## Lien depuis le README

```markdown
📖 [Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)
```
