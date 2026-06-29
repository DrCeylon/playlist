# Principes produit

*Les règles du jeu — ce qu'on fait, ce qu'on ne fera jamais.*

## Philosophie

Ce projet est né d'un besoin personnel, construit avec une rigueur professionnelle, et porté par une envie de **reconstruction** — quelque chose de beau, d'utile, et partageable.

Comme en architecture Guidewire : on définit les règles **avant** le code.

## Les 5 commandements

### 1. On ne supprime pas

- ❌ Pas de suppression de playlists
- ❌ Pas de retrait de morceaux dans une playlist (via cet outil)
- ✅ Création autorisée
- ✅ Mise à jour autorisée (ajout de morceaux)

*Un sinistre qu'on peut rouvrir, pas effacer.*

### 2. Gratuit d'abord

Le workflow par défaut ne coûte rien :
- Python stdlib
- API iTunes Search publique
- AppleScript + app Musique macOS

MusicKit API (payant) reste **expérimental et optionnel**.

### 3. L'ordre des sections est sacré

Le JSON définit un parcours. La playlist finale respecte :
1. L'ordre des `sections`
2. L'ordre des `songs` dans chaque section

Pas de shuffle silencieux. Pas de « l'algorithme a décidé ».

### 4. Traçabilité complète

Chaque exécution produit un rapport :
- Catalogue → CSV + HTML
- Création → TXT

Comme un dossier ClaimCenter : on sait ce qui s'est passé, morceau par morceau.

### 5. Validation stricte des entrées

JSON invalide = erreur claire en français. Pas de demi-mesure.

Comme une souscription PolicyCenter : les données entrantes sont validées avant traitement.

## Décisions produit documentées

| Décision | Raison |
|----------|--------|
| Pas de reggaeton dans Orlando | Choix éditorial du créateur (papa) |
| Pas de Spotify | Écosystème Apple Music familial |
| Pas de suppression | Éviter les accidents irréversibles |
| Sections avec emojis | Fun + lisibilité dans Apple Music |
| Rapport HTML cliquable | Réduire la friction d'ajout manuel |
| Batching AppleScript (25) | Performance sans sacrifier la fiabilité |
| Cache API catalogue | Éviter de re-interroger 96 morceaux |
| Phase 2 planning/generation | Préparer iOS sans casser Phase 1 |

## Hors périmètre (explicitement)

- Streaming vers d'autres plateformes (Spotify, YouTube Music…)
- Édition collaborative temps réel
- Recommandations IA opaques sans contrôle utilisateur
- Gestion de bibliothèque complète (suppression, notation, etc.)
- Application web

## Qualité et tests

- Tests unitaires sur scoring, loader, cache, planning
- Pas de dépendance externe runtime (reproductibilité)
- Code review via PR GitHub
- Documentation wiki (tu y es)

## Évolution des principes

Ces règles peuvent évoluer, mais jamais silencieusement :
- Toute modification de principe = mise à jour de ce wiki
- Toute fonction destructive = opt-in explicite avec confirmation

---

*Des principes clairs, un produit honnête. Comme une bonne implémentation Guidewire — sauf que là, le stakeholder c'est moi, et il veut de la bonne musique.*
