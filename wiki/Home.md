# 🎧 Resonance — Playlist Builder

*Bienvenue — génère tes playlists à partir de mots-clés, de morceaux de référence, ou d'une liste que tu as préparée.*

---

## En une phrase

**Générer des playlists** à partir de **mots-clés** ou de **morceaux de référence** — en CLI aujourd'hui, en app macOS **Resonance** demain.

→ Vision complète : [Vision et objectif](Vision-et-Objectif)

## Trois façons d'utiliser le projet

| Mode | Statut | Description |
|------|--------|-------------|
| **CLI manuel** | ✅ Disponible | JSON → `create_playlist.py` |
| **CLI assisté** | ✅ Disponible | Seeds + mots-clés → `generate_playlist.py` |
| **App macOS Resonance** | 🚧 Phase 4 | SwiftUI — shell + builder playlist |

## Ce que tu peux faire aujourd'hui

| Action | Outil | Coût |
|--------|-------|------|
| Générer une playlist (seeds + contraintes) | `generate_playlist.py` | Gratuit |
| Vérifier le catalogue Apple | `check_catalog.py` | Gratuit |
| Créer la playlist dans Apple Music (macOS) | `create_playlist.py` | Gratuit |
| Prévisualiser sans toucher à Music | `--dry-run` | Gratuit |
| App macOS Resonance (shell + thèmes) | `apps/resonance` | Gratuit |
| MusicKit API (catalogue direct) | `--engine musickit` | **Expérimental** |

## Workflow CLI (3 étapes)

```
1. generate_playlist.py  →  JSON généré (optionnel)
2. check_catalog.py      →  Rapport HTML avec liens Apple Music
3. create_playlist.py    →  Playlist créée dans l'app Musique
```

Le workflow manuel (JSON écrit à la main) reste supporté.

## Exemple fourni : Orlando Pool Party 2026

Playlist d'exemple du créateur — 7 sections, 96 morceaux, montée progressive.

→ [Playlist Orlando Pool Party](Playlist-Orlando-Pool-Party)

## Navigation du wiki

**Vision**
- [**Vision et objectif**](Vision-et-Objectif) ← commence ici
- [À propos — qui je suis](A-propos)
- [Principes produit](Principes-Produit)

**Démarrer**
- [Guide de démarrage rapide](Guide-de-demarrage)
- [Workflow complet](Workflow-complet)

**Référence**
- [Format JSON des playlists](Format-JSON-Playlist)
- [Commandes et options CLI](Commandes-et-Options)
- [Architecture technique](Architecture-Technique)

**Évolution**
- [Phase 2 — Génération intelligente](Phase-2-Generation)
- [**Phase 4 — Interface Resonance**](Phase-4-Interface-Resonance) ← **nouveau**
- [MusicKit (expérimental)](MusicKit-Experimental)
- [Feuille de route iOS](Feuille-de-route-iOS)

**Support**
- [Dépannage et FAQ](Depannage-et-FAQ)

## Vision long terme

Une **app Apple** (macOS, puis iOS) — **Resonance** — où n'importe qui génère une playlist depuis une interface soignée, branchée sur le même moteur Python.

→ [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance) · [Feuille de route iOS](Feuille-de-route-iOS)

---

*Projet perso, ouvert à tous. Écoute ce que tu veux — l'outil s'adapte à toi, pas l'inverse.*
