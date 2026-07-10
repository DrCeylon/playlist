# Compatibility Matrix — Resonance v1.0.0

Matrice de compatibilité officielle pour la release v1.0.0.

## Légende

| Symbole | Signification |
|---------|---------------|
| ✅ | Supporté et testé |
| ⚠️ | Partiel / expérimental |
| ❌ | Non supporté |
| 🔧 | Manuel (pas de CI) |

## Systèmes d'exploitation

| OS | CLI génération | CLI check_catalog | CLI create_playlist | App Resonance | CI automatisée |
|----|----------------|-------------------|---------------------|---------------|----------------|
| macOS 14+ | ✅ | ✅ | ✅ | ✅ | ✅ Swift |
| macOS 13 | ⚠️ | ✅ | ✅ | ⚠️ non testé | — |
| Linux | ✅ | ✅ | ❌ | ❌ | ✅ pytest |
| Windows | ⚠️ | ✅ | ❌ | ❌ | ❌ |

## Runtime

| Composant | Version requise | Notes |
|-----------|-----------------|-------|
| Python | **3.12+** | Strict (`requires-python >=3.12`) |
| Xcode / Swift | Dernière stable | macOS app uniquement |
| app Musique | Installée | Import / create_playlist |

## Providers

| Provider | Catalog search | Import playlist | Remote read | Sync plan | Sync apply push | Sync apply pull | Auth |
|----------|----------------|-----------------|-------------|-----------|-----------------|-----------------|------|
| Apple Music | ✅ | ✅ | ✅ | ✅ | ✅ append_only | ⚠️ add only | Music.app local |
| YouTube Music | ⚠️ exp. | ⚠️ exp. | ⚠️ exp. | ⚠️ exp. | ❌ | ❌ | Fichiers locaux |
| Spotify | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — |

## Modes sync (`SyncMode`)

| Mode | Plan (dry-run) | Apply v1.0 | Notes |
|------|----------------|------------|-------|
| `dry_run` | ✅ | N/A | Aucune mutation |
| `append_only` | ✅ | ✅ | **Recommandé v1.0** |
| `mirror` | ✅ | ⚠️ | Non fiable Apple |
| `manual_resolve` | ✅ | ⚠️ | Résolution conflits séparée |

## Directions sync (`SyncDirection`)

| Direction | Plan | Apply v1.0 |
|-----------|------|------------|
| `push_to_provider` | ✅ | ✅ |
| `pull_from_provider` | ✅ | ⚠️ add_track only |
| `bidirectional_preview` | ✅ | ❌ preview only |

## Bridge JSON-RPC

| Commande | Python tests | Swift tests | Stable v1.0 |
|----------|--------------|-------------|-------------|
| `generate` | ✅ | ✅ | ✅ |
| `import_stream` | ✅ | ✅ | ✅ |
| `diagnostics` | ✅ | ✅ | ✅ |
| `plan_sync` | ✅ | ✅ | ✅ |
| `apply_sync` | ✅ | ✅ | ✅ |
| `resolve_sync_conflicts` | ✅ | ⚠️ | ✅ |
| `list_remote_playlists` | ✅ | ✅ | ✅ |

## Dépendances optionnelles

| Extra pip | Package | Requis pour |
|-----------|---------|-------------|
| `dev` | pytest | Tests, contribution |
| `youtube` | ytmusicapi | YouTube Music expérimental |

Runtime production : **stdlib Python uniquement**.

## Stockage local

| Fichier / répertoire | Format | Version schema v1.0 |
|----------------------|--------|---------------------|
| `data/playlists/managed_playlists.json` | JSON | Phase 6.3+ |
| `data/sync_operations.json` (si configuré) | JSON | Phase 6.5+ |
| `data/history/sessions.json` | JSON | Phase 4.8+ |
| `cache/apple_music_identity.json` | JSON | ADR-003 |

## CI / qualité

| Job | Runner | Déclencheur |
|-----|--------|-------------|
| `Python CI` | ubuntu-latest | `playlist_builder/**`, `tests/**` |
| `Resonance macOS` | macos-latest | `apps/resonance/**` |

## Versions produit alignées v1.0.0

| Artefact | Version |
|----------|---------|
| `playlist_builder.__version__` | 1.0.0 |
| `pyproject.toml` | 1.0.0 |
| ResonanceMac `CFBundleShortVersionString` | 1.0.0 |
| Tag Git cible | v1.0.0 |

## Hors compatibilité garantie

- Branches `cursor/**` non taguées
- APIs internes `integration.*` non documentées comme publiques
- Scripts `scripts/perf/` et modes `LEGACY_EXPERIMENTAL`
- Contrats futurs Resonance Identity / Cloud Sync
