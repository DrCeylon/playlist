# Phase 5.1 — Smart Input Framework

*Phase en cours — voir la documentation complète : [Smart Input Framework](Smart-Input-Framework)*

## Objectif

Réduire la saisie libre dans le formulaire de génération Resonance macOS. L'utilisateur sélectionne des **références canoniques** (artiste, morceau, mots-clés) via autocomplete, suggestions et recherches récentes locales.

**Pas d'IA. Pas de cloud. Pas d'apprentissage.**

## Livrables Phase 5.1

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
| Tests Python + ResonanceCoreTests | ✅ |

## Hors scope 5.1

- Genre comme champ seed dans le formulaire (référentiel prêt, UI à venir)
- Multi-provider UI (architecture prête)
- Apprentissage utilisateur

## Suite

- Phase 5.2 : polish UX (raccourcis ⌘G, onboarding)
- Phase 5.0 : édition playlist post-import
