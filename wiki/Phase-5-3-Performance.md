# Phase 5.3 — Performance

*Proposition structurée — juillet 2026*

## Objectif

Réduire les temps de **génération** et d'**import Apple Music** en s'appuyant sur des **mesures reproductibles**, sans refactor massif ni changement UX validé en 5.2.

**Principe directeur : mesurer d'abord, optimiser ensuite.**

---

## Constat actuel

### Architecture runtime (certain)

```
ResonanceMac (Swift)
  └─ BridgeClient.send() → Process() Python one-shot par commande
       └─ engine_bridge.py (stdin une ligne → réponse → exit)
            └─ build_app_context() à chaque démarrage
                 └─ RuntimeEngineBridgeBackend
```

- Le module `playlist_builder/cli/engine_bridge.py` **supporte** une boucle stdin multi-commandes, mais Swift **ferme stdin après la première commande** (`BridgeClient.runProcess`) → **cold start garanti** à chaque `generate`, `import`, `autocomplete`, etc.
- Logs existants : `resonance-bridge: process started`, `resonance-import: …`, diagnostics `[+N ms]` côté import.

### Import Apple Music (certain)

Pipeline actuel (`import_stream.py`) :

1. `ensure_running(activate=False)` — lancement Music.app
2. **Résolution** — lots de 5 morceaux (`RESOLVE_BATCH_SIZE`), IdentityCache + iTunes Search + AppleScript `collect_candidates_batch`
3. **Livraison** — lots de 25 (`BATCH_SIZE`), AppleScript `add_tracks_by_persistent_id_batch`
4. Pacing intentionnel : `DELIVERY_BATCH_PACE_SECONDS = 0.4`, polling playlist `0.75 s`, retries jusqu'à `12 s`
5. Post-import : `flush_caches()` si configuré

### Génération (certain)

- Moteur Python scoring + discovery ; shortfall possible si catalogue / contraintes insuffisants (`explain_shortfall`, `shortfall_message` dans le DTO).
- Chaque génération = un cold start bridge + import modules + construction `AppContext`.

### Caches existants (certain)

| Cache | Emplacement | Usage |
|-------|-------------|-------|
| **IdentityCache** | `data/` (JsonCache) | `artist:title` → persistent_id Apple Music |
| **Catalog iTunes** | `cache/` (JsonCache) | Recherches iTunes Search API |
| **MusicKit expérimental** | optionnel | Non utilisé en production macOS |

Rate limiting : iTunes `0.5 s` min entre appels ; catalog gateway `2.0 s` par défaut.

### Chemin API Apple (certain)

- **Production macOS** : AppleScript → Music.app + iTunes Search API publique (pas de token développeur requis).
- **MusicKit REST** : code présent mais **hors workflow quotidien** — nécessite compte Apple Developer payant + JWT (voir [MusicKit expérimental](MusicKit-Experimental)).

---

## Hypothèses à valider

### A. Lenteur Apple Music / AppleScript

| Opération | Hypothèse | Statut |
|-----------|-----------|--------|
| Lancement Music.app | 1–3 s au premier `ensure_running` | **À mesurer** |
| `collect_candidates_batch` | 1 subprocess `osascript` par lot de morceaux | **Certain** (code) |
| Résolution unitaire | iTunes API + scoring + éventuelle acquisition | **À mesurer** par morceau |
| `add_tracks_by_persistent_id_batch` | 1 `osascript` par lot de 25 | **Certain** |
| Création playlist | 1 `osascript` `ensure_playlist` | **Certain** |
| Clear playlist avant sync | boucle delete + polling jusqu'à 15 s | **Certain** — coût potentiellement élevé |
| Polling bibliothèque (manuel) | probe toutes les 4 s côté Swift | **Certain** |
| Pacing entre lots | `0.4 s` × nombre de lots | **Certain** — overhead volontaire |

**Risque** : la lenteur dominante est probablement **N × osascript** + pacing + clear playlist, pas la résolution Python pure.

### B. Lenteur bridge Python

| Point | Analyse | Statut |
|-------|---------|--------|
| Process par commande | `Process()` + `build_app_context()` à chaque appel | **Certain** |
| Cold start modules | `import playlist_builder.*` + factory | **À mesurer** (cible : 200 ms – 2 s selon machine) |
| Swift → Python → réponse | JSON-lines sur pipes ; handshake mesuré côté Swift (`[+N ms] Bridge Python handshake terminé`) | **Partiellement instrumenté** |
| Bridge persistant | Entrypoint prêt ; client Swift **non** | **Probable quick win** après validation |

### C. Lenteur catalogue / provider

| Point | Analyse | Statut |
|-------|---------|--------|
| iTunes Search | HTTP + rate limit 0.5 s ; cache JsonCache si hit | **Certain** |
| IdentityCache | Évite re-résolution si hit | **Certain** — efficace en réimport |
| `flush_caches` post-import | Peut invalider gains cache | **Certain** — à évaluer |
| Artwork | URL réseau côté Swift (`InspirationArtworkBackdrop`) | Hors import ; impact génération preview uniquement |

### D. Limitation compte développeur Apple (hors abonnement Apple Music utilisateur)

| Affirmation | Niveau de certitude |
|-------------|---------------------|
| Le workflow production actuel **ne nécessite pas** de compte Apple Developer payant | **Certain** — AppleScript + iTunes Search |
| MusicKit API (`/v1/catalog`, `/v1/me/library`) **nécessite** un Developer Program + tokens JWT | **Certain** — [doc Apple](https://developer.apple.com/documentation/applemusicapi) |
| L'absence de compte développeur **force** le fallback AppleScript pour livraison bibliothèque | **Certain** — choix produit documenté |
| L'iTunes Search API publique a des **rate limits** (HTTP 429) mais pas de compte développeur | **Certain** — retry implémenté |
| Un compte développeur **accélérerait** potentiellement résolution/livraison via API directe | **Probable** — à benchmarker vs AppleScript |
| Les lenteurs actuelles viennent **principalement** de l'absence de compte développeur | **Non prouvé** — AppleScript + pacing + one-shot bridge sont des causes suffisantes sans hypothèse payante |

**À vérifier avant investissement MusicKit** : benchmark A/B même playlist, 20 morceaux, AppleScript vs MusicKit (si tokens disponibles).

---

## Plan de mesure

### Phase 0 — Instrumentation (sans changer le comportement)

1. **Trace unifiée** `resonance-perf:` avec champs : `phase`, `operation`, `duration_ms`, `batch_index`, `track_index`, `cache_hit`.
2. **Span import** déjà partiel → compléter :
   - `bridge_cold_start_ms`
   - `context_build_ms`
   - `music_app_ensure_ms`
   - `resolve_batch_ms` (par lot)
   - `applescript_collect_ms`
   - `delivery_batch_ms` (par lot)
   - `playlist_clear_ms`
   - `playlist_settle_poll_ms`
   - `manual_poll_ms` (côté Swift)
3. **Trace génération** : `generate_total_ms`, `scoring_ms`, `catalog_fetch_ms`, `shortfall_count`.
4. **Export rapport** JSON local (`reports/perf/`) à la fin de chaque import/génération (mode Architecte ou flag env `RESONANCE_PERF_TRACE=1`).

### Jeux de test reproductibles

| Scénario | Morceaux | But |
|----------|----------|-----|
| S1 — Cache froid | 10 | Baseline complète |
| S2 — Cache chaud | 10 (réimport même playlist) | Mesurer IdentityCache |
| S3 — Moyen | 30 | Usage réel |
| S4 — Gros | 80+ | Stress + timeout |
| S5 — Manuel | 1 morceau acquisition manuelle | Isoler polling |

Exécuter **3 fois** chaque scénario sur la même machine macOS ; reporter médiane et p95.

### Métriques à collecter

| Métrique | Seuil d'alerte indicatif |
|----------|--------------------------|
| `bridge_cold_start_ms` | > 1500 ms |
| `resolve_per_track_ms` | > 800 ms |
| `delivery_per_track_ms` | > 500 ms |
| `applescript_calls_count` | > 2 × track_count |
| `import_total_ms` | > 60 s pour 30 morceaux |
| `generate_total_ms` | > 15 s pour 20 morceaux |
| `cache_hit_ratio` | < 30 % en réimport |

---

## Quick wins possibles (après mesure)

| # | Action | Risque | Prérequis mesure |
|---|--------|--------|------------------|
| Q1 | Bridge persistant Swift (réutiliser Process, multi-commandes stdin) | Moyen | Cold start > 10 % du temps total |
| Q2 | Réduire / adapter pacing livraison si Music.app stable | Faible | Profil delivery dominant |
| Q3 | Éviter `clear_playlist` si import incrémental (`sync=False`) | Moyen | UX validée |
| Q4 | Ne pas `flush_caches` systématiquement post-import | Faible | Mesurer hit rate |
| Q5 | Augmenter `RESOLVE_BATCH_SIZE` si AppleScript batch stable | Moyen | Pas de timeout osascript |
| Q6 | Paralléliser iTunes search (hors AppleScript) | Moyen | Rate limit 429 |
| Q7 | Warm-up bridge au lancement app (ping `health`) | Faible | Cold start significatif |

**Ne pas implémenter sans données.**

---

## Optimisations structurantes (phase ultérieure)

1. **Bridge persistant + pool** — session Python unique, `AppContext` réutilisé, health check.
2. **Séparation résolution / livraison** — résolution async catalogue pendant que l'utilisateur prévisualise.
3. **Cache unifié résolution** — TTL + invalidation par playlist/provider ; métriques hit/miss.
4. **Import incrémental par défaut** — skip clear + add only new tracks.
5. **MusicKit optionnel** — feature flag si compte développeur ; benchmark obligatoire avant bascule.
6. **Génération** — expansion catalogue plus agressive / file d'attente scoring (lié au shortfall, pas seulement perf).

---

## Risques

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Réduire pacing → Music.app instable | Import partiel / erreurs | Tests régression macOS, rollback pacing |
| Bridge persistant → état corrompu / fuite mémoire | Crash app | Timeout idle, restart process, tests longue durée |
| Cache stale → mauvais persistent_id | Morceau incorrect | TTL court + invalidation sur erreur delivery |
| MusicKit → complexité tokens | Maintenance | Rester optionnel, pas remplacement aveugle |
| Optimiser avant mesurer | Régression UX | Gate : rapport perf obligatoire avant chaque PR perf |

---

## Ordre d'exécution recommandé

```
1. Instrumentation trace unifiée (Python + Swift)
2. Benchmarks S1–S5 sur Mac référence → rapport baseline
3. Identifier top 2 postes (attendu : bridge cold start + AppleScript delivery)
4. Quick wins validés un par un (1 PR = 1 hypothèse + avant/après)
5. Décision bridge persistant (go/no-go chiffré)
6. Décision MusicKit / compte développeur (go/no-go business + benchmark)
7. Optimisations structurantes par priorité ROI
```

---

## Hors scope Phase 5.3 initiale

- Refactor UX workflow 5.2
- Polish couleurs / textes (phase polish séparée)
- Édition playlist post-import (Phase 5.4+ produit)
- iOS / MusicKit natif

---

## Critères de succès Phase 5.3

| Critère | Cible |
|---------|-------|
| Import 30 morceaux (cache froid) | −40 % temps médian vs baseline |
| Import 30 morceaux (cache chaud) | −60 % vs baseline |
| Génération 20 morceaux | −30 % vs baseline |
| Traçabilité | 100 % des phases avec `duration_ms` |
| Régressions | `swift test` + `pytest` verts, aucun crash import |

---

## Références code

| Composant | Fichier |
|-----------|---------|
| Bridge one-shot Swift | `apps/resonance/ResonanceCore/.../BridgeClient.swift` |
| Bridge loop Python | `playlist_builder/cli/engine_bridge.py` |
| Import stream | `playlist_builder/app/bridge_runtime/import_stream.py` |
| AppleScript | `playlist_builder/core/applescript.py` |
| Delivery pacing | `playlist_builder/integration/apple_music/delivery_pacing.py` |
| Identity cache | `playlist_builder/infrastructure/cache/identity_cache.py` |
| iTunes client | `playlist_builder/integration/apple_music/itunes_client.py` |
