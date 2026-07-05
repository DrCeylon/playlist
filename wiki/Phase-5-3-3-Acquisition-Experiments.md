# Phase 5.3.3 — Expériences acquisition Apple Music

*Phase expérimentale mesurée — juillet 2026*

## Objectif

Valider **concrètement sur macOS** quelle stratégie d'acquisition catalogue → bibliothèque est viable **avant** toute optimisation ou refactor.

**Hors scope immédiat** :

- Refactor massif
- Migration MusicKit
- Changement UX produit
- Suppression du workflow manuel 5.2

**Principe** : un script explicite, lancé manuellement, qui n'est **pas** intégré au workflow Resonance.

---

## Cause racine confirmée (5.3.2)

L'erreur **-10006** sur :

```applescript
duplicate current track to source "Library"
```

est une **limitation structurelle** de Music.app / AppleScript pour les morceaux catalogue ou abonnement ouverts via URL — reconnue par Apple ([Developer Forums #694200](https://developer.apple.com/forums/thread/694200)).

Ce n'est **ni** un bug Resonance **ni** un problème de performance pur.

---

## Stratégies testées

| ID | Nom | Description |
|----|-----|-------------|
| **S1** | `S1_add_url_direct` | `add (trackUrl)` pour chaque variante d'URL |
| **S2** | `S2_open_location_applescript` | Reproduit le fallback PR9 : open → poll → play → duplicate → search |
| **S3** | `S3_system_events_add_to_library` | Menu Music.app « Add to Library » via System Events |
| **S4** | `S4_manual_fallback` | Workflow manuel Resonance 5.2 : open + prompt utilisateur + sonde biblio |

Chaque stratégie produit :

- succès / échec
- durée totale (`duration_ms`)
- erreur AppleScript éventuelle
- `persistent_id` obtenu ou non
- présence dans `library playlist 1`
- activation Music.app ou non

---

## Limites connues AppleScript

| Limitation | Impact |
|------------|--------|
| URL tracks ≠ library tracks | `persistent ID` souvent inaccessible avant ajout biblio |
| `duplicate to Library` | -10006 fréquent sur abonnement |
| `add URL` | Variable selon type de contenu |
| System Events | Nécessite Autorisation Accessibilité ; libellés menu FR/EN |
| Pas d'API stable documentée | Apple : *"issue identified"* (2021), pas de fix garanti |

---

## Outil expérimental

```bash
# Depuis la racine du dépôt, sur macOS
python3.12 scripts/perf/test_acquisition_strategies.py \
  --url "https://music.apple.com/us/song/EXAMPLE/1234567890" \
  --track-id 1234567890 \
  --artist "Artist Name" \
  --title "Track Title" \
  --strategies S1,S2,S3,S4 \
  --machine "$(sysctl -n hw.model)"
```

Options utiles :

| Option | Description |
|--------|-------------|
| `--strategies S1,S3` | Sous-ensemble de stratégies |
| `--activate-music` | Active la fenêtre Music pour S1/S2 |
| `--no-manual-prompt` | S4 sans attente Entrée (sonde immédiate) |
| `--reports-dir reports/perf` | Répertoire de sortie |

### Prérequis macOS

1. Morceau **absent** de la bibliothèque locale (jamais rencontré)
2. Music.app accessible + abonnement Apple Music actif
3. Autorisation **Automatisation** (Terminal → Music)
4. Pour S3 : **Accessibilité** (System Events → Music)

### Rapports générés

```
reports/perf/acquisition_strategy_YYYYMMDD_HHMMSS.json
reports/perf/acquisition_strategy_YYYYMMDD_HHMMSS.md
```

---

## Critères de décision (post-mesure)

**Décision prise — juillet 2026.** Voir `wiki/Phase-5-3-3-Acquisition-Decision.md` et ADR-012.

### Résultats macOS (Dwayne Johnson — You're Welcome, `6779424544`)

| Stratégie | Résultat | Durée |
|-----------|----------|-------|
| S1 | Échec | 2.7 s |
| S2 | Échec (-10006) | 84.2 s |
| S4 | **Succès** (PID bibliothèque) | 33.3 s |

### Décision retenue

| Stratégie | Rôle production |
|-----------|-----------------|
| **S1** | Probe rapide (~3 s) avant manual |
| **S2** | **Déclassé** — `LEGACY_EXPERIMENTAL` uniquement |
| **S3** | Expérimental — non intégré |
| **S4** | **Fallback principal fiable** (UX 5.2) |
| Cache PID | Chemin rapide inchangé |

Le produit Resonance implémente ADR-012 : plus d'attente ~80 s sur S2 avant la carte manuelle.

---

## Critères historiques (pré-mesure)

Une stratégie est **retenue** pour la Phase 5.3.4 (implémentation) si :

1. **Succès reproductible** sur 3 runs avec le même morceau test (puis 3 morceaux différents)
2. Retourne un **`persistent_id` bibliothèque** utilisable par `add_tracks_by_persistent_id_batch`
3. Durée **inférieure** au chemin S2 actuel (~71 s) ou fiabilité **supérieure** si durée comparable
4. Compatible avec l'UX 5.2 (pas d'activation forcée si évitable)
5. Ne supprime pas S4 manuel comme fallback

| Résultat expérimental | Décision |
|-----------------------|----------|
| S1 fiable et rapide | Remplacer Phase B PR9 par S1 seul |
| S3 fiable | Fallback UI derrière feature flag expérimental |
| Seul S4 fiable | Renforcer workflow manuel ; désactiver auto-acquire par défaut ? (décision produit) |
| Aucune auto fiable | POC MusicKit ou acquisition manuelle systématique |

---

## Recommandation (Phase 5.3.3 — implémentée)

- **Production** : S1 rapide → S4 manuel immédiat si échec ; cache inchangé.
- **S2** : conservé dans `acquisition_experiments.py` et `LEGACY_EXPERIMENTAL` pour benchmarks.
- **MusicKit** : recommandé pour évaluation future quand licence développeur disponible — pas dans cette phase.

**Le produit Resonance est modifié** selon ADR-012 et `wiki/Phase-5-3-3-Acquisition-Decision.md`.

---

## Fichiers

| Fichier | Rôle |
|---------|------|
| `scripts/perf/test_acquisition_strategies.py` | CLI expérimental |
| `playlist_builder/integration/apple_music/acquisition_experiments.py` | Implémentation des stratégies |
| `playlist_builder/reports/acquisition_strategy_report.py` | Export JSON/Markdown |
| `tests/test_acquisition_strategy_experiments.py` | Tests reporting (sans macOS) |

---

## Références

- `wiki/Phase-5-3-2-Acquisition-Investigation.md`
- `docs/architecture/ADR-012-apple-catalog-acquisition-production-policy.md`
- `docs/architecture/ADR-009-apple-catalog-acquisition-workflow.md`
- [Apple Developer Forums — Add songs to Library](https://developer.apple.com/forums/thread/694200)
