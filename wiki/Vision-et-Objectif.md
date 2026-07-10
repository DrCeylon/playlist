# Vision et objectif

*Pourquoi Resonance existe — la boussole du projet.*

📖 **Vision long terme :** [RESONANCE_VISION_2030](../docs/product/RESONANCE_VISION_2030.md) · [Roadmap](../docs/ROADMAP.md)

---

## En une phrase

**Resonance est un système d'exploitation local-first pour vos playlists** — composer intelligemment, posséder votre bibliothèque sur votre machine, synchroniser avec les services musicaux que *vous* choisissez.

Ce n'est pas un service de streaming. Ce n'est pas un hébergeur de fichiers audio. C'est **l'infrastructure ouverte** qui rend vos playlists portables.

---

## Pourquoi Resonance existe

| Problème | Réponse Resonance |
|----------|-------------------|
| Playlists prisonnières d'un seul service | Bibliothèque locale = source de vérité ; sync multi-provider |
| Convertisseurs one-shot (Soundiiz…) | Sync continu avec résolution de conflits |
| Smart playlists silotées | Règles composables cross-provider (objectif 2.0) |
| Pas d'historique ni d'undo | Versioning et snapshots (fondations en place) |
| Lock-in écosystème | Open source, MIT, gateways remplaçables |

---

## Ce qui nous différencie

1. **Playlist comme objet de première classe** — versionnée, historisée, synchronisable
2. **Intelligence de correspondance** — scoring explicable, cache d'identité par provider
3. **Sync consciente des conflits** — plan → conflits → résolution → apply
4. **Neutralité provider** — le moteur ne connaît pas Apple Music
5. **Automatisation ouverte** — CLI, API locale (2.0), raccourcis, Home Assistant (2030)

---

## Paliers produit

| Palier | Promesse |
|--------|----------|
| **MVP** (2026) | Composer + livrer sur Apple Music ; fondations sync |
| **1.0** (2027) | Open Source public ; 2 providers ; UX sync complète |
| **2.0** (2028) | Bibliothèque personnelle : règles, undo, sync multi-destination |
| **2030** | Standard ouvert pour la portabilité des playlists |

Détail complet : [RESONANCE_VISION_2030](../docs/product/RESONANCE_VISION_2030.md)

---

## Principes non négociables

| Principe | Signification |
|----------|---------------|
| **Local-first** | Tout fonctionne sans cloud Resonance |
| **Compte optionnel** | Identity / cloud = métadonnées uniquement, jamais obligatoire |
| **Pas d'audio hébergé** | Snapshots = métadonnées + références provider |
| **Music Providers ≠ Resonance Services** | Jamais confondus dans le code |
| **Open source** | MIT — fork, contribue, étends |

---

## L'objectif concret aujourd'hui (MVP)

Tu donnes une **intention musicale**. Resonance construit la playlist et la livre.

| Mode | Tu fournis… | Resonance… |
|------|-------------|------------|
| **Génération** | Seeds, mots-clés, contraintes | Compose via le moteur de scoring |
| **Import** | Playlist générée ou JSON | Livre dans Apple Music (manual acquisition si besoin) |
| **Sync** | Playlist locale liée à un provider | Plan dry-run → résolution conflits → apply |
| **App macOS** | Interface SwiftUI | Génération, import, historique, gestionnaire |

Les modes coexistent avec le **CLI historique** (JSON manuel, `create_playlist.py`).

---

## Pour qui ?

**Tout le monde** — particuliers, DJs, curateurs, développeurs.

- Tu veux une playlist pool party ? OK
- Tu veux synchroniser Apple Music et Spotify ? OK (objectif 1.0)
- Tu veux des règles automatiques le vendredi ? OK (objectif 2.0)
- Tu veux automatiser via Home Assistant ? OK (objectif 2030)
- Tu veux comprendre et contribuer au code ? OK

---

## Nature du projet

| Question | Réponse |
|----------|---------|
| Commercial ? | Non — projet perso open source |
| Open source ? | Oui — MIT |
| Produit employeur ? | Non |
| App iOS ? | Vision 2030 |
| Compte obligatoire ? | Non — jamais |

---

## Où on en est (juillet 2026)

```
Génération intelligente + scoring        OK
Import Apple Music (streaming)           OK
App macOS Resonance                      OK
Repository local (SSOT)                  OK
Sync plan / apply / conflits             OK
YouTube Music expérimental               En cours
Multi-provider (architecture)            OK
UX sync wizard + providers               En cours (6.8)
```

État détaillé : [Etat-des-Phases](Etat-des-Phases.md)

---

## Où on va

Voir [Roadmap](../docs/ROADMAP.md) et [Backlog produit](../docs/product/BACKLOG.md).

**Resonance 2.0** = votre bibliothèque musicale personnelle, intelligente, versionnée, synchronisée partout, sous votre contrôle.

**2030** = l'infrastructure ouverte de référence pour posséder sa musique dans un monde multi-cloud.

---

## Références

- [RESONANCE_VISION_2030](../docs/product/RESONANCE_VISION_2030.md)
- [Architecture cible](../docs/architecture/TARGET_ARCHITECTURE.md)
- [ADR-013 — Multi-provider](../docs/architecture/ADR-013-multi-provider-platform-vision.md)
- [Phase 6 — Provider Platform](../docs/product/phase-6-provider-platform.md)
