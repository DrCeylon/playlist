# Release Plan — Resonance v1.0.0

Plan de release pour la première version publique de **Resonance** (produit) / **playlist-builder** (package Python).

## Objectif de la release

Publier une **v1.0.0** qui :

1. Délivre un workflow CLI + app macOS **stable et documenté**.
2. Respecte les principes **local-first**, **non destructif**, **provider-neutral**.
3. Inspire confiance aux nouveaux utilisateurs et contributeurs (licence, CI, sécurité, versioning cohérent).

## Périmètre v1.0.0

### Inclus

| Domaine | Contenu |
|---------|---------|
| CLI | `generate_playlist`, `check_catalog`, `create_playlist` |
| Moteur Python | Génération, scoring, import Apple Music, sync plan/apply (append_only) |
| App macOS | Resonance — génération, import, historique, Playlist Manager, diagnostics |
| Providers | Apple Music (production) ; YouTube Music (**lecture expérimentale**) |
| Docs | Wiki FR, ADRs, guides release, limitations connues |

### Exclu (post-v1.0)

- iOS / iPadOS shell
- Resonance Identity / Cloud Sync
- Sync mirror/reorder fiable côté provider
- Spotify gateway
- Wizard sync UX (Phase 6.8)
- Distribution App Store / notarisation automatisée

## Jalons

### J0 — Audit & fondations OSS (cette PR)

- [x] Audit complet (`RELEASE_AUDIT.md`)
- [x] Documents release (checklist, limitations, migration, matrix)
- [x] `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CHANGELOG.md`
- [x] CI Python (`python-ci.yml`)
- [x] Alignement version **1.0.0**
- [x] Synchronisation compteurs tests documentation

### J1 — Gel fonctionnel

- Figer `main` sauf correctifs bloquants
- Merger PRs fondations non conflictuelles (#75 observability si validée)
- Exécuter `scripts/check_all.sh` sur macOS réel

### J2 — Validation release candidate

```bash
# Linux / CI
python3.12 -m pytest -q

# macOS complet
./scripts/check_all.sh
cd apps/resonance && ./scripts/package-mac-app.sh
```

Checklist : `RELEASE_CHECKLIST.md`

### J3 — Tag & annonce

```bash
git tag -a v1.0.0 -m "Resonance v1.0.0 — first public release"
git push origin v1.0.0
```

- Créer GitHub Release avec notes depuis `CHANGELOG.md`
- Mettre à jour wiki `Etat-des-Phases.md` (statut « v1.0 publiée »)

### J4 — Post-release (v1.0.x)

| Priorité | Thème |
|----------|-------|
| P1 | Provider picker UI |
| P1 | CI gate sans filtre paths sur `main` |
| P2 | Wizard sync 6.8 |
| P2 | Merger observability (#75) si pas en J1 |
| P3 | Notarisation / distribution `.app` |

## Critères de sortie (Go / No-Go)

| Critère | Seuil |
|---------|-------|
| Tests Python CI | 100 % verts |
| Tests Swift CI (macOS) | 100 % verts |
| Licence | MIT présente |
| SECURITY.md | Présent |
| Version unique | 1.0.0 partout |
| Limitations documentées | `KNOWN_LIMITATIONS.md` à jour |
| Aucun secret dans git | `git ls-files` clean |
| Régression fonctionnelle | Aucune non documentée |

## Communication

| Audience | Canal |
|----------|-------|
| Utilisateurs FR | Wiki, README |
| Contributeurs | CONTRIBUTING.md, AGENTS.md |
| Sécurité | SECURITY.md → GitHub Advisories |

## Risques

| Risque | Mitigation |
|--------|------------|
| Divergence version | Source unique `playlist_builder.__version__` |
| CI Python contournée (path filters) | `python-ci.yml` + gate `main` |
| Attentes YouTube production | Marqué expérimental partout |
| Sync mirror attendue | Documenté dans KNOWN_LIMITATIONS |

## Références

- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md)
- [RELEASE_AUDIT.md](RELEASE_AUDIT.md)
