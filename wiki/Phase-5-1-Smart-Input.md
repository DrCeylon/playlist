# Phase 5.1 — Smart Input Framework

*Phase clôturée — merge `main` @ `99e269d` (PR #33, squash)*

## Objectif

Réduire la saisie libre dans le formulaire de génération Resonance macOS. L'utilisateur sélectionne des **références canoniques** (artiste, morceau, mots-clés) via autocomplete, suggestions et recherches récentes locales.

**Pas d'IA. Pas de cloud. Pas d'apprentissage.**

## Livrables (validés macOS)

| Composant | Statut |
|-----------|--------|
| `ArtistRef`, `TrackRef`, `GenreRef`, `KeywordRef` | ✅ ResonanceCore |
| `AutocompleteEngine`, cache, debounce, annulation | ✅ ResonanceCore |
| Bridge `autocomplete_search` | ✅ Python + Swift |
| Recherche iTunes multi-résultats (artist/track) | ✅ Apple Music gateway |
| Référentiel genres + synonymes (local) | ✅ |
| Tags mots-clés + suggestions (local) | ✅ |
| `SmartAutocompleteField` macOS | ✅ |
| Recherches récentes (UserDefaults) | ✅ |
| `ResonanceCoreTests` (engine, cache, bridge) | ✅ |
| Tests Python autocomplete + iTunes mock | ✅ |

## Choix finaux retenus

| Sujet | Décision |
|-------|----------|
| Encapsulation moteur | `session` en `private(set)` — tests via `updateQuery` / API publique |
| Cache entités | `String(describing: entity.id)` — pas de contrainte `ID == String` |
| Recherches récentes mémoire | `InMemoryRecentSearchProvider` en `final class` + `NSLock` |
| Tests bridge streaming | `dispatchStreamingLine` **internal** ; tests dans `ResonanceCoreTests` |
| Captures `@Sendable` tests | `LockedBox` thread-safe (`SendableTestCapture.swift`) |
| Package.swift | `exclude` avant `sources` ; exclusion `Tests`, `Info.plist`, `AppIcon.iconset` |
| Mapping génération | Refs → `SeedReference` / `[String]` au `buildRequest()` — contrat moteur inchangé |

## Hors scope 5.1 (reporté)

- Genre comme champ seed dans le formulaire (référentiel prêt)
- Multi-provider UI (architecture prête)
- Apprentissage utilisateur

## Documentation

→ [Smart Input Framework](Smart-Input-Framework) — architecture complète

## Suite

- **Phase 5.2** : polish UX (raccourcis ⌘G, onboarding)
- **Phase 5.0** : édition playlist post-import

## Validation

```bash
python3 -m pytest -q          # 318 passed
cd apps/resonance
./scripts/build.sh            # swift build + swift test
swift test
swift build
```

Validé sur macOS avant merge PR #33.
