# Phase Playlist Manager + YouTube Sync — clôture

**Tag Git :** `phase-playlist-manager-complete`  
**Branche :** `main` (fast-forward depuis `cursor/phase-playlist-manager-youtube-sync`)  
**Date :** juillet 2026

## État produit (macOS Resonance)

Navigation sidebar actuelle :

| Onglet | Route | Rôle |
|--------|-------|------|
| Accueil | `home` | Dashboard — playlists récentes, actions rapides, reprise workflow |
| Nouvelle Playlist | `new_playlist` | Génération + import |
| Playlists | `playlists` | Gestionnaire playlists locales (provider, sync, statut) |
| Synchronisation | `sync` | Plan dry-run + apply push append_only (Phase 6.5) |
| Providers | `providers` | Catalogue providers — Apple principal, YouTube expérimental |
| Historique | `history` | Sessions locales |
| Laboratoire | `diagnostics` | Diagnostics bridge |
| Paramètres | `settings` | Thèmes |

## Livrables techniques

- DTO `ManagedPlaylist*` + protocole `PlaylistLibraryServing`
- Commandes bridge : `list_managed_playlists`, `get_managed_playlist`, `sync_managed_playlist`
- Playlists dérivées des sessions historique (Python)
- YouTube Music : `ProviderCapability.experimental`, non disponible en production
- Fixes import/retry/manual acquisition intégrés (phases 5.5.x)

## Validation

```bash
source .venv/bin/activate
python3.12 -m pytest -q          # 486 passed, 1 skipped

cd apps/resonance
swift build
swift test
./scripts/build.sh
```

CI : `.github/workflows/resonance-macos.yml` sur `main` et `cursor/**`.

## Limites connues

- Sync mirror/reorder Apple Music non garantis — voir [docs/KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md)
- YouTube Music : expérimental (lecture/import)
- Pas d'édition morceaux / duplication / comparateur provider complet (Phase 6.8)
- Dette détaillée : [docs/TECHNICAL_DEBT.md](../docs/TECHNICAL_DEBT.md)

## Prochaine phase suggérée

1. Hydrater `get_managed_playlist` avec les tracks historiques
2. Gateway YouTube expérimental
3. Sync incrémentale UI (`sync` param bridge existant)
