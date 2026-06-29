# MusicKit expérimental

*Présent dans le code. Absent du workflow quotidien. Volontairement.*

## Statut : non utilisé pour l'instant

MusicKit nécessite un **compte Apple Developer payant** (99 USD/an) pour générer les tokens JWT.

**Décision produit** : le workflow gratuit AppleScript + iTunes Search API reste le chemin principal. MusicKit est conservé comme prototype pour la future app iOS.

## Quand l'envisager

- Tu souscris au programme Apple Developer
- Tu veux tester la création directe depuis le catalogue (sans ajout manuel bibliothèque)
- Tu prépares l'app iOS et veux valider la logique API

## Quand l'ignorer

- Tu veux juste créer ta playlist Orlando → **utilise AppleScript**
- Tu ne veux pas payer 99 USD/an → **utilise AppleScript**
- Tu es sur macOS avec l'app Musique → **utilise AppleScript**

## Activation

```bash
export APPLE_MUSIC_DEVELOPER_TOKEN="eyJ..."
export APPLE_MUSIC_USER_TOKEN="..."

python3 create_playlist.py --engine musickit --storefront us
```

### Options MusicKit

| Option | Description |
|--------|-------------|
| `--engine musickit` | Active le moteur API |
| `--storefront us` | Store Apple Music (`us`, `ch`, `fr`…) |
| `--cache cache/musickit_catalog.json` | Cache des IDs catalogue |
| `--no-cache` | Désactive le cache |
| `--allow-duplicates` | N'ignore pas les doublons existants |

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `APPLE_MUSIC_DEVELOPER_TOKEN` | JWT signé avec clé privée MusicKit (Apple Developer Portal) |
| `APPLE_MUSIC_USER_TOKEN` | Token utilisateur autorisant l'accès bibliothèque |

### Obtenir les tokens (résumé)

1. Compte [Apple Developer Program](https://developer.apple.com/programs/) (payant)
2. Créer une clé MusicKit dans le portail développeur
3. Générer un JWT developer token (durée limitée, à renouveler)
4. Obtenir un user token via le flux OAuth MusicKit

→ Documentation Apple : [MusicKit API](https://developer.apple.com/documentation/applemusicapi)

## Ce que fait le client MusicKit

```
Pour chaque morceau :
  └─ Recherche catalogue /v1/catalog/{storefront}/search

Création ou mise à jour playlist :
  └─ POST /v1/me/library/playlists
  └─ POST /v1/me/library/playlists/{id}/tracks
```

### Optimisations implémentées

- Cache JSON des IDs catalogue
- Déduplication (skip morceaux déjà en playlist)
- Retry sur HTTP 429
- Scoring unifié avec iTunes Search
- Ajout par lots de 100 morceaux

## Principes de sécurité

| Action | Supportée |
|--------|-----------|
| Créer une playlist | ✅ |
| Mettre à jour (ajouter des morceaux) | ✅ |
| Supprimer une playlist | ❌ Volontairement exclu |
| Retirer des morceaux d'une playlist | ❌ Volontairement exclu |

*Philosophie non destructive — on construit, on n'efface pas.*

## Différences AppleScript vs MusicKit

| Critère | AppleScript | MusicKit |
|---------|-------------|----------|
| Coût | Gratuit | 99 USD/an |
| Plateforme | macOS uniquement | macOS, Linux, cloud |
| Pré-requis bibliothèque | Morceaux déjà en bibliothèque | Accès catalogue direct |
| Complexité setup | Aucune | Tokens JWT |
| Statut projet | **Production** | **Expérimental** |

## Lien iOS

Sur iPhone, le framework **MusicKit natif** remplacera ce client Python REST. L'authentification sera gérée par iOS, pas par des JWT manuels.

→ [Feuille de route iOS](Feuille-de-route-iOS)

---

*MusicKit, c'est l'avenir. AppleScript, c'est le présent. Et le présent, c'est ce qui fait danser Arthur et Léonard ce weekend.*
