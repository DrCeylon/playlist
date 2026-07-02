# Publication du wiki GitHub

Ce dossier contient la documentation wiki complète en français.

## Publier sur le wiki GitHub

Le wiki GitHub est un dépôt Git séparé. Pour publier :

```bash
cd /chemin/vers/playlist
git pull origin main
cp wiki/*.md playlist.wiki/
cd playlist.wiki
git add .
git commit -m "Mise à jour wiki — Phase 4.8A clôture Resonance"
git push origin master
```

## Structure des pages

| Fichier | Page wiki |
|---------|-----------|
| `Home.md` | Page d'accueil |
| `_Sidebar.md` | Navigation latérale |
| `Vision-et-Objectif.md` | Vision et objectif |
| `Architecture-Technique.md` | Architecture |
| `Phase-4-Interface-Resonance.md` | Phase 4 — app macOS |
| **`Phase-4-8A-Cloture.md`** | **Clôture Phase 4.8A** |
| **`Phase-5-Vision.md`** | **Proposition Phase 5** |
| `Depannage-et-FAQ.md` | Dépannage |
| `Guide-de-demarrage.md` | Guide de démarrage |

## Dernière mise à jour (juillet 2026 — Phase 4.8A)

- Stabilisation Resonance macOS : clavier, import, delivery pacing, icône
- Historique actionnable, acquisition manuelle copier-coller
- 307 tests Python, guards Swift
- Proposition Phase 5 (vision produit)

## Lien depuis le README

```markdown
📖 [Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)
```
