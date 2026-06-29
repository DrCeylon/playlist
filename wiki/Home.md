# 🎧 Apple Music Playlist Builder

*Bienvenue — génère tes playlists Apple Music à partir de mots-clés, de morceaux de référence, ou d'une liste que tu as préparée.*

---

## En une phrase

**Générer des playlists Apple Music** à partir de **mots-clés** ou de **morceaux de référence** — pour tout le monde, gratuitement, sans prise de tête.

→ Vision complète : [Vision et objectif](Vision-et-Objectif)

## Deux façons d'utiliser l'app

| Mode | Statut | Description |
|------|--------|-------------|
| **Manuel** | ✅ Disponible | Tu écris un JSON → l'app crée la playlist |
| **Assisté** | 🚧 Phase 2 | Tu donnes des seeds + mots-clés → l'app génère et crée |

Les deux coexistent. Choisis selon ton envie du moment.

## Ce que tu peux faire aujourd'hui

| Action | Outil | Coût |
|--------|-------|------|
| Vérifier les morceaux dans le catalogue Apple | `check_catalog.py` | Gratuit |
| Créer la playlist dans Apple Music (macOS) | `create_playlist.py` | Gratuit |
| Prévisualiser sans toucher à Music | `--dry-run` | Gratuit |
| MusicKit API (catalogue direct) | `--engine musickit` | **Expérimental** — licence Apple Developer payante |

## Workflow manuel (3 étapes)

```
1. check_catalog.py     →  Rapport HTML avec liens Apple Music
2. Ajout manuel         →  Morceaux manquants dans ta bibliothèque
3. create_playlist.py   →  Playlist créée dans l'app Musique
```

## Exemple fourni : Orlando Pool Party 2026

Playlist d'exemple du créateur — 7 sections, 96 morceaux, montée progressive.  
C'est **sa** pool party à Orlando, **ses** goûts. Toi, tu fais ce qui te plaît.

→ [Playlist Orlando Pool Party](Playlist-Orlando-Pool-Party)

## Navigation du wiki

- [**Vision et objectif**](Vision-et-Objectif) ← commence ici
- [À propos — qui je suis](A-propos)
- [Guide de démarrage rapide](Guide-de-demarrage)
- [Workflow complet](Workflow-complet)
- [Format JSON des playlists](Format-JSON-Playlist)
- [Commandes et options CLI](Commandes-et-Options)
- [Architecture technique](Architecture-Technique)
- [Phase 2 — Génération intelligente](Phase-2-Generation)
- [MusicKit (expérimental)](MusicKit-Experimental)
- [Feuille de route iOS](Feuille-de-route-iOS)
- [Principes produit](Principes-Produit)
- [Dépannage et FAQ](Depannage-et-FAQ)

## Vision long terme

Une **app iOS** pour que **n'importe qui** génère une playlist depuis son iPhone — mots-clés, morceaux de référence, un tap, c'est dans Apple Music.

→ [Feuille de route iOS](Feuille-de-route-iOS)

---

*Projet perso, ouvert à tous. Écoute ce que tu veux — l'outil s'adapte à toi, pas l'inverse.*
