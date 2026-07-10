# Release Checklist — v1.0.0

Cocher avant de taguer `v1.0.0` sur `main`.

## A. Gouvernance & légal

- [ ] `LICENSE` (MIT) présent à la racine
- [ ] `SECURITY.md` présent — procédure de signalement vulnérabilité
- [ ] `CONTRIBUTING.md` à jour
- [ ] `CHANGELOG.md` entrée `1.0.0` complète
- [ ] `docs/GOVERNANCE.md` cohérent avec la réalité du projet
- [ ] Aucun secret dans l'index git (`git ls-files reports/ cache/ data/` vide)

## B. Versioning

- [ ] `playlist_builder/__init__.py` → `__version__ = "1.0.0"`
- [ ] `pyproject.toml` → `version = "1.0.0"`
- [ ] `apps/resonance/ResonanceMac/Resources/Info.plist` → `CFBundleShortVersionString` = `1.0.0`
- [ ] Bridge `diagnostics` renvoie `engine_version` = `1.0.0`
- [ ] Tag Git `v1.0.0` créé sur le commit de release

## C. CI / qualité

- [ ] `.github/workflows/python-ci.yml` vert sur la branche de release
- [ ] `.github/workflows/resonance-macos.yml` vert (macOS)
- [ ] `python3.12 -m pytest -q` → tous verts localement
- [ ] `scripts/check_environment.py` passe
- [ ] Sur macOS : `./scripts/check_all.sh` passe
- [ ] Aucune régression fonctionnelle non documentée

## D. Documentation

- [ ] `README.md` — compteur tests à jour, lien vers limitations
- [ ] `wiki/Etat-des-Phases.md` — statut v1.0
- [ ] `wiki/Home.md` — compteur tests à jour
- [ ] `docs/KNOWN_LIMITATIONS.md` — reflète l'état réel
- [ ] `docs/MIGRATION_GUIDE.md` — valide pour utilisateurs existants
- [ ] `docs/COMPATIBILITY_MATRIX.md` — plateformes et providers
- [ ] `docs/TECHNICAL_DEBT.md` — métriques à jour

## E. Produit & UX

- [ ] Fonctionnalités expérimentales clairement étiquetées (YouTube, MusicKit)
- [ ] Libellés UI sans « preview » trompeur (Settings / Home)
- [ ] Workflow CLI documenté de bout en bout
- [ ] App `.app` construisible (`package-mac-app.sh`)

## F. Packaging

- [ ] `pip install -e ".[dev]"` fonctionne (Python 3.12+)
- [ ] Entry points CLI : `playlist-check-catalog`, `playlist-create`, `playlist-generate`
- [ ] Extra `[youtube]` documenté comme optionnel et expérimental

## G. GitHub Release

- [ ] Notes de release rédigées (depuis CHANGELOG)
- [ ] Assets optionnels : archive source du tag
- [ ] Issues milestone v1.0 fermées ou reportées avec label

## H. Post-release immédiat

- [ ] Annoncer limitations connues dans la release note
- [ ] Surveiller issues « first run » première semaine
- [ ] Planifier v1.0.1 si correctifs critiques

## Commandes de validation rapide

```bash
# Minimum (toute plateforme avec Python 3.12)
python3.12 -m pytest -q
python scripts/check_environment.py

# Complet (macOS)
./scripts/check_all.sh

# Packaging app
cd apps/resonance && ./scripts/package-mac-app.sh

# Audit git
git ls-files reports/ cache/ data/ .pytest_cache/
```
