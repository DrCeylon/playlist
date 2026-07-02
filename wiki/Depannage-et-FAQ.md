# Dépannage et FAQ

*Quand ça coince — et comment décoincer.*

## FAQ générale

### Pourquoi Apple Music et pas Spotify ?

Écosystème familial Apple, synchronisation iCloud, téléchargement hors ligne pour la pool party. Choix personnel, pas une guerre des plateformes.

### Faut-il payer quelque chose ?

**Non** pour le workflow standard. MusicKit (optionnel) nécessite un compte Apple Developer payant — pas nécessaire pour l'usage courant.

### Puis-je utiliser ça sur Windows/Linux ?

- `check_catalog.py` → **oui** (rapports catalogue)
- `create_playlist.py` → **non** (nécessite macOS + app Musique)

### L'app iOS existe ?

Pas encore. Le shell **macOS Resonance** est disponible en développement (Phase 4.4+).

→ [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance) · [Feuille de route iOS](Feuille-de-route-iOS)

### L'app macOS Resonance, comment la lancer ?

Sur macOS avec Xcode / Swift installé :

```bash
cd apps/resonance
./scripts/build.sh
./scripts/package-mac-app.sh
open dist/ResonanceMac.app
```

Pour le développement rapide (icône Dock mais pas Finder) :

```bash
swift run ResonanceMac
```

L'app propose : navigation sidebar, Accueil, **Nouvelle Playlist** (saisie clavier AppKit), génération moteur Python, **import Apple Music** avec progression et acquisition manuelle, **Historique**, **Laboratoire**.

Variable utile si le repo n'est pas détecté automatiquement :

```bash
export RESONANCE_REPO_ROOT=/chemin/vers/playlist
```

### `generate_playlist.py` vs JSON manuel ?

- **JSON manuel** : tu choisis chaque morceau (`create_playlist.py`)
- **`generate_playlist.py`** : tu donnes seeds + mots-clés, le moteur assemble la playlist

→ [Phase 2 — Génération](Phase-2-Generation) · [Commandes CLI](Commandes-et-Options)

### C'est lié à Guidewire / mon employeur ?

Non. Projet personnel. Les analogies Guidewire dans ce wiki sont des métaphores, pas des affiliations.

---

## Problèmes courants — Catalogue

### ❌ Beaucoup de morceaux « non trouvés » dans `check_catalog.py`

**Causes possibles :**
- Store incorrect (`--country us` vs ta bibliothèque `ch`)
- Variante de titre différente sur Apple Music
- Artiste avec `feat.` non reconnu

**Solutions :**
```bash
# Essaie ton store
python3 check_catalog.py --country ch

# Re-vérifie sans cache
python3 check_catalog.py --no-cache
```

Vérifie manuellement dans le rapport HTML — le lien « chercher » aide.

### ⏳ Rate limit / lenteur catalogue

```bash
python3 check_catalog.py --sleep 1.5
```

Le cache accélère les re-runs :
```
cache/itunes_catalog.json
```

### HTTP 429 (trop de requêtes)

Le script retente automatiquement avec backoff. Si ça persiste, augmente `--sleep`.

---

## Problèmes courants — Création playlist

### ❌ Morceaux non trouvés dans `create_playlist.py`

**Cause n°1** : le morceau n'est **pas dans ta bibliothèque** Apple Music.

AppleScript ne peut pas ajouter un morceau catalogue non possédé. Solution :
1. Ouvre le rapport HTML catalogue
2. Ajoute le morceau à ta bibliothèque (bouton **+**)
3. Relance `create_playlist.py`

**Cause n°2** : variante artiste/titre différente entre JSON et bibliothèque.

Le script tente un match exact puis partiel (`contains`). Si ton JSON dit `Mark Ronson` mais la bibliothèque a `Mark Ronson feat. Bruno Mars`, ça peut échouer.

**Solution** : aligne le JSON sur le nom exact dans Apple Music.

### ⏭️ Tous les morceaux sont « déjà présents »

Normal si tu relances sans avoir modifié le JSON. Le script évite les doublons.

Pour forcer le ré-ajout :
```bash
python3 create_playlist.py --allow-duplicates
```

### `Cet outil nécessite macOS`

Tu es sur Linux/Windows. `create_playlist.py` nécessite macOS.

Alternative : utilise un Mac, ou attends l'app iOS.

### L'app Musique ne répond pas

1. Ouvre l'app **Musique** manuellement
2. Vérifie que la synchronisation bibliothèque est active
3. Relance le script

### Erreur AppleScript obscure

Vérifie :
- Caractères spéciaux dans les titres (guillemets, retours ligne)
- Nom de playlist avec caractères problématiques
- Permissions Automation (Préférences Système → Confidentialité → Automatisation)

---

## Problèmes JSON

### `Playlist invalide: Champ manquant 'title'`

Un morceau n'a pas de `title`. Corrige le JSON.

### `JSON invalide`

Valide ton JSON :
```bash
python3 -c "import json; json.load(open('playlists/ma_playlist.json'))"
```

### Encodage

Le fichier doit être **UTF-8**. Les emojis dans les noms de sections sont supportés.

---

## Problèmes MusicKit (expérimental)

### `Configuration MusicKit manquante`

```bash
export APPLE_MUSIC_DEVELOPER_TOKEN="..."
export APPLE_MUSIC_USER_TOKEN="..."
```

Si tu n'as pas ces tokens → **utilise AppleScript** (pas besoin de tokens).

### `MusicKit HTTP 401`

Token developer expiré ou invalide. Les JWT MusicKit ont une durée de vie limitée — régénère-le.

### `MusicKit HTTP 403`

User token invalide ou permissions insuffisantes.

---

## Problèmes Resonance macOS (Phase 4.8A)

### L'import affiche une erreur JSON / « data couldn't be read »

Corrigé en 4.8A : le bridge ignore les lignes stdout non-JSON. Si le message persiste :
1. Vérifie `RESONANCE_REPO_ROOT`
2. Relance avec `RESONANCE_ARCHITECT_MODE=1` pour le détail technique
3. Consulte [Phase 4.8A — Clôture](Phase-4-8A-Cloture)

### Music.app se fige en fin d'import

La livraison utilise désormais pacing + retry + confirmation. Laisse l'import terminer ; vérifie le rapport partiel si certains morceaux manquent.

### Autorisation Automatisation manquante

Réglages Système → Confidentialité et sécurité → **Automatisation** → autorise Resonance ou Python à contrôler **Musique**.

### Acquisition manuelle — comment chercher le morceau ?

Dans l'écran d'import : boutons **Copier recherche** / **Artiste** / **Morceau**, puis colle dans la recherche Music.app.

---

## Tests et debug

### Lancer les tests

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS uniquement
```

### Dry-run (zéro risque)

```bash
python3 create_playlist.py --dry-run
```

### Voir les rapports

```bash
ls -lt reports/
cat reports/report_*.txt
open reports/catalog_matches_*.html
```

---

## Je n'ai pas trouvé ma réponse

1. Vérifie le [Workflow complet](Workflow-complet)
2. Consulte [Commandes et options](Commandes-et-Options)
3. Ouvre une issue sur GitHub avec :
   - Commande exécutée
   - Message d'erreur complet
   - Extrait JSON (sans données perso)

---

*Un bon rapport de sinistre accélère le traitement. Un bon rapport de bug accélère le fix. Même logique, moins de paperasse.*
