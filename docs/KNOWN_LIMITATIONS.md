# Known Limitations — Resonance v1.0.0

Limitations connues et acceptées pour la release publique v1.0.0.  
Ce document complète le wiki et les ADRs — il ne remplace pas le dépannage détaillé.

## Plateforme

| Limitation | Détail |
|------------|--------|
| App macOS uniquement | Pas d'app iOS/iPadOS en v1.0 |
| CLI `create_playlist` | macOS requis (AppleScript → app Musique) |
| `check_catalog` | Fonctionne hors macOS (catalogue public) |
| macOS minimum app | 14.0 (`LSMinimumSystemVersion`) |

## Providers musicaux

### Apple Music (production)

| Limitation | Détail |
|------------|--------|
| Sync **append_only** fiable | Mode push `append_only` supporté et testé (Phase 6.5) |
| Sync **mirror** | Non garanti — dépend de Music.app / AppleScript |
| **Reorder** distant | Non fiable |
| **Remove** distant | Non garanti hors cas simples |
| MusicKit API | Expérimental — compte Apple Developer requis |
| Acquisition manuelle | Peut nécessiter interaction utilisateur (dialogues Music.app) |

### YouTube Music (expérimental)

| Limitation | Détail |
|------------|--------|
| Statut | `ProviderCapability.EXPERIMENTAL` — **non production** |
| Dépendance | `pip install -e ".[youtube]"` + `ytmusicapi` |
| Écriture | Write port non fiable — lecture/import prioritaire |
| Auth | Cookies / headers utilisateur — fichiers locaux uniquement |
| Support | Peut casser si l'API non officielle change |

### Autres providers

| Provider | Statut v1.0 |
|----------|-------------|
| Spotify | Non implémenté |
| Deezer / Tidal | Non implémenté |

## Synchronisation

| Limitation | Détail |
|------------|--------|
| Pull complet | Pull limité (add_track) — voir messages apply |
| Conflits auto en apply | Modèle et `resolve_sync_conflicts` disponibles ; apply automatique partiel |
| Idempotence | Clé d'idempotence sur apply — rejeu safe pour opérations terminées |
| Wizard UX | Phase 6.8 non livrée — sync via écrans actuels |

## Interface graphique (macOS)

| Limitation | Détail |
|------------|--------|
| Provider génération | `PlaylistBuilderViewModel` envoie encore `appleMusic` par défaut |
| Import incrémental UI | Toggle sync import non exposé partout |
| Thème | `fatalError` si chargement thème échoue (devrait être rare) |

## Performance & architecture

| Limitation | Détail |
|------------|--------|
| Bridge Python | Process one-shot par commande — latence sur imports longs |
| Schema repository | Version plus récente que l'app → erreur explicite (données préservées) |
| Pas de cloud Resonance | Données locales uniquement ; pas de sync multi-Mac |
| Observabilité | Fondations en cours d'intégration (PR #75) — logs stderr restent primaires |

## Sécurité & confidentialité

| Limitation | Détail |
|------------|--------|
| Credentials | Stockage local (Keychain / fichiers) — responsabilité utilisateur |
| Pas d'audit centralisé | Pas de télémétrie serveur Resonance en v1.0 |

## Documentation

| Limitation | Détail |
|------------|--------|
| Wiki vs `docs/` | Wiki en français (utilisateur) ; ADRs souvent en anglais (architecture) |
| Archives Phase 4.x | Certains docs produit sont des archives — voir `wiki/Etat-des-Phases.md` |

## Ce qui n'est **pas** une limitation (v1.0)

- Génération de playlists par seeds / mots-clés
- Import Apple Music avec progression et historique
- Repository local playlists gérées (SSOT)
- Planification sync dry-run
- Apply sync push append_only
- Résolution intelligente de conflits (preview / resolve)
- Diagnostics bridge et rapports import JSON
- Thèmes SwiftUI multiples

## Signaler une limitation manquante

Ouvrir une [issue](https://github.com/DrCeylon/playlist/issues) avec le label `documentation` si une contrainte réelle n'est pas listée ici.
