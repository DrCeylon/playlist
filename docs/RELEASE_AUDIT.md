# Release Audit — Resonance v1.0 (juillet 2026)

Audit réalisé en mode **Release Manager** sur `main` avant préparation v1.0.0.  
Objectif : identifier tout ce qui empêcherait une publication publique de qualité.

## Verdict exécutif

| Domaine | État | Bloquant v1.0 ? |
|---------|------|-----------------|
| Fonctionnalités cœur (CLI + macOS) | ✅ Matures (Phases 1–6.7) | Non |
| Tests locaux | ✅ 486 pytest + ~135 Swift | Non |
| CI Python automatisée | ❌ Absente sur `main` | **Oui** |
| Licence OSS | ❌ Absente | **Oui** |
| Politique sécurité | ❌ Absente | **Oui** |
| Cohérence versioning | ❌ Triple divergence | **Oui** |
| Documentation contributeur | ⚠️ Partielle | Moyen |
| Exactitude docs (compteurs tests) | ⚠️ Drift README/wiki | Moyen |
| Branding « preview » UI | ⚠️ Sous-estime la maturité | Faible |

**Conclusion :** le code est prêt pour une **v1.0 fonctionnelle** ; le dépôt n'inspire pas encore pleinement confiance en l'état OSS (licence, CI, versioning, SECURITY).

---

## 1. Architecture

### Points forts

- Séparation claire : `canonical/` → `app/` → `integration/<provider>/`.
- Sync provider-neutral : `plan_sync` pur, `apply_sync` séparé, journal `PlaylistSyncOperation`.
- Repository local = SSOT ; snapshots distants immuables (ADR-017).
- Bridge JSON-RPC avec DTO partagés Python/Swift (`ResonanceCore`).
- Observabilité fondations en PR #75 (non mergée au moment de l'audit).

### Risques / dette

| Sujet | Fichier(s) | Sévérité |
|-------|------------|----------|
| Stub sync legacy encore exposé | `playlist_library.py` → `sync_managed_playlist_stub` | Moyenne |
| Bridge one-shot par commande (latence import) | `bridge_runtime/` | Moyenne |
| Provider picker UI non branché | `PlaylistBuilderViewModel.swift` | Moyenne |
| Warnings Sendable Swift 6 | CI macOS | Basse |

---

## 2. Dette technique

Référence : `docs/TECHNICAL_DEBT.md` (lignes dupliquées corrigées dans cette PR).

| Priorité | Sujet |
|----------|-------|
| Moyenne | YouTube Music write non fiable (ADR-018) |
| Moyenne | Sync mirror/reorder Apple Music non garantis |
| Moyenne | `PlaylistBuilderViewModel` hardcode `appleMusic` |
| Basse | Import `sync: true` toujours côté Swift |
| Future | Resonance Identity / Cloud Sync (docs only) |

Aucun marqueur `TODO`/`FIXME` actif dans le code applicatif.

---

## 3. UX

| État | Détail |
|------|--------|
| ✅ | Génération, import Apple Music, historique, diagnostics |
| ✅ | Playlist Manager : Playlists, Sync, Providers |
| ⚠️ | Libellés « preview » dans `SettingsView`, `HomeView` |
| ⚠️ | Sélection provider génération non effective (Apple forcé) |
| ❌ | Wizard sync 6.8 non livré |
| ❌ | iOS non démarré (hors scope v1.0 macOS) |

---

## 4. Performances

- Import long : bridge Python relancé par commande (pas de process persistant).
- `perf_span` opt-in (`RESONANCE_PERF_TRACE`) — complété par couche observabilité (PR #75).
- IdentityCache et catalog cache documentés.
- Scripts `scripts/perf/` pour benchmarks internes — non user-facing.

---

## 5. Sécurité

| Aspect | État |
|--------|------|
| Credentials provider | Local Keychain / fichiers utilisateur (YouTube exp.) |
| `.gitignore` | Exclut `oauth*.json`, `headers*.json`, `data/`, `cache/` |
| Fichiers sensibles commités | ✅ Aucun (`git ls-files` reports/cache/data vide) |
| `SECURITY.md` | ❌ Manquant (ajouté dans cette PR) |
| Bridge sanitization | `assert_bridge_safe_mapping` en place |

---

## 6. Documentation

| Document | État |
|----------|------|
| README racine | ✅ Utile mais compteur tests obsolète (444 → 486) |
| Wiki français | ✅ Riche ; drift sur compteurs et statut sync |
| ADRs | ✅ 18 ADRs architecture |
| CONTRIBUTING / GOVERNANCE | ❌ Absents sur `main` |
| Guide limitations v1.0 | ❌ Absent → `KNOWN_LIMITATIONS.md` |
| Plan release | ❌ Absent → `RELEASE_PLAN.md` |

PR ouvertes docs : #48 (AGENTS), #53 (Cursor Cloud) — contenu intégré partiellement ici.

---

## 7. Packaging & installation

| Élément | État |
|---------|------|
| `pyproject.toml` | ✅ Entry points CLI, extras `dev`/`youtube` |
| Version PyPI | ⚠️ `0.8.2` vs `__version__` `1.1.0` vs app `1.0.0` |
| Dépendances runtime | ✅ Stdlib seule (volontaire) |
| `pip install -e ".[dev]"` | ✅ Documenté |
| App `.app` macOS | `package-mac-app.sh` documenté wiki |

---

## 8. Mises à jour

- Pas de mécanisme auto-update (normal pour OSS local-first).
- `git pull` documenté dans README.
- Pas de tag GitHub publié à ce jour.
- `MIGRATION_GUIDE.md` créé pour passage vers v1.0.0.

---

## 9. Scripts

| Script | Référencé | OK |
|--------|-----------|-----|
| `scripts/setup_dev.sh` | README | ✅ |
| `scripts/check_all.sh` | README | ✅ |
| `scripts/check_environment.py` | CI | ✅ |
| `apps/resonance/scripts/build.sh` | CI macOS | ✅ |
| `Makefile` | Basique ; pas de cible `check-all` | ⚠️ |

---

## 10. CI/CD

| Workflow | État |
|----------|------|
| `resonance-macos.yml` | ✅ Swift build+test ; **filtre paths** → Python non testé en CI |
| `python-ci.yml` | ❌ Absent → ajouté |
| Issue/PR templates | ❌ Absents → ajoutés |
| Dependabot | ❌ Absent (acceptable v1.0) |

---

## 11. Licences & dépendances

| Élément | État |
|---------|------|
| `LICENSE` | ❌ Absent → MIT ajouté |
| Python runtime | Stdlib uniquement |
| Python dev | pytest |
| Swift SPM | Pas de dépendances externes |
| YouTube | `ytmusicapi` optionnel (`[youtube]`) |

---

## 12. Versioning

| Source | Version audit |
|--------|---------------|
| `pyproject.toml` | 0.8.2 |
| `playlist_builder/__init__.py` | 1.1.0 |
| `Info.plist` CFBundleShortVersionString | 1.0.0 |
| Swift tests `engine_version` | 1.0.0 (hardcodé) |

**Action :** aligner sur **1.0.0** (source unique `__version__`).

---

## 13. Qualité des tests

| Métrique | Valeur |
|----------|--------|
| Tests Python | 488 passed, 1 skipped |
| Tests Swift (macOS) | ~135 |
| Couverture sync apply | ✅ `test_playlist_sync_apply.py` |
| Couverture bridge | ✅ `test_ui_bridge_json_rpc.py` |
| Couverture YouTube exp. | ✅ avec mocks |
| E2E Apple Music réel | Manuel (macOS + Music.app) |

Scénarios critiques couverts : génération, import, sync plan/apply, conflits, bridge contract, DTO parity.

---

## 14. Fonctionnalités incomplètes / expérimentales

### Incomplètes (documentées, non bloquantes v1.0 macOS)

- Sync mirror / reorder / remove provider (hors append_only)
- Résolution conflits sync automatique en apply (modèle prêt, moteur partiel)
- Wizard sync UX (Phase 6.8)
- Provider picker UI effectif
- iOS shell

### Expérimentales (explicitement marquées)

- YouTube Music (`ProviderCapability.EXPERIMENTAL`)
- MusicKit CLI (`--engine musickit`)
- Acquisition `LEGACY_EXPERIMENTAL` (benchmarks only)
- Resonance Identity / Cloud Sync (vision docs)

---

## 15. Améliorations indispensables avant v1.0

| # | Action | Statut PR release |
|---|--------|-------------------|
| 1 | Ajouter `LICENSE` (MIT) | ✅ |
| 2 | Ajouter `SECURITY.md` | ✅ |
| 3 | CI Python (`python-ci.yml`) | ✅ |
| 4 | Aligner version 1.0.0 | ✅ |
| 5 | `CONTRIBUTING.md`, `AGENTS.md`, `CHANGELOG.md` | ✅ |
| 6 | Docs release (plan, checklist, limitations, migration, matrix) | ✅ |
| 7 | Corriger drift README/wiki tests | ✅ |
| 8 | Templates GitHub issue/PR | ✅ |
| 9 | Tag `v1.0.0` sur GitHub | ⏳ Mainteneur |
| 10 | Merger PRs fonctionnelles (#75 observability, etc.) | ⏳ Post-audit |

---

## 16. Audit Git

```bash
git ls-files reports/ cache/ data/ .pytest_cache/   # → vide ✅
```

Branches `cursor/**` nombreuses — nettoyage post-merge recommandé (voir `wiki/Maintenance-et-Workflow.md`).

Aucun secret committé détecté dans l'index.
