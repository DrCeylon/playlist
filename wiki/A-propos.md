# À propos

## Qui suis-je ?

Je suis **architecte solution**, spécialisé dans les logiciels d'assurances **non-vie** édités par **Guidewire** — principalement **PolicyCenter** (souscription, polices, produits) et **ClaimCenter** (sinistres, indemnisation, parcours client).

Mon métier, au fond : transformer des règles métier complexes en systèmes fiables, traçables et maintenables. Des contrats. Des validations. Des workflows. Des rapports. Du concret.

Ce projet playlist, c'est mon **terrain de jeu perso** — la même rigueur d'architecte, mais avec plus de soleil, plus de Kygo, et nettement moins de codes produits ISO.

## Ma vie en dehors du code

Je suis **papa de Arthur et Léonard** — deux garçons extraordinaires qui m'apprennent chaque jour le courage, la patience, et l'art de recommencer.

Je suis en **reconstruction** — pas au sens sinistre total (heureusement), mais au sens humain : rebâtir, réapprendre, avancer avec confiance. Ce dépôt GitHub en fait partie. L'app iOS en fera partie aussi.

Et oui, je suis **fun** — ou du moins j'essaie.

## L'objectif de l'application

**Générer des playlists Apple Music à partir de mots-clés ou de morceaux de référence.**

→ Détails : [Vision et objectif](Vision-et-Objectif)

### Pour qui ?

**Tout le monde.** C'est un projet perso, pas un produit commercial. Mais il est ouvert, documenté, et conçu pour que n'importe qui puisse l'utiliser, le forker, l'adapter.

### Deux modes, un seul outil

| Mode | Description |
|------|-------------|
| **Manuel** | Tu définis chaque morceau dans un JSON (disponible aujourd'hui) |
| **Assisté** | Tu donnes des seeds + mots-clés, l'app génère (Phase 2, en cours) |

### Mes préférences ≠ les règles du produit

La playlist Orlando n'a pas de reggaeton — c'est **mon** choix pour **ma** pool party. Toi, tu écoutes ce que tu veux. L'outil ne juge pas, n'impose pas, n'exclut rien par défaut. *(Les exclusions, c'est toi qui les définis dans tes contraintes.)*

## Pourquoi ce projet ?

### Le besoin initial

Préparer une **pool party à Orlando** sans cliquer 96 morceaux à la main. Puis réaliser que d'autres ont le même problème — pool party ou pas.

### La réponse architecte

1. **Définir un contrat** → JSON, seeds, ou mots-clés
2. **Valider les entrées** → loader avec messages clairs
3. **Vérifier le catalogue** → `check_catalog.py`
4. **Générer ou exécuter** → Phase 2 ou `create_playlist.py`
5. **Tracer** → rapports CSV, HTML et TXT

### Ce que ce projet n'est pas

- Pas un Spotify Killer
- Pas un produit Guidewire (side project sans lien employeur)
- Pas une app iOS… **encore**
- Pas un juge de goûts musicaux

## Roadmap

| Phase | Objectif | Statut |
|-------|----------|--------|
| **Phase 1** | JSON manuel → Apple Music | ✅ En production |
| **Phase 2** | Génération par mots-clés et morceaux de référence | 🚧 Cœur de la vision |
| **Phase 3** | App iOS pour tout le monde | 📋 Planifié |

## Mes principes dans ce code

- **Liberté musicale** : tu écoutes ce que tu veux
- **Non destructif** : on crée, on ne supprime pas
- **Gratuit d'abord** : AppleScript + iTunes Search API
- **Ordre des sections sacré** : ton parcours, ton rythme
- **Ouvert à tous** : projet perso, usage universel

## Remerciements

À **Arthur et Léonard** — pour l'énergie, les pool parties imaginaires, et les « Papa, mets cette chanson ! »

À la **communauté Guidewire** — pour m'avoir appris à penser en contrats, règles et workflows.

À **toi** — si tu utilises, forkes, ou améliores ce projet.

---

*Ce wiki est vivant. Comme le projet. Comme moi.*
