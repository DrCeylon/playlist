# Phase 5.3 — Benchmarks performance

Scripts de collecte baseline pour la Phase 5.3.1.

## Prérequis

- macOS pour les scénarios import (S1–S5) et génération réelle
- Python 3.12 + dépendances du projet
- `RESONANCE_PERF_TRACE=1` pour activer les traces `resonance-perf:`

## Scénarios

| ID | Description | Morceaux | Cache |
|----|-------------|----------|-------|
| S0 | Bridge cold start (`list_providers`) | — | — |
| S1 | Import baseline | 10 | froid |
| S2 | Réimport même playlist | 10 | chaud |
| S3 | Usage réel | 30 | froid |
| S4 | Stress | 80 | froid |
| S5 | Acquisition manuelle | 1 | froid |
| G20 | Génération | 20 | — |
| G50 | Génération | 50 | — |

Exécuter **3 fois** chaque scénario sur la même machine ; reporter médiane et p95.

## Commandes

```bash
# Depuis la racine du dépôt
export RESONANCE_PERF_TRACE=1

# Cold start bridge (toute plateforme)
python3.12 scripts/perf/benchmark_phase_5_3.py --scenarios S0 --runs 3

# Baseline complète (macOS — import via app ou extension fixtures)
python3.12 scripts/perf/benchmark_phase_5_3.py --all --runs 3 --machine "MacBook Pro M3"

# Validation standard
cd apps/resonance && swift build && swift test && ./scripts/build.sh
cd ../.. && source .venv/bin/activate && python3.12 -m pytest -q
```

## Sorties

- `reports/perf/perf_trace_*.json` — spans bruts
- `reports/perf/perf_trace_*.csv` — export tabulaire
- `reports/perf/phase-5-3-baseline.md` — rapport baseline (top 3 postes)

Les rapports sont générés localement (`reports/` est gitignoré).

## Format trace `resonance-perf:`

Chaque ligne stderr :

```json
resonance-perf: {"phase":"import","operation":"resolve_batch","duration_ms":842,"batch_index":2,"cache_hit":false}
```

Champs : `phase`, `operation`, `duration_ms`, optionnellement `batch_index`, `track_index`, `cache_hit`, `metadata`.
