# Publication du wiki GitHub

Ce dossier contient la **documentation utilisateur en français**. La documentation contributeur est dans le dépôt principal (`docs/`, `CONTRIBUTING.md`).

## Publier sur le wiki GitHub

Le wiki GitHub est un dépôt Git séparé :

```bash
git clone https://github.com/DrCeylon/playlist.git
cd playlist && git pull origin main
cp wiki/*.md /chemin/vers/playlist.wiki/
cd /chemin/vers/playlist.wiki
git add .
git commit -m "Mise à jour wiki Resonance"
git push origin master
```

## Dernière mise à jour (juillet 2026 — préparation Open Source)

- Phases fonctionnelles 1–6.8 terminées sur `main`
- **490+** tests Python
- Documentation contributeur : `docs/README.md`, `CONTRIBUTING.md`, `AGENTS.md`
- [État des phases](Etat-des-Phases) · [Maintenance Git](Maintenance-et-Workflow)

## Structure

| Fichier | Audience |
|---------|----------|
| `Home.md` | Accueil utilisateur |
| `Guide-de-demarrage.md` | Premiers pas |
| `Etat-des-Phases.md` | Avancement technique |
| `Vision-et-Objectif.md` | Pourquoi Resonance existe |
| `Depannage-et-FAQ.md` | Support utilisateur |

## Lien depuis le README

```markdown
📖 [Documentation utilisateur (Wiki)](https://github.com/DrCeylon/playlist/wiki)
🛠 [Contributing](https://github.com/DrCeylon/playlist/blob/main/CONTRIBUTING.md)
```
