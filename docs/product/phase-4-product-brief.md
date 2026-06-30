# Phase 4.0 — Product brief

## Executive summary

**Resonance** (nom provisoire) est une plateforme intelligente de création,
résolution, acquisition et import de playlists musicales. Ce n’est pas un
générateur JSON ni un wrapper AppleScript : c’est un **laboratoire de curation**
qui orchestre un moteur canonique multi-fournisseurs derrière une expérience
premium.

Phase 4.0 pose les fondations produit, UX, architecture UI et choix technologique
**sans implémenter l’interface**.

## Problem statement

Les utilisateurs avancés veulent :

1. **Composer** des playlists avec intention (énergie, ambiance, exclusions).
2. **Voir** pourquoi un morceau a été choisi ou rejeté.
3. **Importer** vers leur bibliothèque sans friction, y compris quand l’acquisition
   catalogue est nécessaire.
4. **Faire confiance** au système (diagnostics, cache, reprise).

La CLI actuelle prouve le moteur. Il manque une **surface produit** à la hauteur
de la sophistication technique.

## Product vision

> *De l’intention à la playlist, en une expérience fluide, observable et sûre.*

### Pillars

| Pilier | Description |
|--------|-------------|
| **Intelligent** | Scoring, contraintes, courbes d’énergie, suggestions |
| **Observable** | Pipeline visible : génération → résolution → acquisition → delivery |
| **Safe** | Jamais destructif : pas de suppression playlist/bibliothèque |
| **Portable** | Même logique métier macOS, iPadOS, iOS |
| **Premium** | Finition Things / Fantastical, pas utilitaire technique |

## Target users

### Primary — Curateur exigeant (Nicolas persona)

- macOS + Apple Music aujourd’hui
- Comprend JSON/CLI mais ne veut plus vivre dans le terminal
- Veut contrôle fin (exclusions, énergie) et feedback riche

### Secondary — Créateur événementiel

- Playlists longues, sections, montée progressive
- Besoin de preview avant import

### Future — Utilisateur mobile

- iPhone / iPad, MusicKit, import depuis la poche
- Moins de diagnostics, plus de fluidité

## Provisional product identity

| Élément | Proposition |
|---------|-------------|
| **Nom** | **Resonance** (codename produit ; repo reste `playlist`) |
| **Tagline** | *Compose. Resolve. Deliver.* / *Composez. Résolvez. Livrez.* |
| **Ton** | Savant fou **premium** — précis, chaleureux, jamais condescendant |
| **Vocabulaire** | *session*, *résolution*, *acquisition*, *livraison*, *laboratoire*, *confiance* |
| **À éviter** | « Erreur 42 », jargon AppleScript, « sync failed » brut |

### Exemples de copy

- Succès : `⚗ Analyse terminée — 97 % de confiance, 3 hits cache, 2 acquisitions catalogue.`
- Progression : `🔍 Résolution : Kygo — Firestone…`
- Attente manuelle : `⏸ Music.app attend votre confirmation — ajoutez le morceau, puis continuez.`
- Échec partiel : `12 morceaux livrés, 2 en attente d’acquisition. Rien n’a été supprimé.`

## Scope Phase 4.0 (this PR)

- Documentation produit et architecture
- ADR-011, framework decision, wireframes
- Design system + theme engine **spec**
- Roadmap PR 4.1–4.9
- **No** UI implementation, **no** new UI dependencies

## Out of scope (Phase 4.0)

- SwiftUI code
- PySide6 / Electron prototype
- App Store submission
- Spotify / Deezer implementation
- Refonte CLI

## Success metrics (future implementation)

| Metric | Target |
|--------|--------|
| Time to first playlist (new user) | < 5 min guided |
| Import success rate (library + acquisition) | ≥ CLI parity |
| UI blocking during import | 0 s (background engine) |
| ViewModel unit test coverage | ≥ 90 % shared logic |
| Accessibility | WCAG AA contrast, full keyboard nav macOS |

## Non-negotiables (inherited from engine)

1. Canonical model stays provider-neutral.
2. No `persistent_id`, AppleScript, or MusicKit in `ui/shared`.
3. No playlist or library deletion.
4. IdentityCache after every successful resolution.
5. All provider access via integration gateway.

## Related documents

- [phase-4-ux-flows.md](phase-4-ux-flows.md)
- [phase-4-wireframes.md](phase-4-wireframes.md)
- [phase-4-framework-decision.md](phase-4-framework-decision.md)
- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
