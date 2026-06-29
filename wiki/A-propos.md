# À propos

## Qui suis-je ?

Je suis **architecte solution**, spécialisé dans les logiciels d'assurances **non-vie** édités par **Guidewire** — principalement **PolicyCenter** (souscription, polices, produits) et **ClaimCenter** (sinistres, indemnisation, parcours client).

Mon métier, au fond : transformer des règles métier complexes en systèmes fiables, traçables et maintenables. Des contrats. Des validations. Des workflows. Des rapports. Du concret.

Ce projet playlist, c'est mon **terrain de jeu perso** — le même rigueur d'architecte, mais avec plus de soleil, plus de Kygo, et nettement moins de codes produits ISO.

## Ma vie en dehors du code

Je suis **papa de Arthur et Léonard** — deux garçons extraordinaires qui m'apprennent chaque jour le courage, la patience, et l'art de recommencer.

Je suis en **reconstruction** — pas au sens sinistre total (heureusement), mais au sens humain : rebâtir, réapprendre, avancer avec confiance. Ce dépôt GitHub en fait partie. L'app iOS en fera partie aussi.

Et oui, je suis **fun** — ou du moins j'essaie. Une playlist sans emoji 🏝, c'est comme une police sans numéro de contrat : techniquement possible, mais pourquoi ?

## Pourquoi ce projet ?

### Le besoin initial

Préparer une **pool party à Orlando** avec une bande-son montée progressive sur ~6 heures. Pas envie de cliquer 96 morceaux à la main dans Apple Music. Pas envie d'une playlist générée au hasard par un algorithme opaque.

### La réponse architecte

1. **Définir un contrat** → fichier JSON avec sections ordonnées
2. **Valider les données** → loader avec messages d'erreur clairs
3. **Vérifier le catalogue** → `check_catalog.py` (comme une pré-souscription)
4. **Exécuter** → `create_playlist.py` (comme une émission de police)
5. **Tracer** → rapports CSV, HTML et TXT (comme un dossier sinistre… mais en mieux)

### Ce que ce projet n'est pas

- Pas un Spotify Killer
- Pas un produit Guidewire (mes employeurs/clients n'ont rien à voir avec ce side project)
- Pas une app iOS… **encore**

## Ce que ce projet deviendra

| Phase | Objectif | Statut |
|-------|----------|--------|
| **Phase 1** | JSON → Apple Music via macOS | ✅ En production |
| **Phase 2** | Génération intelligente depuis des morceaux seeds | 🚧 En cours |
| **Phase 3** | App iOS native (SwiftUI + MusicKit) | 📋 Planifié |

## Mes principes dans ce code

- **Non destructif** : on crée et on met à jour, on ne supprime pas de playlists
- **Gratuit d'abord** : AppleScript + iTunes Search API avant toute licence payante
- **Ordre des sections sacré** : comme un parcours sinistre bien structuré, chaque étape a sa place
- **Tests** : parce qu'un architecte qui ne teste pas, c'est un sinistre en attente
- **Documentation** : tu la lis en ce moment même — mission accomplie

## Remerciements

À **Arthur et Léonard** — pour l'énergie, les pool parties imaginaires, et les « Papa, mets cette chanson ! » qui ont inspiré plus d'un morceau de la playlist Orlando.

À la **communauté Guidewire** — pour m'avoir appris à penser en contrats, règles et workflows. Ça sert même pour une playlist.

---

*Ce wiki est vivant. Comme moi. Comme le projet.*
