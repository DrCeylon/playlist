# Phase 5.3.3 — Décision d'architecture acquisition Apple Music

*Décision produit — juillet 2026*

## Résumé exécutif

Après mesures (5.3.2) et expériences macOS (5.3.3), le chemin **S2 open/play/duplicate** est **déclassé** du workflow produit. Le flux par défaut est :

**cache → S1 rapide (~3 s) → acquisition manuelle S4 immédiate si échec**

Plus aucun import Resonance ne doit attendre ~80 s sur `duplicate current track to source "Library"`.

---

## Résultats expérimentaux (macOS réel)

**Morceau** : Dwayne Johnson — *You're Welcome*  
**URL** : https://music.apple.com/us/song/youre-welcome/6779424544  
**Track ID** : `6779424544`

| Stratégie | Résultat | Durée | PID | Biblio |
|-----------|----------|-------|-----|--------|
| S1 — add URL direct | Échec | 2 740 ms | — | non |
| S2 — open/play/duplicate | Échec (-10006) | 84 208 ms | — | non |
| S4 — fallback manuel | **Succès** | 33 293 ms | `5A9F4F4AF88E2299` | oui |

---

## Décision

| # | Décision |
|---|----------|
| 1 | S2 n'est plus un chemin principal |
| 2 | S2 reste disponible en `LEGACY_EXPERIMENTAL` (CLI expérimental, désactivé par défaut) |
| 3 | S4 manuel devient le fallback fiable principal sans persistent ID |
| 4 | Pas d'attente 6×5 s avant la carte manuelle |
| 5 | Cache identity inchangé — import rapide si PID connu |
| 6 | UX Phase 5.2 conservée (`ManualAcquisitionGate`) |
| 7 | MusicKit / YouTube Music : hors scope immédiat |

---

## Comportement avant / après

### Avant (PR9 / ADR-009)

```
Bibliothèque vide → catalogue trouvé
  → acquire_song_from_url (S1 + S2 monolithique, ~71–84 s)
  → 6 sondes biblio × 5 s
  → puis carte manuelle si toujours absent
```

**Problème** : ~80 s perdus sur S2 avant toute action utilisateur.

### Après (ADR-012)

```
Cache PID connu → résolution immédiate (inchangé)

Bibliothèque vide → catalogue trouvé
  → try_add_catalog_url (S1, ~3 s)
  → si succès : 2 sondes biblio max
  → si échec : open_catalog_url_for_manual + carte manuelle immédiate
  → après confirmation : 4 sondes biblio (Phase 5.2)
```

**Gain** : la lenteur restante est explicite (action utilisateur ~33 s mesurés en S4), pas une attente silencieuse.

---

## Fichiers modifiés

| Fichier | Changement |
|---------|------------|
| `acquisition_policy.py` | Politique production vs legacy |
| `library_acquisition.py` | `_acquire_production` / `_acquire_legacy_experimental` |
| `applescript_client.py` | `try_add_catalog_url`, `open_catalog_url_for_manual` |
| `resolver.py` | Manual immédiat ; 2 sondes post-S1 |
| `tests/test_acquisition_production_policy.py` | Nouveaux tests politique |
| `tests/test_apple_music_manual_acquisition.py` | Mocks S1 au lieu de S2 |
| `docs/architecture/ADR-012-*.md` | Décision officielle |

Code S2 **conservé** : `acquire_song_from_url`, `acquisition_experiments.py`, `test_acquisition_strategy_experiments.py`.

---

## Limites restantes

- S1 (`add URL`) échoue souvent sur morceaux abonnement — comportement Apple, pas Resonance.
- S2 (-10006) reste une limitation structurelle AppleScript ([forums #694200](https://developer.apple.com/forums/thread/694200)).
- L'acquisition manuelle dépend de l'utilisateur et de Music.app (~30 s typiques).
- Pas d'API stable documentée pour l'ajout catalogue → bibliothèque sans MusicKit.

---

## Recommandation MusicKit / multi-provider

| Option | Quand | Notes |
|--------|-------|-------|
| **Conserver S4 manuel** | Court terme (actuel) | Fiable, UX 5.2 validée |
| **POC MusicKit** | Licence développeur Apple disponible | `MusicLibrary.add` — candidat pour remplacer S1/S2 |
| **YouTube Music** | Phase provider séparée | ADR dédié ; pas de réutilisation AppleScript |
| **S3 System Events** | Expérimental seulement | Accessibilité + libellés menu localisés |

Ne pas lancer MusicKit ni YouTube dans cette phase.

---

## Validation

```bash
cd apps/resonance && swift build && swift test && ./scripts/build.sh
cd ../..
source .venv/bin/activate
python3.12 -m pytest -q
```

---

## Références

- [ADR-012](../docs/architecture/ADR-012-apple-catalog-acquisition-production-policy.md)
- [ADR-009](../docs/architecture/ADR-009-apple-catalog-acquisition-workflow.md) (étapes auto S2 supplantées en production)
- `wiki/Phase-5-3-2-Acquisition-Investigation.md`
- `wiki/Phase-5-3-3-Acquisition-Experiments.md`
