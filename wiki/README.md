# Publication du wiki GitHub

Ce dossier contient la documentation wiki complète en français.

## Publier sur le wiki GitHub

Le wiki GitHub est un dépôt Git séparé. Pour publier :

```bash
# 1. Cloner le wiki (remplace par ton URL)
git clone https://github.com/DrCeylon/playlist.wiki.git

# 2. Copier les fichiers
cp /chemin/vers/playlist/wiki/*.md playlist.wiki/

# 3. Pousser
cd playlist.wiki
git add .
git commit -m "Documentation wiki complète en français"
git push origin master
```

## Structure des pages

| Fichier | Page wiki |
|---------|-----------|
| `Home.md` | Page d'accueil |
| `_Sidebar.md` | Navigation latérale |
| `A-propos.md` | À propos |
| `Guide-de-demarrage.md` | Guide de démarrage |
| `Workflow-complet.md` | Workflow complet |
| `Format-JSON-Playlist.md` | Format JSON |
| `Commandes-et-Options.md` | Référence CLI |
| `Architecture-Technique.md` | Architecture |
| `Playlist-Orlando-Pool-Party.md` | Playlist Orlando |
| `Phase-2-Generation.md` | Phase 2 |
| `MusicKit-Experimental.md` | MusicKit |
| `Feuille-de-route-iOS.md` | iOS |
| `Principes-Produit.md` | Principes |
| `Depannage-et-FAQ.md` | Dépannage |

## Mise à jour

Quand le code évolue, mets à jour les pages concernées dans `wiki/` puis repousse vers le dépôt wiki.

## Lien depuis le README

Ajoute dans le README principal :

```markdown
📖 [Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)
```
