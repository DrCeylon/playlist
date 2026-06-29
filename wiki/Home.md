# 🎧 Apple Music Playlist Builder

*Bienvenue dans le wiki officiel — écrit par un papa qui code entre deux playlists.*

---

## En une phrase

**Apple Music Playlist Builder** transforme un fichier JSON en playlist Apple Music, section par section, morceau par morceau — sans prise de tête.

## Pourquoi ce projet existe

Entre deux journées d'architecture Guidewire (PolicyCenter le matin, ClaimCenter l'après-midi, et parfois les deux dans la même réunion), j'avais envie de construire quelque chose de **léger, fun et utile** : une playlist parfaite pour une pool party à Orlando, générée proprement, rejouable, documentée.

Comme en assurance non-vie : on part d'un **besoin réel**, on structure un **contrat** (le JSON), on **valide** les entrées, on **exécute** le process, et on produit un **rapport** clair. Sauf qu'ici, le sinistre c'est un morceau introuvable — et heureusement, personne n'appelle le service client.

## Ce que tu peux faire aujourd'hui

| Action | Outil | Coût |
|--------|-------|------|
| Vérifier les morceaux dans le catalogue Apple | `check_catalog.py` | Gratuit |
| Créer la playlist dans Apple Music (macOS) | `create_playlist.py` | Gratuit |
| Prévisualiser sans toucher à Music | `--dry-run` | Gratuit |
| MusicKit API (catalogue direct) | `--engine musickit` | **Expérimental** — licence Apple Developer payante |

## Workflow recommandé (3 étapes)

```
1. check_catalog.py     →  Rapport HTML avec liens Apple Music
2. Ajout manuel         →  Morceaux manquants dans ta bibliothèque
3. create_playlist.py   →  Playlist créée dans l'app Musique
```

## Playlist vedette

**🏝 Orlando Pool Party 2026** — 7 sections, 96 morceaux, montée progressive, bonne humeur maximale, **zéro reggaeton** (décision de papa approuvée par Arthur et Léonard… enfin, surtout par moi).

→ Voir [Playlist Orlando Pool Party](Playlist-Orlando-Pool-Party)

## Navigation du wiki

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

Une **app iOS** pour générer des playlists depuis l'iPhone — parce que construire quelque chose de solide pour mes garçons et pour moi, c'est aussi ça, la reconstruction.

→ [Feuille de route iOS](Feuille-de-route-iOS)

---

*« On ne supprime pas les playlists. On reconstruit. »* — principe fondateur du projet
