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

## Dernière mise à jour (juillet 2026 — maintenance post Phase 5.1)

- Smart Input Framework mergé (PR #33)
- [État des phases](Etat-des-Phases) — tableau PR / branches actives
- [Maintenance & workflow Git](Maintenance-et-Workflow)
- PR actives : #34 icône, #35 autocomplete artiste, #36 import UX
- ~318 tests Python ; `swift test` sur macOS (CI)

## Structure des pages

| Fichier | Page wiki |
|---------|-----------|
| `Home.md` | Page d'accueil |
| `_Sidebar.md` | Navigation latérale |
| `Etat-des-Phases.md` | **Avancement phases & PR** |
| `Maintenance-et-Workflow.md` | **Workflow Git & nettoyage** |
| `Architecture-Technique.md` | Architecture |
| `Phase-5-1-Smart-Input.md` | Clôture Phase 5.1 |
| `Smart-Input-Framework.md` | Architecture Smart Input |
| `Phase-5-Vision.md` | Roadmap Phase 5+ |
| `Depannage-et-FAQ.md` | Dépannage |

## Ancienne section structure

| Fichier | Page wiki |
|---------|-----------|
| `Vision-et-Objectif.md` | Vision et objectif |
| `Phase-4-Interface-Resonance.md` | Phase 4 — app macOS |
| `Phase-4-8A-Cloture.md` | Clôture Phase 4.8A |

## Lien depuis le README

```markdown
📖 [Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)
```
