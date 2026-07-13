# Validation manuelle post-import (macOS)

Checklist pour valider le parcours réel décrit dans la consolidation PR #83.

## Prérequis

- macOS avec Music.app et Resonance build récent (branche `cursor/fix-post-import-library-registration-and-sync-link-ef21` ou `main` post-merge #83)
- Bridge Python opérationnel

## Parcours

1. [ ] Générer une playlist dans Resonance
2. [ ] Importer vers Apple Music
3. [ ] Si acquisition manuelle : terminer le workflow, puis retry d'un morceau depuis le rapport
4. [ ] Arriver au rapport final (`completed` ou `partial_success`)
5. [ ] **Sans redémarrage** : ouvrir l'écran Playlists → la playlist apparaît immédiatement
6. [ ] Fermer complètement Resonance
7. [ ] Relancer Resonance → playlist toujours visible dans Playlists
8. [ ] Ouvrir Sync, sélectionner la playlist
9. [ ] `previewPlan` réussit (pas d'erreur `remote_playlist_id ... requis`)
10. [ ] `applySync` réussit ou affiche un plan cohérent avec Music.app
11. [ ] Vérifier dans `data/playlists/managed_playlists.json` : `linked_remote_refs` non vide, `provider_playlist_id` renseigné

## Logs à surveiller

- Pas de lignes non-JSON sur stdout du bridge (`⏳ Morceau pas encore visible` doit être absent ou sur stderr via logging)
- Après import : appels `list_managed_playlists` côté Swift (refresh bibliothèque)

## Substitut automatisé (CI / Linux)

- `tests/test_register_generated_import.py`
- `tests/test_register_generated_import_consolidation.py` (redémarrage repository, multi-provider, retries)

La validation manuelle macOS reste obligatoire avant merge final si non effectuée par un agent cloud.
