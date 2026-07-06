# PR Review Checklist

À parcourir avant de valider une PR Resonance. Toute case non cochée doit être
justifiée dans le rapport de revue.

## Périmètre

- [ ] **Scope respecté** : la PR fait ce qui était demandé, rien de plus (pas de
      dérive de périmètre, pas de nouvelle phase entamée sans demande).

## Architecture

- [ ] **Pas de provider-specific dans le Core** : aucun import
      `integration.<provider>` ni identifiant provider (`persistent_id`, URI Spotify,
      MusicKit ID) hors `integration/` et `IdentityCache`.
- [ ] **Pas d'AppleScript dans `bridge_runtime`** : le bridge reste provider-neutral
      (aucun AppleScript, aucun import Apple direct).
- [ ] Dépendances toujours orientées vers l'intérieur (canonical → ports →
      application → gateway → provider).

## Tests

- [ ] **Tests Python** lancés et verts (`python3.12 -m pytest -q`) ; tests ajoutés/à
      jour pour tout nouveau comportement.
- [ ] **Tests Swift** lancés et verts si le toolchain est disponible
      (`apps/resonance/scripts/build.sh`) ; sinon absence justifiée (Linux/pas de Swift).

## Documentation

- [ ] **Docs / ADR mises à jour** si des frontières ou des contrats changent
      (nouvel ADR pour un provider ; `CURRENT_PHASE.md` / `NEXT_BACKLOG.md` à jour).

## Qualité & risques

- [ ] **Dette technique** : stable ou en baisse ; toute dette introduite est
      explicitement signalée.
- [ ] **UX inchangée** si aucun changement UX n'a été demandé.
- [ ] **Migration** : indiquer si une migration (données / cache / schéma) est
      nécessaire, ou confirmer que non.

## Livraison

- [ ] **Rapport final clair** : fichiers touchés, résumé, validation (état réel des
      tests, sans masquer d'échec), état git, prochaine action recommandée.
