# Architecture Decisions — Journal court

Résumé chronologique et compact des décisions **déjà figées**. Chaque entrée renvoie
à l'ADR complet quand il existe (`docs/architecture/ADR-*`). Ce journal ne remplace
pas les ADR : il permet une reprise rapide du contexte.

Format : `Décision` — `Statut` — `Pourquoi / conséquence` — `Réf`.

---

- **Resonance Core provider-neutral** — *Accepté*.
  Le cœur ne dépend d'aucun provider ; il possède la composition et l'état canonique.
  Aucun identifiant provider dans les contrats partagés.
  Réf : `docs/architecture/vision.md`, `ADR-001-canonical-model.md`, `ADR-013`.

- **Apple Music est un provider** — *Accepté*.
  Apple Music n'est pas le centre du produit mais une implémentation de ports parmi
  d'autres, isolée dans `integration/apple_music/`.
  Réf : `ADR-004`, `ADR-005`, `ADR-013`.

- **`IdentityCache` comme primitive d'identité cross-provider** — *Accepté*.
  Persistance des identifiants externes par provider ; supporte N providers sans
  changement de schéma. Un `ProviderIdentityRegistry` (façade) est prévu, pas encore fait.
  Réf : `ADR-003`, `ADR-013`.

- **ADR-012 — Politique d'acquisition Apple : cache PID → S1 rapide → manuel** —
  *Accepté* (supersede l'acquisition automatique d'ADR-009).
  L'acquisition automatique catalogue→bibliothèque (AppleScript S2) est déclassée
  (lente, ~71 s/titre, échecs -10006). Production : fast path cache PID, sinon sonde
  S1 (`add URL`), sinon ouverture du lien catalogue + **acquisition manuelle**.
  Réf : `ADR-012-apple-catalog-acquisition-production-policy.md`.

- **`ProviderImportPort` introduit en phase 5.5** — *En cours*.
  Extraction du streaming d'import + acquisition manuelle hors de `import_stream.py`
  vers un port provider-neutral, pour découpler le bridge d'Apple.
  Réf : `ADR-013` (`ProviderImportPort*`), `CURRENT_PHASE.md`.

- **Spotify / YouTube Music hors scope tant qu'il n'y a pas d'ADR** — *Accepté*.
  Aucun code provider Spotify/YouTube avant un ADR provider-local accepté
  (ADR-014 Spotify, ADR-015 YouTube Music).
  Réf : `ADR-013` (non-goals), `NEXT_BACKLOG.md` (P4, P5).

- **MusicKit : potentiel mais non prioritaire** — *Accepté (différé)*.
  MusicKit pourrait fiabiliser les ajouts programmatiques, mais nécessite un compte
  Apple Developer payant. Ne bloque pas la livraison actuelle ; reste expérimental.
  Réf : `ADR-012` (Future work), `docs/musickit.md`.
