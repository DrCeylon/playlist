# 🎧 Resonance

*Compose, own, and sync your playlists — locally first, across music services.*

---

## En une phrase

**Resonance** transforme une intention musicale (mots-clés, morceaux de référence, contraintes) en playlists que tu contrôles — sur ton Mac, puis vers Apple Music, YouTube Music, et d'autres services.

→ Vision : [Vision et objectif](Vision-et-Objectif) · [Product Vision (EN)](../docs/PRODUCT_VISION.md)

## Trois façons d'utiliser le projet

| Mode | Statut | Description |
|------|--------|-------------|
| **App macOS Resonance** | ✅ Production | SwiftUI — génération, import, playlists, sync, conflits |
| **CLI assisté** | ✅ Production | `generate_playlist.py` → JSON → Apple Music |
| **CLI manuel** | ✅ Production | JSON écrit à la main → `create_playlist.py` |

## Pour les contributeurs

Documentation en anglais dans le dépôt :

| Doc | Contenu |
|-----|---------|
| [README](../README.md) | Point d'entrée GitHub |
| [CONTRIBUTING](../CONTRIBUTING.md) | Comment contribuer |
| [ARCHITECTURE](../docs/ARCHITECTURE.md) | Design système |
| [ROADMAP](../docs/ROADMAP.md) | Feuille de route |
| [AGENTS](../AGENTS.md) | Agents IA |

**Tests :** 490+ Python · Swift sur CI macOS

## Ce que tu peux faire aujourd'hui

| Action | Outil |
|--------|-------|
| Générer une playlist intelligente | App Resonance ou `generate_playlist.py` |
| Importer dans Apple Music | App Resonance (macOS) |
| Gérer des playlists locales | App → Playlists |
| Synchroniser avec un service | App → Synchronisation |
| Connecter YouTube Music (exp.) | App → Services musicaux |

## Navigation

**Utilisateurs**
- [Guide de démarrage](Guide-de-demarrage)
- [Workflow complet](Workflow-complet)
- [Dépannage & FAQ](Depannage-et-FAQ)

**Produit**
- [Vision et objectif](Vision-et-Objectif)
- [Principes produit](Principes-Produit)
- [État des phases](Etat-des-Phases)

**Technique**
- [Architecture (EN)](../docs/ARCHITECTURE.md)
- [Provider Platform (EN)](../docs/PROVIDER_PLATFORM.md)
- [Architecture technique (archive)](Architecture-Technique)

---

*Projet open source (MIT). Local-first. Aucun compte Resonance requis.*
