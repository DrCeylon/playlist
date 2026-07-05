# Phase 5.3.2 — Investigation acquisition catalogue (`acquire_song_from_url`)

*Analyse technique basée sur les mesures baseline — juillet 2026*

## Constat mesuré (certain)

| Métrique | Valeur | Part |
|----------|--------|------|
| `import.import_total` | 392 354 ms | 100 % |
| `import.resolve_total` | 391 574 ms | 99,8 % |
| `import.delivery_total` | 719 ms | 0,2 % |
| `applescript.acquire_song_from_url` × 5 | ~71 070–71 191 ms chacun | ~355 634 ms (~90,7 % import) |

**Conclusion immédiate** : le goulot est la **résolution avec acquisition catalogue**, pas la livraison playlist ni le bridge Python.

---

## Cause racine identifiée

### Cause principale (certaine — code + cohérence des mesures)

`acquire_song_from_url` exécute **un script AppleScript monolithique** (`_build_acquire_song_script`) qui enchaîne :

1. **Phase A** — pour chaque variante d'URL (jusqu'à **4–5 URLs** : `itms://`, `https://`, `music://`, URL primaire) :
   - `add (trackUrl)` — ajout direct catalogue → bibliothèque
   - Si succès → retour immédiat avec `persistent ID`

2. **Phase B** (fallback abonnement) — pour **chaque URL** jusqu'à succès ou épuisement :
   - `open location` — ouvre la fiche morceau dans Music.app
   - **Polling `current track`** : 16 × `delay 0.5` → **jusqu'à 8 s**
   - `delay play_delay` → **5 s** (défaut `play_delay_seconds=5.0`)
   - `play`
   - `delay 1` → **1 s** (hardcodé)
   - `duplicate current track to source "Library"`
   - `delay settle_delay` → **6 s** (défaut `settle_delay_seconds=6.0`)
   - Recherche bibliothèque (`search library playlist 1`)
   - Si échec recherche → **URL suivante** (recommence Phase B)

**Budget de délais scriptés par itération Phase B** :

```
8 + 5 + 1 + 6 = 20 secondes minimum (polling complet)
0,5 + 5 + 1 + 6 = 12,5 s si current track immédiat
```

Avec **4 variantes d'URL** et échecs de recherche bibliothèque :

```
4 × 20 s = 80 s (borne supérieure scriptée)
3,5 × 20 s ≈ 70 s → cohérent avec ~71 s observés systématiquement
```

La durée **quasi identique sur 5 morceaux** (écart < 0,2 %) indique un **comportement déterministe de notre script** (boucles URL + `delay` AppleScript), pas une variance réseau aléatoire.

### Cause secondaire (certaine — code)

Après `acquire_song_from_url`, `AppleMusicLibraryAcquisition` exécute un **`time.sleep(settle_delay_seconds)`** supplémentaire (= **6 s**) pour les statuts `added`, `duplicated`, `opened` — **en dehors** du span `acquire_song_from_url` mais **dans** `resolve_total`.

Puis `AppleMusicResolver._refresh_library_candidates_with_retries` peut ajouter jusqu'à **6 × 5 s = 30 s** de polling Python entre tentatives `collect_candidates_batch`.

### Ce qui n'est PAS la cause (invalidé par mesures)

| Hypothèse | Statut |
|-----------|--------|
| Bridge Python cold start dominant | **Invalidé** — delivery 719 ms, resolve = acquisition |
| Livraison playlist / pacing delivery | **Invalidé** — 0,2 % du total |
| Timeout `run_applescript` (120 s) | **Invalidé** — 71 s << 120 s, pattern reproductible |
| Absence compte développeur Apple comme cause unique | **Non démontré** — délais majoritairement **notre script** |

---

## Chronologie détaillée des ~71 secondes

Hypothèse la plus probable alignée sur les mesures (à confirmer par spans Phase B détaillés) :

| Étape | Durée estimée | Source |
|-------|---------------|--------|
| Phase A : `add URL` × 4 variantes | 0–40 s | Music.app bloque sur `add` si abonnement (variable) ; souvent échec rapide |
| Phase B : itération URL 1 | ~20 s | 8+5+1+6 s scriptés + `open`/`duplicate` |
| Phase B : itération URL 2 | ~20 s | recherche biblio échoue → URL suivante |
| Phase B : itération URL 3 | ~20 s | idem |
| Retour `duplicated` ou `added` | ~11 s partiel | 3,5ᵉ itération ou succès recherche |
| **Total `acquire_song_from_url`** | **~71 s** | Mesure baseline |
| `post_acquire_python_sleep` | **+6 s** | `library_acquisition.py` |
| `collect_candidates_batch` retries | 0–25 s | resolver, si biblio pas encore visible |

**Fichiers** :

- `playlist_builder/integration/apple_music/applescript_client.py` — `_build_acquire_song_script`
- `playlist_builder/integration/apple_music/library_acquisition.py` — `settle_delay_seconds`, post-sleep
- `playlist_builder/integration/apple_music/resolver.py` — `_AUTOMATIC_ACQUISITION_LIBRARY_ATTEMPTS = 6`, retry 5 s

---

## Instrumentation fine (5.3.2)

Avec `RESONANCE_PERF_TRACE=1`, `acquire_song_from_url` bascule en **mode phased** (même logique, spans séparés) :

| Span | Description |
|------|-------------|
| `acquire.add_url` | Tentative `add URL` par variante |
| `acquire.open_location` | `open location` Music.app |
| `acquire.poll_current_track` | Attente `current track` (16×0,5 s) |
| `acquire.play_delay` | `delay 5 s` |
| `acquire.play` | Commande `play` |
| `acquire.post_play_delay` | `delay 1 s` |
| `acquire.duplicate_to_library` | `duplicate … to source "Library"` |
| `acquire.settle_delay` | `delay 6 s` |
| `acquire.library_search` | Recherche biblio post-duplication |
| `acquire.post_acquire_python_sleep` | Sleep Python post-acquisition |

Sans `RESONANCE_PERF_TRACE`, le script monolithique est **inchangé** (pas de régression UX/workflow).

---

## Acquisition : est-elle nécessaire ?

### Contexte (certain)

L'acquisition est déclenchée quand :

1. Le morceau est **absent de la bibliothèque locale** Music.app
2. `acquire_missing=True` (config production)
3. Un candidat iTunes catalogue est trouvé avec confiance ≥ 70 %

La livraison (`add_tracks_by_persistent_id_batch`) nécessite un **`persistent ID` bibliothèque** — pas un ID catalogue Apple Music.

### Alternatives analysées

| Approche | Faisable ? | Avantage | Limite |
|----------|------------|----------|--------|
| Ajout direct playlist par URL catalogue | **Non prouvé** AppleScript | Éviterait biblio | `duplicate`/`add` catalogue→biblio reste requis pour `persistent ID` |
| Ajout par `persistent ID` sans biblio | **Non** | — | Les IDs catalogue ≠ IDs biblio locale |
| Skip acquisition si déjà en biblio | **Oui** (déjà via IdentityCache) | Cache chaud rapide | Ne résout pas 1er import |
| Acquisition asynchrone (continuer import) | **Partiel** | UX plus fluide | Livraison impossible sans PID ; change workflow |
| MusicKit `POST /v1/me/library` | **Oui avec compte dev** | API directe, pas AppleScript | JWT, quotas, hors stack actuelle |
| Réduire variantes URL / délais scriptés | **Oui** | −40–70 % par morceau | Risque stabilité Music.app à valider |

**Conclusion** : pour le workflow AppleScript actuel, l'acquisition **est nécessaire** pour obtenir un `persistent ID` bibliothèque. Le problème n'est pas l'existence de l'acquisition mais **sa stratégie et ses délais internes**.

---

## Comportement Music.app (AppleScript)

Quand `open location` est appelé sur une URL Apple Music :

1. Music.app **ouvre la fiche** du morceau (navigateur interne / vue catalogue)
2. Le morceau **n'est pas automatiquement** dans la bibliothèque utilisateur (abonnement streaming)
3. Notre script attend que `current track` soit défini (lecture démarre ou focus morceau)
4. `play` lance la lecture
5. `duplicate current track to source "Library"` **copie** le morceau streamé vers la bibliothèque locale — pattern documenté pour contenu Apple Music par abonnement
6. On **poll la bibliothèque** via `search library playlist 1` pour obtenir le `persistent ID`

**Ce n'est pas** un timeout Apple Music externe de 71 s — c'est **notre enchaînement** d'attentes + itérations URL.

Référence Apple : [Music.app AppleScript dictionary](https://developer.apple.com/library/archive/documentation/AppleApplications/Conceptual/AppleScriptLangGuide/) — commandes `add`, `open location`, `duplicate`, `search`.

---

## MusicKit : impact hypothétique (analyse seulement)

| Aspect | MusicKit API | Stack actuelle |
|--------|--------------|----------------|
| Ajout bibliothèque | `POST /v1/me/library` (compte dev + token utilisateur) | AppleScript `duplicate` |
| Résolution catalogue | `/v1/catalog/.../songs` | iTunes Search API publique |
| Livraison playlist | Pas d'équivalent direct playlist utilisateur documenté simplement | AppleScript `duplicate` vers playlist |
| Ce qui accélérerait | Acquisition API (ms–s vs 71 s script) | — |
| Ce qui ne changerait pas | Pacing delivery, clear playlist, Music.app pour playlist user | — |
| Prérequis | Apple Developer Program (~99 USD/an), JWT, Music User Token | Aucun |

**Conclusion** : MusicKit pourrait réduire **l'acquisition catalogue→biblio** (part ~90 % mesurée), pas la livraison (déjà 719 ms). Migration = coût business + complexité tokens. **Benchmark A/B requis** avant décision.

---

## Multi-provider : couplage actuel

| Couche | Couplage Apple | Abstraction existante |
|--------|----------------|----------------------|
| `ProviderId` / `IntegrationGateway` | Faible | `ProviderId.SPOTIFY`, `YOUTUBE_MUSIC` déjà définis |
| `import_stream.py` | **Fort** — `ProviderId.APPLE_MUSIC` hardcodé, `darwin` check | À extraire |
| `AppleScriptClient` / `delivery.py` | **Total** | Aucun port générique livraison |
| `resolver.py` + acquisition | **Total** | `CatalogSearchPort` partiel |
| DTO / UI | Faible | Provider-agnostic |
| Swift `ImportViewModel` | Moyen | Manual polling Apple-specific |

**Verdict** : l'architecture **canonical/gateway** permet d'ajouter Spotify/YouTube Music, mais **import_stream + acquisition + AppleScript** sont le couplage principal à isoler derrière un `LibraryAcquisitionPort` / `PlaylistDeliveryPort` en Phase ultérieure.

---

## Recommandations par ROI (5.3.3)

| # | Action | Gain estimé | Complexité | Risque |
|---|--------|-------------|------------|--------|
| **R1** | Réduire itérations URL (1 URL canonique au lieu de 4–5) | **−40 à −60 s / morceau** (si 3–4 itérations Phase B évitées) | Faible | Moyen — tester par type URL |
| **R2** | Réduire délais scriptés (`play_delay` 5→1, `settle` 6→2, poll 16→4) | **−10 à −15 s / itération** | Faible | Moyen — stabilité duplicate |
| **R3** | Court-circuiter Phase B si `add URL` échoue vite — ne pas enchaîner toutes variantes | **−20 à −40 s** | Moyenne | Faible |
| **R4** | Supprimer `post_acquire_python_sleep` redondant (6 s déjà dans script) | **−6 s / morceau** | Faible | Faible |
| **R5** | Réduire `_AUTOMATIC_ACQUISITION_LIBRARY_ATTEMPTS` (6→2) avec backoff adaptatif | **−0 à −20 s** | Faible | Faible |
| **R6** | Bridge persistant | **< 1 %** sur cet import | Élevée | — **déprioritisé** |
| **R7** | MusicKit acquisition API | **−60 à −68 s / morceau** (estimation) | Très élevée | Business + tokens |

**Import 5 morceaux avec acquisition** : gain potentiel R1+R2+R4 ≈ **−280 à −350 s** (~70–90 % du resolve actuel).

---

## Plan Phase 5.3.3 proposé

1. **Re-mesurer** avec spans phased (`RESONANCE_PERF_TRACE=1`) sur 1 morceau — valider répartition exacte add vs open vs delays
2. **POC R4** : retirer sleep Python redondant — mesure avant/après (1 PR)
3. **POC R1+R2** : 1 URL + délais réduits — test régression 10 morceaux macOS
4. **Décision go/no-go MusicKit** — uniquement si R1–R4 insuffisants
5. **Rapport final** `reports/perf/phase-5-3-final.md` vs baseline

---

## Hypothèses — bilan

| Hypothèse | Résultat |
|-----------|----------|
| Bridge Python = goulot principal | **Invalidée** |
| Delivery AppleScript = goulot | **Invalidée** |
| `acquire_song_from_url` = goulot (~90 %) | **Validée** |
| ~71 s = délais scriptés + multi-URL | **Validée** (code + variance < 0,2 %) |
| Timeout externe Apple 71 s | **Invalidée** |
| Music.app seul responsable | **Partiellement** — `add`/`open` bloquent, mais délais `delay` sont **notre code** |
| Acquisition évitable sans changer stack | **Invalidée** pour persistent ID biblio |
| MusicKit résoudrait tout | **Invalidée** — livraison déjà rapide ; cible = acquisition |
