# Integration Plan — Resonance (juillet 2026)

Plan d'intégration Chief Integration Engineer. Exécuté sur `cursor/integration-main-ef21`.

## Branches analysées

| Branche | PR | Verdict |
|---------|-----|---------|
| `quality-audit-ef21` | #70 | ✅ Mergée en 1er (P0) |
| `multi-provider-readiness-ef21` | #72 | ✅ Mergée |
| `plugin-platform-foundations-ef21` | #74 | ✅ Mergée avant observability |
| `observability-foundations-ef21` | #75 | ✅ Mergée (conflit manuel) |
| `resonance-vision-2030-ef21` | #73 | ✅ Mergée (docs) |
| `release-v1-readiness-ef21` | #76 | ✅ Mergée (supersède #71) |
| `phase-6-8-product-experience-ef21` | #69 | ✅ Mergée en dernier (UX) |
| `oss-readiness-ef21` | #71 | ❌ **Abandonnée** — doublon #70+#76 |
| `resonance-agent-os-docs-c172` | #48 | ❌ **Abandonner** — obsolète (phase 5.5) |
| `setup-dev-environment-62d3` | #53 | ❌ **Abandonner** — supersédé par `setup_dev.sh` |

## Ordre de merge réel

```
main (486 tests)
  → #70 quality-audit          (499 tests) FF
  → #72 multi-provider         (499 tests) merge
  → #74 plugin-platform        (509 tests) merge
  → #75 observability          (528 tests) merge + fix diagnostics_snapshot
  → #73 vision-2030            (528 tests) merge + fix architecture README
  → #76 release-v1             (530 tests) merge + fix CONTRIBUTING/README/debt
  → #69 phase-6-8 UX           (530 tests) merge + fix Swift UI
```

## Conflits rencontrés

| Étape | Fichiers | Résolution |
|-------|----------|------------|
| #75 observability | `diagnostics_snapshot.py` | Union imports + sections `extension_points` + `observability` |
| #73 vision | `docs/architecture/README.md`, `vision.md` | Union ADR-019 + ADR-020 + liens croisés |
| #76 release | `CONTRIBUTING.md`, `README.md`, `TECHNICAL_DEBT.md` | Fusion contenu quality + release |
| #69 phase-6-8 | `HomeView.swift`, `SettingsView.swift`, `AppShellView.swift` | UX 6.8 + version « Resonance 1.0.0 » |

## Fichiers multi-branches (audit)

43 fichiers touchés par 2+ branches. Points chauds :

- `docs/TECHNICAL_DEBT.md` (4 branches) — consolidé
- `diagnostics_snapshot.py` (observability + plugin) — union additive
- OSS files (LICENSE, CONTRIBUTING, python-ci) — quality + release, #71 ignoré

## PRs à fermer

Après merge sur `main` :

- Fermer #69–#76 comme merged
- Fermer #71 en commentant « superseded by #70+#76 integration »
- Fermer #48, #53 comme obsolete

## Branches à supprimer post-merge

Toutes les `cursor/*-ef21` mergées + `cursor/integration-main-ef21` après FF sur main.
