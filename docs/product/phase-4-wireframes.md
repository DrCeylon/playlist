# Phase 4.0 — Wireframes (textuels)

Convention : `[ ]` champ, `( )` radio, `[x]` sélection, `│` layout.

---

## 1. Accueil

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Resonance          File   Session   Lab                    🔔  ⚙        │
├────────────┬─────────────────────────────────────────────────────────────┤
│ ◉ Accueil  │  Bonjour, Nicolas                                         │
│ ○ Nouvelle │                                                             │
│ ○ Historiq │  ┌─ Provider ─────────────────────────────────────────────┐ │
│ ○ Lab      │  │  🎧 Apple Music          Connecté · Bibliothèque OK   │ │
│            │  │  Cache identité : 42 entrées   Catalogue : FR         │ │
│            │  └──────────────────────────────────────────────────────┘ │
│            │                                                             │
│            │  ┌─ Dernière session ─────────────────────────────────────┐ │
│            │  │  🏝 Orlando Pool Party 2026                              │ │
│            │  │  Généré hier · 58 morceaux · Import partiel (56/58)   │ │
│            │  │  [ Rouvrir ]  [ Réimporter ]  [ Rapport ]              │ │
│            │  └──────────────────────────────────────────────────────┘ │
│            │                                                             │
│            │  Raccourcis                                                 │
│            │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│            │  │ + Nouvelle   │ │ 📜 Historique│ │ ⚗ Laboratoire│        │
│            │  │   playlist   │ │              │ │              │        │
│            │  └──────────────┘ └──────────────┘ └──────────────┘        │
│            │                                                             │
│            │  Activité récente                                           │
│            │  · E2E Absent — not_found — il y a 2 h                       │
│            │  · E2E Gateway — completed — hier                            │
├────────────┴─────────────────────────────────────────────────────────────┤
│ ⚗ Engine v1.1.0 · 3 providers registered (1 actif)                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Nouvelle playlist

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Accueil          Nouvelle playlist                    [ Générer ⚗ ]   │
├────────────┬─────────────────────────────────────────────────────────────┤
│ sidebar    │  Identité                                                   │
│            │  Nom      [ Orlando Pool Party 2027________________ ]       │
│            │  Desc.    [ Pool party progressive, sans reggaeton_______ ]   │
│            │                                                             │
│            │  Provider                                                   │
│            │  (•) Apple Music   ( ) Spotify (bientôt)   ( ) MusicKit      │
│            │  Pays catalogue [ fr ▼ ]                                    │
│            │                                                             │
│            │  Graines                                                    │
│            │  ┌─────────────────────────────────────────────────────┐   │
│            │  │ Artiste [ Kygo________ ]  Morceau [ Firestone___ ]  │   │
│            │  │ Poids   [ ====●===== ] 1.0          [ + Ajouter ]   │   │
│            │  └─────────────────────────────────────────────────────┘   │
│            │                                                             │
│            │  Ambiance & taille                                          │
│            │  Mots-clés [ tropical, deep house, sunset____________ ]     │
│            │  Morceaux  [ 50 ]    ou    Durée [ 180 ] min               │
│            │                                                             │
│            │  Courbe d'énergie                                           │
│            │  Profil [ Montée progressive ▼ ]                            │
│            │  ┌ preview graphique ─────────────────────────────────┐    │
│            │  │     ╭──╮      ╭────╮                              │    │
│            │  │  ╭──╯  ╰──────╯    ╰──╮  Warm → Peak → Cool       │    │
│            │  └──────────────────────────────────────────────────┘    │
│            │                                                             │
│            │  Exclusions                                    [ + Règle ]  │
│            │  · Artiste  Pitbull                                         │
│            │  · Genre    reggaeton                                       │
│            │                                                             │
│            │              [ Annuler ]    [ Générer la playlist ⚗ ]      │
└────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 3. Preview / Résultat

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Retour    Orlando Pool Party 2027          [ Modifier ] [ Importer ▶ ]│
├──────────────────────────────────────────────────────────────────────────┤
│  ⚗ 50 morceaux · confiance moyenne 84 % · 3 sections                    │
│  Provider : Apple Music · Estimation : 2 acquisitions catalogue         │
├──────────────────────────────────────────────────────────────────────────┤
│  ▼ 🌴 Warm Up Tropical (14)                                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 01  Kygo — Firestone           ████████░░ 92   cache probable     │  │
│  │ 02  Lost Frequencies — Reality ███████░░░ 88   catalogue          │  │
│  │ 03  Klingande — Jubel          ██████░░░░ 81                      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ▼ ☀️ Sunny Vibes (18)                                                   │
│  ▼ 🌙 Closing (18)                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  [ Régénérer ]  [ Exporter JSON ]  [ Importer vers Apple Music ▶ ]      │
└──────────────────────────────────────────────────────────────────────────┘
```

**Détail morceau (sheet) :**

```text
┌─ Kygo — Firestone ──────────────────────────────┐
│ Score : 92 · Confiance : haute                  │
│ Raisons : titre exact, artiste fuzzy, seed    │
│ Source : catalogue iTunes FR                  │
│ [ Voir candidats alternatifs ]  (mode lab)     │
└───────────────────────────────────────────────┘
```

---

## 4. Import (progression)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Import en cours                                              [ Annuler ] │
├──────────────────────────────────────────────────────────────────────────┤
│  Orlando Pool Party 2027 → Apple Music · Sync                              │
│  ████████████████████░░░░░░░░░░  32 / 50                                 │
│                                                                          │
│  🔍 Résolution : Kyo — Dernière danse…                                    │
│                                                                          │
│  Résumé live                                                               │
│  ✅ ajoutés        28                                                     │
│  ⏭ déjà présents    2                                                     │
│  📥 acquisitions    1   ← en cours                                        │
│  ❌ non trouvés      1                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│  Journal (défilant)                                                       │
│  12:04:02  cache hit   Kygo — Firestone                                   │
│  12:04:05  added       Lost Frequencies — Reality                          │
│  12:04:18  acquisition Kyo — Dernière danse (auto)                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Attente manuelle Music.app

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ⏸ Acquisition manuelle requise                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│     Kyo — Dernière danse                                                 │
│     Correspondance catalogue : Kyo — Dernière danse (confiance 98 %)     │
│                                                                          │
│     1. Music.app s’est ouvert sur le morceau                             │
│     2. Cliquez sur ＋ ou « Ajouter à la bibliothèque »                    │
│     3. Vérifiez qu’il apparaît dans Bibliothèque                         │
│     4. Revenez ici et continuez                                          │
│                                                                          │
│     [ Ouvrir Music.app ]                                                 │
│                                                                          │
│              [ Ignorer ce morceau ]    [ J’ai ajouté — Continuer ▶ ]    │
│                                                                          │
│  ⚠️ Rien n’a été supprimé de votre bibliothèque ou de vos playlists.     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Diagnostics / Laboratoire

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ⚗ Laboratoire                    Mode : ( Simple ) ( ● Architecte )      │
├────────────┬─────────────────────────────────────────────────────────────┤
│ Filtres    │  Session [ E2E Absent ▼ ]   Provider [ Apple Music ▼ ]     │
│            │                                                             │
│            │  Pipeline (dernière exécution)                              │
│            │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│            │  │ Génér. │→│ Score  │→│ Gateway│→│ Acquis.│→│ Deliver│   │
│            │  │  —     │ │  —     │ │   ✓    │ │   ⚠    │ │   —    │   │
│            │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│            │                                                             │
│            │  Timeline                                                    │
│            │  12:04:00  gateway.import_playlist sync=true                │
│            │  12:04:01  resolver.cache_miss Kyo — Dernière danse         │
│            │  12:04:02  catalog.search confidence=98                     │
│            │  12:04:05  acquisition.opened                                │
│            │  12:04:35  import.not_found                                   │
│            │                                                             │
│            │  [ Exporter JSON ]  [ Copier ]  [ Ouvrir dossier reports ]  │
└────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 7. Historique

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Historique                          [ Filtrer ▼ ]  [ Rechercher_____ ]  │
├──────────────────────────────────────────────────────────────────────────┤
│  Aujourd’hui                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ E2E Absent · 1 morceau · not_found · Apple Music        11:33     │  │
│  │ [ Relancer ]  [ Importer ]  [ Rapport ]                            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  Hier                                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Orlando Pool Party 2026 · 58 morceaux · partial · Apple   18:02   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Paramètres

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Paramètres                                                                │
├──────────────────────────────────────────────────────────────────────────┤
│  Provider                                                                 │
│    Défaut          [ Apple Music ▼ ]                                      │
│    Pays catalogue  [ fr ▼ ]                                               │
│                                                                          │
│  Apparence                                                                │
│    Thème           [ Apple Music Dark ▼ ]    [ Aperçu ]                   │
│                                                                          │
│  Import                                                                   │
│    [x] Acquisition catalogue automatique                                  │
│    [ ] Attendre confirmation manuelle si échec auto                        │
│                                                                          │
│  Cache                                                                    │
│    Identité   cache/identity.json        [ Vider ]                        │
│    Catalogue  cache/itunes_catalog.json  [ Vider ]                        │
│                                                                          │
│  Avancé                                                                   │
│    [ ] Mode laboratoire par défaut                                        │
│    Chemin engine   [ auto-detect ]                                        │
│                                                                          │
│  À propos   Resonance 0.1.0 · Engine 1.1.0                               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## iPhone adaptations (résumé)

| Écran | Adaptation |
|-------|------------|
| Accueil | cartes empilées, provider compact |
| Nouvelle | `NavigationStack` step ou long scroll |
| Preview | sections accordion full-width |
| Import | bottom sheet progression |
| Lab | masqué par défaut, dans Réglages → Avancé |
| Paramètres | `Form` style inset grouped |

## Related

- [phase-4-ux-flows.md](phase-4-ux-flows.md)
- [design-system.md](design-system.md)
