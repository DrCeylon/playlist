# Phase 6.8 — Product Experience

## Objectif

Transformer Resonance en produit macOS agréable à utiliser, en s'appuyant sur le backend mature des phases 6.1–6.7.

## Audit UX (synthèse)

### Frictions identifiées

| Zone | Problème | Action 6.8 |
|------|----------|------------|
| Navigation | Laboratoire dans la sidebar principale | Déplacé vers Paramètres > Avancé |
| État | 3 instances `PlaylistsViewModel` isolées | `PlaylistLibraryStore` partagé |
| Sync | Pull one-shot, pas de plan/conflits | Wizard plan → résolution → apply |
| Providers | Lecture seule | Connecter / déconnecter |
| Copy | Jargon technique visible | `ProductDisplay` — libellés humains |
| Conflits | Liste brute non actionnable | Picker de résolution par conflit |
| Dashboard | Carte architecture interne | Carte « À traiter » + actions |

### Information architecture

| Écran | Justification |
|-------|---------------|
| **Accueil** | Point d'entrée : récent, alertes, raccourcis |
| **Créer** | Workflow génération → preview → import (inchangé) |
| **Playlists** | SSOT local : liste, détail, morceaux, lien sync |
| **Synchronisation** | Wizard guidé : prévisualiser, résoudre, appliquer |
| **Services musicaux** | Connexion comptes, état, capacités humaines |
| **Historique** | Sessions génération/import (inchangé) |
| **Paramètres** | Thème, bibliothèque, laboratoire (avancé) |

### Vues retirées de la navigation principale

- **Laboratoire** (`DiagnosticsView`) — conservé, accessible via Paramètres

## Implémentation

### Nouveaux modules Swift

- `ProductDisplay` — libellés utilisateur
- `PlaylistLibraryStore` — état playlists partagé
- `SyncViewModel` — orchestration UI sync (délègue au service)
- `ProductComponents` — `ProductSectionCard`, `StatusChip`, `ProductEmptyState`

### Bridge consommé

- `plan_sync`, `resolve_sync_conflicts`, `apply_sync`
- `provider_auth_status`, `provider_connect`, `provider_disconnect`

### Principes

- HIG Apple, `NavigationStack`, `@Observable` / `ObservableObject`
- Aucune logique métier dans les ViewModels — délégation aux services bridge
- Repository local reste SSOT

## Références

- Phase 6.7 — conflict resolution
- ADR-016 — playlist sync model
