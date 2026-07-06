# Cloud Agent Setup — Lancer un Cursor Cloud Agent sur Resonance

Guide opérationnel pour faire travailler un Cursor Cloud Agent plusieurs heures de
façon autonome, sans casser la vision architecture. À lire par la personne qui
lance l'agent (Nicolas / ChatGPT en préparation).

---

## 1. Prérequis

- Accès au repo `playlist` sur GitHub et à Cursor Cloud.
- Environnement du VM déjà provisionné par le script de mise à jour
  (virtualenv `.venv`, dépendances dev). Voir la section
  « Cursor Cloud specific instructions » d'`AGENTS.md`.
- Python 3.12+ (le VM l'a par défaut). `tests/conftest.py` échoue si < 3.12.
- Aucun secret requis pour le workflow par défaut : la découverte catalogue utilise
  l'API iTunes **publique**. `create_playlist.py` (AppleScript) et l'app Swift sont
  **macOS-only** et hors du VM Linux.

## 2. Vérifier une branche propre

Avant de lancer l'agent :

```bash
git status          # arbre de travail propre attendu
git branch --show-current
```

- Partir d'une base à jour (`main` ou la branche de phase concernée).
- S'assurer qu'aucun changement non voulu ne traîne dans l'arbre de travail.

## 3. Committer les changements locaux

- Committer ou remiser (`git stash`) tout travail local en cours **avant** de lancer
  l'agent, pour que l'agent démarre d'un état connu.
- L'agent créera sa propre branche `cursor/<descriptif>-<suffixe>` et fera des
  **small commits**.

## 4. Lancer depuis Cursor Cloud

1. Ouvrir Cursor Cloud et sélectionner le repo `playlist`.
2. Choisir la branche de base (ex. `main` ou la branche de phase courante).
3. Coller le prompt (section 5) et lancer l'agent.

## 5. Prompt recommandé

Structure d'un bon prompt (cadré, borné, vérifiable) :

```text
Contexte : lis AGENTS.md et docs/engineering/CURRENT_PHASE.md avant tout.
Tâche : <décrire précisément l'objectif, ex. item P0 du NEXT_BACKLOG>.
Contraintes :
- respecter les invariants d'architecture (Core provider-neutral, bridge neutre) ;
- ne pas toucher à l'UX sans demande ;
- pas de Spotify/YouTube sans ADR ;
- small commits ;
- lancer `python3.12 -m pytest -q` et rapporter l'état réel.
Périmètre : <ce qui est inclus>.
Hors scope : <ce qui est exclu>.
Définition de terminé : voir RESONANCE_ENGINEERING_HANDBOOK.md §6.
Rapport final attendu : fichiers touchés, résumé, validation, état git, prochaine action.
```

Toujours pointer l'agent vers un **item précis** du backlog plutôt que vers un
objectif vague.

## 6. Critères d'arrêt

L'agent doit s'arrêter quand :

- la tâche cadrée est terminée selon la Definition of Done (handbook §6) ; **ou**
- il est **bloqué** (dépendance manquante, décision produit/ADR nécessaire, secret
  absent) — dans ce cas il s'arrête et le signale clairement au lieu d'élargir le périmètre ; **ou**
- poursuivre exigerait un **changement hors scope** (nouvelle phase, refonte UX,
  nouveau provider sans ADR).

## 7. Limites

- **Sur le VM Linux** : impossible de compiler/exécuter l'app Swift `apps/resonance/`
  et d'exécuter `create_playlist.py` (macOS + Apple Music requis). Leur logique est
  couverte par les tests Python via le bridge.
- **Aucun linter** configuré : `pytest` est la seule barrière qualité automatique.
- L'agent **n'a pas** autorité pour décider de la stratégie produit, changer l'UX,
  ou introduire un provider sans ADR accepté.
- La suite de tests dure ~2 min : c'est normal, ne pas la contourner.

## 8. Quoi vérifier au retour

- **Rapport final** présent et structuré (fichiers, résumé, validation, git,
  prochaine action).
- **Périmètre** respecté ; aucun changement UX / provider non demandé.
- **Invariants** tenus : `git diff` ne montre pas de provider-specific dans le Core
  ni d'AppleScript dans le bridge.
- **Tests** : `python3.12 -m pytest -q` vert (relancer localement au besoin).
- **PR** : branche `cursor/*`, commits petits et lisibles, docs/ADR à jour si des
  contrats ont bougé. Parcourir `docs/engineering/REVIEW_CHECKLIST.md` avant de merger.
- **Dette technique** : stable ou en baisse ; toute dette introduite est signalée.
