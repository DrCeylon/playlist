# Principes produit

*Les règles du jeu — ce qu'on fait, ce qu'on ne fera jamais.*

→ Contexte : [Vision et objectif](Vision-et-Objectif)

## Philosophie

Projet **perso**, ouvert à **tout le monde**, construit avec une rigueur d'architecte solution et une envie de **reconstruction** — quelque chose de beau, d'utile, et partageable.

L'objectif : **générer des playlists Apple Music** à partir de **mots-clés** ou de **morceaux de référence** — manuellement aujourd'hui, de façon assistée demain.

## Les 6 commandements

### 1. Liberté musicale

- ✅ Chaque utilisateur définit **ses** goûts, **ses** exclusions, **sa** vibe
- ✅ Reggaeton, metal, jazz, K-pop — tout est légitime
- ❌ L'outil n'impose aucun style par défaut

*Les préférences du créateur (ex. Orlando sans reggaeton) sont des exemples, pas des règles produit.*

### 2. On ne supprime pas

- ❌ Pas de suppression de playlists
- ❌ Pas de retrait de morceaux dans une playlist (via cet outil)
- ✅ Création autorisée
- ✅ Mise à jour autorisée (ajout de morceaux)

### 3. Gratuit d'abord

Le workflow par défaut ne coûte rien :
- Python stdlib
- API iTunes Search publique
- AppleScript + app Musique macOS

MusicKit API (payant) reste **expérimental et optionnel**.

### 4. L'ordre des sections est sacré

Le parcours musical défini par l'utilisateur est respecté :
1. Ordre des `sections`
2. Ordre des `songs` dans chaque section

Pas de shuffle silencieux.

### 5. Traçabilité complète

Chaque exécution produit un rapport (CSV, HTML, TXT). On sait ce qui s'est passé, morceau par morceau.

### 6. Validation stricte des entrées

Données invalides = erreur claire en français. Pas de demi-mesure.

## Deux modes, une vision

| Mode | Input | Output |
|------|-------|--------|
| **Manuel** | JSON avec sections et morceaux | Playlist Apple Music |
| **Assisté** *(Phase 2)* | Mots-clés + morceaux de référence + contraintes | Playlist générée puis créée |

Les deux modes partagent les mêmes principes ci-dessus.

## Décisions produit documentées

| Décision | Raison |
|----------|--------|
| Ouvert à tout le monde | Projet perso partagé, pas un jardin secret |
| Pas de Spotify (pour l'instant) | Écosystème Apple Music ciblé |
| Pas de suppression | Éviter les accidents irréversibles |
| Sections avec emojis | Fun + lisibilité (optionnel pour l'utilisateur) |
| Rapport HTML cliquable | Réduire la friction d'ajout manuel |
| Phase 2 planning/generation | Cœur de la vision, pas un bonus |
| Exclusions via contraintes utilisateur | Liberté totale (ex. `excluded_terms`) |

## Hors périmètre (explicitement)

- Jugement sur les goûts musicaux
- Streaming vers d'autres plateformes (Spotify, YouTube Music…)
- Édition collaborative temps réel
- Recommandations IA opaques sans contrôle utilisateur
- Gestion de bibliothèque complète (suppression, notation, etc.)
- Application web
- Modèle commercial / abonnement

## Qualité et tests

- Tests unitaires sur scoring, loader, cache, planning, génération
- Pas de dépendance externe runtime
- Documentation wiki maintenue à jour

---

*Des principes clairs, zéro jugement musical. Tu veux du reggaeton à 6 h du matin ? C'est ton droit le plus strict.*
