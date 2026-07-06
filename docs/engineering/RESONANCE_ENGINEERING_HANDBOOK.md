# Resonance — Engineering Handbook

Document de référence pour l'ingénierie de **Resonance**. Il complète `AGENTS.md`
(règles courtes lues avant chaque tâche) et les ADR (`docs/architecture/ADR-*`).
En cas de conflit, l'ordre de priorité est : instructions explicites de l'utilisateur >
`AGENTS.md` > ADR acceptés > ce handbook.

---

## 1. Vision produit

Resonance est un **moteur universel de composition et de livraison de playlists**.
Ce n'est **pas** une application Apple Music : Apple Music n'est qu'un **provider**.

Objectif à moyen terme : intégrer une dizaine de providers musicaux sans réécrire
le cœur applicatif. Trois contextes bornés :

1. **Composition** — transformer une intention utilisateur (seeds, mots-clés,
   contraintes) en une playlist **canonique**.
2. **Catalog** — découvrir et classer des candidats musicaux depuis des sources
   externes.
3. **Delivery** — résoudre les morceaux canoniques vers des identités provider et
   importer / synchroniser les playlists.

Le Core possède la **composition** et l'**état canonique** de la playlist. Les
providers possèdent la **résolution**, l'**acquisition**, la **livraison** et la
**persistance des identifiants externes**.

Voir `docs/architecture/vision.md` et `docs/architecture/ADR-013-multi-provider-platform-vision.md`.

---

## 2. Rôles

| Rôle | Responsabilité |
|------|----------------|
| **Nicolas** (product owner) | Décide de la vision, des priorités, du périmètre et de l'UX. Approuve les ADR, valide et merge les PR. Seule personne à autoriser une nouvelle phase ou un changement UX. |
| **ChatGPT** (architecte / copilote de réflexion) | Aide à cadrer les phases, rédige/relit les ADR et la documentation, découpe le backlog, prépare les prompts d'agent. Ne modifie pas le code directement. |
| **Cursor Cloud Agent** (implémenteur) | Exécute une tâche cadrée de façon autonome : lit `AGENTS.md`, respecte le périmètre, écrit du code en petits commits, lance les tests, produit un rapport final structuré. Ne redéfinit pas le périmètre ni la vision. |

Principe : **l'agent implémente, il ne décide pas de la stratégie**. Toute ambiguïté
de périmètre se résout en restant conservateur (ne rien élargir) et en le signalant
dans le rapport final.

---

## 3. Invariants d'architecture

Ces invariants sont **non négociables**. Une PR qui les viole doit être refusée.

1. **Le Core ne dépend d'aucun provider.** Aucun module hors `integration/` n'importe
   `integration.apple_music` (ni un futur `integration.spotify`).
2. **Aucun identifiant provider dans les contrats partagés.** Pas de `persistent_id`
   Apple, d'URI Spotify ou de MusicKit song ID dans `canonical/`, l'application, l'UI
   partagée ou le bridge. Ces identifiants vivent dans les adaptateurs provider et
   l'`IdentityCache`.
3. **Les dépendances pointent vers l'intérieur** (dependency rule) :

   ```text
   UI / CLI / Bridge
        ↓
   Application (use cases — provider-neutral)
        ↓
   Canonical model + ports
        ↓
   IntegrationGateway (orchestration only)
        ↓
   Provider gateways (Apple, Spotify, …)
        ↓
   Plateformes externes
   ```

4. **Le scoring et les décisions restent en Python**, déterministes et testables.
   Le code plateforme ne fait que collecter des candidats.
5. **Python 3.12+**, stdlib d'abord ; toute nouvelle dépendance runtime doit être
   justifiée. `Protocol` (ports) plutôt que de profondes hiérarchies d'héritage ;
   dataclasses `frozen=True, slots=True` pour les value objects canoniques.

---

## 4. Règles par couche

### 4.1 Core / canonical (`playlist_builder/canonical/`, `core/`, `scoring/`, `planning/`)

- Vocabulaire **provider-neutral** uniquement (`CanonicalTrack`, `CanonicalPlaylist`,
  `ProviderId`, `ImportStatus`, `ResolutionDecision`, …).
- N'importe rien de l'application ni de l'intégration.
- Logique déterministe et couverte par des tests unitaires.

### 4.2 Application (`playlist_builder/app/`, `use_cases/`)

- Orchestre les cas d'usage via les **ports** (`CatalogSearchPort`,
  `LibraryResolvePort`, `PlaylistDeliveryPort`, `ProviderImportPort`).
- Ne connaît **jamais** AppleScript ni un SDK provider.
- `factory.py` / `settings.py` composent le contexte applicatif ; c'est le seul
  endroit qui câble les implémentations concrètes derrière les ports.

### 4.3 Provider (`playlist_builder/integration/<provider>/`)

- Toute la logique provider-specific : catalogue, résolution bibliothèque,
  acquisition, livraison, mapping, gestion des identifiants externes.
- Implémente les ports du Core ; possède ses propres modèles plateforme.
- Ex. `integration/apple_music/` : catalogue iTunes, delivery AppleScript,
  `acquisition_policy` (cache PID → S1 → manuel, ADR-012).
- `integration/gateway/` : orchestration générique et sélection de provider —
  **sans** AppleScript ni logique Apple-spécifique en dur (voir dette « duck-typing »).

### 4.4 UI partagée (`playlist_builder/ui/shared/`) et app Swift (`apps/resonance/`)

- L'UI manipule des **identités canoniques** et des états d'import
  **provider-agnostiques**, jamais des identifiants provider.
- Couleurs via le theme engine / design tokens uniquement.
- Pas d'action de suppression de playlist / bibliothèque.
- L'app Swift est un **front-end** : elle ne contient pas de logique métier ;
  elle pilote le moteur Python via le bridge.

### 4.5 Bridge runtime (`playlist_builder/app/bridge_runtime/`, `playlist_builder/ui/bridge/`)

- **Provider-neutral, strictement.** Jamais d'AppleScript ni d'import
  `integration.apple_music` dans le bridge.
- Protocole JSON-RPC / JSON-lines : commandes, événements, streaming d'import,
  acquisition manuelle exprimés en termes **canoniques**.
- Le bridge est lancé à la demande comme sous-processus (`python3 -u -m
  playlist_builder.cli.engine_bridge`) — ce n'est pas un service permanent.

---

## 5. Conventions de branches

- Préfixe `cursor/` pour toute branche créée par un agent.
- Nom descriptif en kebab-case, minuscules : `cursor/<descriptif>-<suffixe>`.
- Une branche = une phase / un lot cohérent. Pas de mélange de phases.
- Rester sur la branche courante ; ne pas la quitter sans demande explicite.
- **Small commits**, messages impératifs et descriptifs (« Add … », « Fix … »,
  « Extract … »). Pas de force-push ni d'amend sans instruction explicite.

---

## 6. Définition de « terminé » (Definition of Done)

Une tâche est terminée seulement si :

1. Le **périmètre demandé** est couvert, sans dérive (rien ajouté hors demande).
2. Les **invariants d'architecture** (section 3) sont respectés.
3. Les **tests disponibles passent** (`python3.12 -m pytest -q`) ; tests Swift lancés
   si le toolchain est disponible.
4. Les **tests pertinents sont ajoutés/à jour** pour tout nouveau comportement.
5. La **documentation / ADR** est mise à jour si des frontières ou contrats changent.
6. L'**UX est inchangée** si le changement UX n'a pas été demandé.
7. Un **rapport final structuré** est fourni (fichiers, résumé, validation, état git,
   prochaine action recommandée).
8. Les commits sont poussés et la PR est créée / mise à jour.

---

## 7. Règles ADR (Architecture Decision Records)

- Toute décision qui touche une **frontière** ou un **contrat** exige un ADR.
- Les ADR vivent dans `docs/architecture/ADR-<NNN>-<slug>.md`, numérotés, avec :
  **Status** (Proposed / Accepted / Superseded), **Context**, **Decision**,
  **Consequences**, **References**.
- Un nouveau **provider** exige un ADR provider-local dédié (ex. ADR-014 Spotify,
  ADR-015 YouTube Music) **avant** toute implémentation.
- Un ADR n'est appliqué qu'une fois **Accepted**. Un ADR peut en **superseder** un
  autre (ex. ADR-012 supersede l'acquisition automatique d'ADR-009).
- Le journal court `docs/engineering/ARCHITECTURE_DECISIONS.md` résume les décisions
  déjà figées et renvoie aux ADR complets.

---

## 8. Règles de tests

- Barrière qualité principale : **pytest** (`python3.12 -m pytest -q`, ~2 min).
  Aucun linter/formatter n'est configuré ; ne pas en introduire sans demande.
- Tout nouveau comportement du Core / d'un provider / du bridge doit être couvert
  par des tests unitaires ou d'intégration.
- Les tests d'intégration mockent les appels réseau (API iTunes) → exécution offline
  possible ; ne pas transformer un test en appel réseau réel.
- La logique de l'app Swift est testable **depuis Python** via le bridge
  (`tests/test_ui_bridge_*`, `test_e2e_import_mocked`, …) — pas besoin de Swift pour
  vérifier le contrat du moteur.
- Ne **pas** modifier les tests existants pour faire passer un changement, sauf si
  le changement de comportement est explicitement demandé et documenté.
- Toujours **lancer** les tests avant de conclure et **rapporter l'état réel**
  (ne jamais masquer un échec).

---

## 9. Roadmap multi-provider

Ordre indicatif (le détail priorisé et à jour est dans `NEXT_BACKLOG.md`) :

1. **Stabiliser l'acquisition manuelle Apple** (phase 5.5.x) — reprise fiable.
2. **`ProviderImportPort`** : extraire le streaming d'import + acquisition manuelle
   hors de `import_stream.py` vers un port provider-neutral.
3. **`IncrementalImportPort`** (phase 5.6) : import incrémental non destructif.
4. **Nettoyer le duck-typing** de `IntegrationGateway` (accès `applescript`).
5. **ADR-014 Spotify** puis provider Spotify.
6. **ADR-015 YouTube Music** puis provider YouTube Music.
7. **`ProviderIdentityRegistry`** : façade au-dessus d'`IdentityCache`
   (1 external_id par (canonical_key, provider_id), pas d'équivalence cross-provider
   en v1).
8. **UI fournisseurs connectés** puis polish.

---

## 10. Dette technique connue

- **`IntegrationGateway` duck-typing** : accès `applescript` implicite / couplage
  Apple résiduel dans l'orchestration générique. À neutraliser (P3 du backlog).
- **`import_stream.py`** : le chemin d'import du bridge duplique partiellement
  `IntegrationGateway.import_playlist` ; `ProviderImportPort` n'est pas encore extrait.
- **Acquisition automatique catalogue→bibliothèque** limitée structurellement
  (AppleScript S2 déclassé, ADR-012) — au-delà de la sonde S1, on passe en manuel.
- **MusicKit** possible mais non prioritaire (nécessite un compte Apple Developer payant).

Toute PR devrait laisser la dette **stable ou en baisse**, jamais en hausse
silencieuse ; signaler toute dette introduite dans le rapport final.

---

## 11. Principe « phase N prépare phase N+1 »

Chaque phase doit **préparer** la suivante sans la commencer :

- Livrer un incrément stable et mergeable, jamais un demi-refactor cassé.
- Introduire les ports / abstractions dont la phase suivante aura besoin, mais
  sans implémenter la phase suivante (ex. documenter `ProviderImportPort` avant de
  l'extraire, préparer le terrain multi-provider sans coder Spotify).
- Documenter explicitement, dans `CURRENT_PHASE.md`, la **prochaine phase probable**
  pour que la reprise soit immédiate.

Corollaire : préférer des changements petits et réversibles à un grand saut ;
« big-bang rewrite » interdit.
