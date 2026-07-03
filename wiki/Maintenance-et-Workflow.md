# Maintenance et workflow Git

Guide pour garder le dépôt propre et compréhensible.

## Branches

### Règles

| Règle | Détail |
|-------|--------|
| Branche par défaut | `main` |
| Branches feature | `cursor/<description>-ef21` (minuscules) |
| Durée de vie | Supprimer la branche distante **après merge** de la PR |
| Une PR = une branche | Ne pas empiler plusieurs sujets non liés |

### Nettoyage après merge

```bash
git checkout main && git pull origin main
git branch -d cursor/ma-branche-ef21
git push origin --delete cursor/ma-branche-ef21
git fetch --prune
```

### Vérifier si une branche est mergée

```bash
git fetch origin
git log origin/main..origin/cursor/ma-branche-ef21 --oneline   # commits non mergés
git merge-base --is-ancestor origin/cursor/ma-branche-ef21 origin/main && echo merged
```

Ne **jamais** supprimer une branche dont la PR est encore ouverte ou contient du travail non mergé.

## Pull Requests

| État | Action |
|------|--------|
| **MERGED** | Fermer automatiquement ; supprimer la branche |
| **OPEN** + brouillon actif | Conserver |
| **OPEN** + obsolète / doublon | Fermer avec commentaire explicatif |
| **CLOSED** sans merge | Archivée ; branche supprimée si inutile |

Les PR Cursor en brouillon (#34–#36) sont les seules ouvertes au juillet 2026.

## Tags et stash

- **Tags** : aucun tag de release pour l'instant ; pas de tags temporaires à maintenir
- **Stash** : signaler tout `git stash` non vidé avant maintenance (aucun attendu en routine)

## Wiki

- Source de vérité produit : dossier `wiki/` du repo (publié vers `playlist.wiki` GitHub)
- Mise à jour directe sur `main` acceptée pour la doc
- Après chaque phase : mettre à jour [État des phases](Etat-des-Phases) et la sidebar

## CI GitHub

Workflow unique : `.github/workflows/resonance-macos.yml`

- Déclenché sur `main` et `cursor/**` quand `apps/resonance/**` change
- `macos-latest` : `./apps/resonance/scripts/build.sh`

## Conventions de commit

- Messages en anglais ou français, impératif ou descriptif clair
- Une intention par commit
- Squash merge préféré pour les PR feature (historique lisible sur `main`)

## Structure du dépôt

```
playlist_builder/     # Moteur Python
apps/resonance/       # App macOS (SwiftPM)
wiki/                 # Documentation utilisateur FR
docs/                 # ADR et specs produit (référence technique)
tests/                # Pytest
scripts/              # Utilitaires (icône, package .app)
```

## Checklist maintenance périodique

1. `git fetch --all --prune` — branches distantes à jour
2. Supprimer branches mergées
3. Vérifier PR ouvertes ([État des phases](Etat-des-Phases))
4. `python3 -m pytest -q` vert
5. Sur Mac : `./apps/resonance/scripts/build.sh` vert
6. Wiki aligné avec `main`

---

*Dernière maintenance : juillet 2026 — Phase 5.1 clôturée.*
