# Resonance Vision 2030

**Document fondateur** — vision produit à long terme  
**Audience :** fondateurs, contributeurs, partenaires  
**Date :** juillet 2026  
**Statut :** stratégie produit — aucune fonctionnalité nouvelle impliquée par ce document seul

---

## Résumé exécutif

**Resonance** veut devenir le **meilleur gestionnaire de playlists multi-providers au monde** — pas un nouveau service de streaming, pas un hébergeur de fichiers audio, pas un clone de Spotify.

Resonance est un **système d'exploitation local-first pour vos playlists** : une bibliothèque musicale *personnelle* qui vit sur votre machine, se synchronise avec les services que *vous* choisissez, et applique une intelligence de composition, de correspondance et de résolution de conflits que les plateformes fermées ne peuvent pas offrir.

**Notre avantage structurel :** nous ne possédons ni catalogue, ni droits, ni lock-in. Nous orchestrons.

---

## 1. Pourquoi Resonance existe

### Le problème fondamental

Aujourd'hui, une playlist n'est pas un objet portable :

| Douleur utilisateur | Cause structurelle |
|---------------------|-------------------|
| « Ma playlist est prisonnière d'Apple Music » | Chaque service possède son propre modèle, ses IDs, son ordre |
| « Je veux la même vibe sur Spotify et sur ma bibliothèque Plex » | Aucun outil ne combine *composition intelligente* + *sync fiable* + *neutralité* |
| « Soundiiz a mal matché 30 % des morceaux » | Les convertisseurs one-shot ignorent le contexte, l'historique, les exclusions |
| « J'ai modifié la playlist sur mon téléphone, tout est cassé sur le Mac » | Pas de SSOT locale, pas de versioning, pas d'undo |
| « Je veux des règles : ajouter chaque vendredi les nouveautés de mes artistes » | Les smart playlists des services sont silotées et non composables |
| « Je ne veux pas donner mes tokens OAuth à un cloud tiers » | Les outils SaaS centralisent secrets et métadonnées |

### Notre réponse

Resonance sépare trois responsabilités que l'industrie confond :

```text
1. COMPOSITION  — transformer une intention en playlist (seeds, règles, scoring)
2. BIBLIOTHÈQUE — votre vérité locale (ordre, tags, versions, historique)
3. PROVIDERS    — sources et destinations interchangeables (Apple, Spotify, Plex…)
```

**Sans compte Resonance obligatoire. Sans stockage audio. Sans dépendance à un seul écosystème.**

---

## 2. Ce qui nous différencie

### Comparatif honnête

| Capacité | Spotify / Apple Music | Soundiiz / TuneMyMusic | Plex / Jellyfin | **Resonance** |
|----------|----------------------|------------------------|-----------------|---------------|
| Smart playlists natives | ✅ (dans le silo) | ❌ | ⚠️ basique | ✅ cross-provider |
| Transfert one-shot | ❌ | ✅ | ❌ | ✅ + continu |
| Sync bidirectionnelle | ❌ | ❌ | ⚠️ local | ✅ plan/apply/conflits |
| SSOT locale | ❌ | ❌ | ⚠️ | ✅ |
| Composition par seeds/scoring | ❌ | ❌ | ❌ | ✅ |
| Résolution conflits explicable | ❌ | ❌ | ❌ | ✅ |
| Local-first / offline | ❌ | ❌ | ✅ | ✅ |
| Open source / extensible | ❌ | ❌ | ⚠️ | ✅ |
| Pas d'hébergement audio | — | — | — | ✅ par design |

### Les cinq différenciateurs réels (notre fossé)

1. **Playlist comme objet de première classe** — versionné, historisé, taggable, synchronisable ; pas un simple export CSV.
2. **Intelligence de correspondance** — scoring unifié, identity cache par provider, qualité de match mesurable et améliorable.
3. **Sync consciente des conflits** — dry-run, résolution guidée, journal d'opérations ; pas un « écraser et prier ».
4. **Neutralité provider** — le moteur ne connaît pas Apple ; les gateways sont remplaçables.
5. **Automatisation ouverte** — API, scripts, raccourcis, Home Assistant ; votre bibliothèque vous appartient.

Ce que nous **ne** vendons pas : découvrir de la nouvelle musique comme TikTok, social feed, ou streaming gratuit.

---

## 3. Principes produit non négociables

| Principe | Implication |
|----------|-------------|
| **Local-first** | Tout fonctionne sans cloud Resonance |
| **Compte Resonance optionnel** | Identity / cloud sync = couche séparée, métadonnées uniquement |
| **Music Providers ≠ Resonance Services** | Jamais dans le même registre |
| **Pas d'audio hébergé** | Snapshots = métadonnées + références provider |
| **Explicabilité** | Chaque match, conflit, règle doit être compréhensible |
| **Undo possible** | Toute mutation locale doit être réversible (objectif 2.0) |
| **Open core** | MIT, contributions, plugins documentés |
| **YAGNI technique** | Pas d'abstraction avant le second cas d'usage réel |

---

## 4. Paliers produit : MVP → 1.0 → 2.0 → 2030

### Légende

| Symbole | Signification |
|---------|---------------|
| ✅ | Livré ou fondation en place |
| 🔄 | En cours |
| 📋 | Planifié palier |
| 💡 | Vision / recherche |

---

### MVP — *où nous sommes* (juillet 2026)

**Promesse :** « Composer et livrer une playlist sur Apple Music, avec une base multi-provider crédible. »

| Domaine | État | Détail |
|---------|------|--------|
| Génération intelligente (seeds, scoring) | ✅ | Moteur Python mature |
| Import streaming Apple Music | ✅ | Manual acquisition, retry |
| App macOS SwiftUI | ✅ | Génération, import, historique |
| Repository local (SSOT) | ✅ | `ManagedPlaylist`, snapshots |
| Sync plan / apply / conflits | ✅ | Append-only production ; mirror partiel |
| YouTube Music expérimental | 🔄 | Lecture / import fichier |
| Multi-provider registry | ✅ | Architecture prête |
| Historique sessions | ✅ | Génération + import |
| UX provider picker | 🔄 | Phase 6.8 |

**Hors scope MVP :** Spotify production, règles auto, cloud, collaboration.

---

### Version 1.0 — *première release publique Open Source*

**Promesse :** « Le gestionnaire de playlists local-first le plus fiable pour Apple Music + un second provider majeur. »

| Domaine | Cible 1.0 |
|---------|-----------|
| **Providers** | Apple Music (production) + Spotify OU YouTube (production) |
| **UX produit** | Wizard sync complet, connect/disconnect providers, picker global |
| **Bibliothèque** | Dashboard playlists gérées, origine, statut sync |
| **Sync** | Push/pull append_only fiable ; dry-run obligatoire |
| **Conflits** | Résolution guidée UI (6.7 livré) |
| **Qualité match** | Score visible par morceau ; rapport import |
| **Documentation** | Contributor + user wiki cohérents |
| **CI / qualité** | Linux + macOS, 500+ tests |
| **Onboarding** | Clone → pytest en 5 min |

**Différenciateur 1.0 :** première app open source qui combine *génération* + *SSOT locale* + *sync provider-neutral*.

---

### Version 2.0 — *Resonance 2.0*

**Promesse :** « Votre bibliothèque musicale personnelle, synchronisée partout, intelligente et sous votre contrôle. »

| Domaine | Cible 2.0 |
|---------|-----------|
| **Providers** | 5+ gateways (Spotify, Deezer, Plex/Jellyfin, local files, …) |
| **Playlists intelligentes** | Règles composables (filtres + seeds + contraintes) |
| **Règles automatiques** | Déclencheurs : calendrier, nouvel album artiste, RSS, webhook |
| **Sync planifiée** | Cron local + notifications ; pas de cloud requis |
| **Sync multi-provider** | Une playlist locale → N destinations ; pull agrégé |
| **Correspondance** | Identity cache enrichi ; feedback utilisateur sur les matchs |
| **Collections & tags** | Taxonomie transversale aux playlists |
| **Favoris** | Morceaux/artistes favoris locaux, réutilisables dans règles |
| **Historique complet** | Journal append-only de toutes mutations |
| **Undo / versioning** | `playlist_version` + rollback N steps |
| **Snapshots temporels** | Archive temporelle ; diff entre deux dates |
| **Visualisation** | Timeline d'évolution, graph de sync, heatmap énergie |
| **Statistiques** | Durée totale, genres, artistes dominants, historique sync |
| **Métadonnées enrichies** | MusicBrainz, Discogs, acoustid — *références*, pas audio |
| **IA assistée** | Suggestions de seeds, résolution conflits, libellés — *opt-in, local ou API user key* |
| **Raccourcis Apple** | Actions : sync, générer, dernière playlist |
| **Scripting** | CLI stable + hooks JSON |
| **API locale** | HTTP localhost documenté (lecture/écriture bibliothèque) |
| **Plugins** | Extension points documentés (gateways, règles, exporters) |

**Différenciateur 2.0 :** seul outil qui traite la playlist comme un *document versionné* vivant sur plusieurs providers.

---

### Vision cinq ans — *2030*

**Promesse :** « L'infrastructure ouverte de référence pour posséder sa musique dans un monde multi-cloud. »

| Domaine | Vision 2030 |
|---------|-------------|
| **Providers** | 15+ intégrations ; communauté de gateways |
| **Collaboration** | Playlists partagées (métadonnées) ; rôles viewer/editor |
| **Resonance Services** | Cloud sync métadonnées optionnel ; pas de musique |
| **IA** | Profils de goût locaux ; explainable recommendations |
| **Home Assistant** | Intégration officielle ; automations domotique-musique |
| **API publique** | API documentée + clés ; rate limit ; webhooks |
| **Marketplace règles** | Templates de playlists intelligentes partagés |
| **iOS / iPadOS** | Parité fonctionnelle macOS |
| **Écosystème** | Plugins tiers, thèmes, exporters (JSON, M3U, Rekordbox…) |
| **Qualité** | Benchmark public de correspondance inter-providers |

**Différenciateur 2030 :** standard de facto open source pour la *portabilité des playlists* — comme Git pour le code, Resonance pour les listes.

---

## 5. Cartographie des fonctionnalités

### 5.1 Playlists intelligentes & règles

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Génération par seeds + scoring | ✅ | ✅ | ✅ | ✅ | **Oui** |
| Contraintes (exclusions, énergie) | ✅ | ✅ | ✅ | ✅ | Oui |
| Règles « si artiste X sort album → ajouter » | ❌ | 📋 | ✅ | ✅ | **Oui** |
| Playlists dynamiques rafraîchies | ❌ | ❌ | ✅ | ✅ | **Oui** |
| Composition multi-sources (library + catalog) | ⚠️ | 📋 | ✅ | ✅ | Oui |

### 5.2 Recommandations

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Scoring explicable | ✅ | ✅ | ✅ | ✅ | Oui |
| « Morceaux similaires » post-generation | ❌ | 📋 | ✅ | ✅ | Modéré |
| Profil de goût persistant | ❌ | ❌ | 📋 | ✅ | Oui (local) |
| Recommendations cross-provider | ❌ | ❌ | 💡 | ✅ | **Oui** |

*Position :* nous ne concurrencions pas Discover Weekly ; nous aidons à **construire** et **maintenir** des listes.

### 5.3 Synchronisation

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Plan sync dry-run | ✅ | ✅ | ✅ | ✅ | Oui |
| Apply append_only | ✅ | ✅ | ✅ | ✅ | Oui |
| Résolution conflits guidée | ✅ | ✅ | ✅ | ✅ | **Oui** |
| Mirror / reorder | ⚠️ | 📋 | ✅ | ✅ | Modéré |
| Sync planifiée (cron) | ❌ | ❌ | ✅ | ✅ | Oui |
| Sync 1 playlist → N providers | ❌ | 📋 | ✅ | ✅ | **Oui** |
| Pull agrégé multi-provider | ❌ | ❌ | 📋 | ✅ | **Oui** |
| Bande passante / quota aware | ❌ | ❌ | 💡 | ✅ | Modéré |

### 5.4 Qualité des correspondances

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Identity cache par provider | ✅ | ✅ | ✅ | ✅ | Oui |
| Manual acquisition | ✅ | ✅ | ✅ | ✅ | Oui |
| Score de confiance affiché | ⚠️ | ✅ | ✅ | ✅ | **Oui** |
| Feedback utilisateur (« mauvais match ») | ❌ | 📋 | ✅ | ✅ | **Oui** |
| ISRC / MusicBrainz enrichment | ❌ | ❌ | 📋 | ✅ | Oui |
| Benchmark public match quality | ❌ | ❌ | ❌ | ✅ | **Oui** |

### 5.5 Bibliothèque, collections, tags

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Playlists gérées (SSOT) | ✅ | ✅ | ✅ | ✅ | **Oui** |
| Snapshots immuables | ✅ | ✅ | ✅ | ✅ | Oui |
| Collections (dossiers) | ❌ | 📋 | ✅ | ✅ | Oui |
| Tags transversaux | ❌ | ❌ | ✅ | ✅ | Oui |
| Favoris morceaux/artistes | ❌ | 📋 | ✅ | ✅ | Modéré |
| Vue « bibliothèque unifiée » | ❌ | ❌ | 📋 | ✅ | **Oui** |

### 5.6 Historique, undo, versioning

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Historique sessions génération/import | ✅ | ✅ | ✅ | ✅ | Oui |
| Journal sync operations | ✅ | ✅ | ✅ | ✅ | Oui |
| `playlist_version` incrémental | ✅ | ✅ | ✅ | ✅ | Fondation |
| Undo dernière action | ❌ | ❌ | ✅ | ✅ | **Oui** |
| Snapshots temporels (point-in-time) | ⚠️ | 📋 | ✅ | ✅ | **Oui** |
| Diff visuel entre versions | ❌ | ❌ | ✅ | ✅ | **Oui** |
| Audit trail exportable | ❌ | 📋 | ✅ | ✅ | Oui |

### 5.7 Collaboration & partage

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Export JSON / fichier | ✅ | ✅ | ✅ | ✅ | Oui |
| Partage fichier snapshot | ⚠️ | ✅ | ✅ | ✅ | Oui |
| Playlists collaboratives temps réel | ❌ | ❌ | ❌ | ✅ | Modéré |
| Collections familiales (cloud metadata) | ❌ | ❌ | 💡 | ✅ | Oui |
| Marketplace templates | ❌ | ❌ | ❌ | ✅ | Oui |

*Position :* collaboration sur **métadonnées**, jamais streaming partagé.

### 5.8 IA

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Scoring déterministe | ✅ | ✅ | ✅ | ✅ | Oui |
| Suggestions seeds (LLM opt-in) | ❌ | ❌ | 📋 | ✅ | Modéré |
| Résolution conflits assistée | ❌ | ❌ | 📋 | ✅ | Oui |
| Profil IA local | ❌ | ❌ | 💡 | ✅ | Oui |
| **Pas de boîte noire obligatoire** | ✅ | ✅ | ✅ | ✅ | **Oui** |

### 5.9 Automatisation & intégrations

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| CLI scripts | ✅ | ✅ | ✅ | ✅ | Oui |
| Raccourcis Apple | ❌ | 📋 | ✅ | ✅ | Oui |
| API HTTP locale | ❌ | ❌ | ✅ | ✅ | **Oui** |
| Webhooks sortants | ❌ | ❌ | 📋 | ✅ | Oui |
| Home Assistant | ❌ | ❌ | 💡 | ✅ | Oui |
| Plugins tiers | ❌ | ❌ | 📋 | ✅ | **Oui** |

### 5.10 Statistiques & visualisation

| Fonctionnalité | MVP | 1.0 | 2.0 | 2030 | Différenciant ? |
|----------------|-----|-----|-----|------|-----------------|
| Compteurs import (added/skipped) | ✅ | ✅ | ✅ | ✅ | — |
| Stats playlist (durée, count) | ⚠️ | ✅ | ✅ | ✅ | Modéré |
| Dashboard bibliothèque | ❌ | 📋 | ✅ | ✅ | Oui |
| Timeline évolution playlist | ❌ | ❌ | ✅ | ✅ | **Oui** |
| Graphe sync / santé providers | ❌ | 📋 | ✅ | ✅ | Oui |

---

## 6. Problèmes que Resonance résout (et ceux qu'il ne résout pas)

### Résolus

| Problème | Comment |
|----------|---------|
| Portabilité des playlists | SSOT locale + sync multi-provider |
| Matchs opaques | Scoring + confiance + feedback |
| Conflits de sync destructifs | Plan → conflits → résolution → apply |
| Lock-in écosystème | Registry ouvert, MIT |
| Automatisation impossible | CLI, API, raccourcis, règles |
| Perte d'historique | Journal + versions + snapshots |

### Explicitement hors scope

| Non-objectif | Raison |
|--------------|--------|
| Streaming audio | Pas notre métier ; les providers le font |
| Hébergement de fichiers | Légal, coût, scope |
| Remplacer Spotify/Apple Music | Nous orchestrons, pas concurrençons |
| Social network musical | Distraction ; pas différenciant |
| DRM circumvention | Illégal et contraire à l'éthique |
| Sync temps réel collaborative type Figma | Complexité ; métadonnées async suffit en 2030 |

---

## 7. Où va Resonance — trajectoire

```text
2026 MVP     →  Composer + livrer (Apple) + fondations sync
2027 1.0     →  Open Source public + 2 providers + UX sync complète
2028 2.0     →  Bibliothèque intelligente + règles + undo + multi-destination
2029         →  API publique + plugins + iOS
2030         →  Standard ouvert + écosystème + collaboration metadata
```

---

## 8. Implications architecture (aperçu)

Voir [TARGET_ARCHITECTURE.md](../architecture/TARGET_ARCHITECTURE.md) pour le détail.

Fondations **déjà posées** pour 2.0 :

- `ManagedPlaylistRepository` (SSOT)
- `RemotePlaylistSnapshot` immuable + archive
- `PlaylistSyncEngine` + conflits provider-neutral
- `playlist_version` sur entités gérées
- `PlaylistSyncOperation` journal
- `ProviderGatewayRegistry` extensible

**À préserver absolument** (ne pas casser avant 2.0) :

- Séparation Music Providers / Resonance Services (ADR-013)
- Contrats bridge stables
- Moteur sync sans `if provider == apple`
- Immutabilité des snapshots historiques

---

## 9. Métriques de succès

| Palier | Métrique clé |
|--------|--------------|
| MVP | 500+ tests ; sync append_only fiable ; 1 provider production |
| 1.0 | 100+ stars GitHub ; 2 providers ; contributor onboarding < 1 h |
| 2.0 | 1000+ utilisateurs actifs ; 5 providers ; undo utilisé > 10 % sessions |
| 2030 | Référence citée dans docs Spotify/Plex ; 10+ gateways communautaires |

---

## 10. Références

- [ROADMAP.md](../ROADMAP.md) — jalons et priorités
- [BACKLOG.md](BACKLOG.md) — epics détaillés
- [TARGET_ARCHITECTURE.md](../architecture/TARGET_ARCHITECTURE.md) — architecture cible
- [ADR-013](../architecture/ADR-013-multi-provider-platform-vision.md) — Music Providers vs Resonance Services
- [ADR-019](../architecture/ADR-019-resonance-product-tiers.md) — paliers produit
- [ARCHITECTURAL_PREP.md](ARCHITECTURAL_PREP.md) — préparation technique immédiate
