# Phase 5.3 — Rapport baseline performance

*Template — sera rempli par `scripts/perf/benchmark_phase_5_3.py` ou import manuel depuis l'app.*

## Résumé des scénarios

| Scénario | Morceaux | Cache | Total (ms) | Top 1 | Top 2 | Top 3 |
|----------|----------|-------|------------|-------|-------|-------|
| S0 — cold start | — | — | _à mesurer_ | bridge.python_cold_start | bridge.context_build | bridge.command_total |
| S1 — import | 10 | froid | _à mesurer_ | — | — | — |
| S2 — import | 10 | chaud | _à mesurer_ | — | — | — |
| S3 — import | 30 | froid | _à mesurer_ | — | — | — |
| S4 — import | 80 | froid | _à mesurer_ | — | — | — |
| G20 — génération | 20 | — | _à mesurer_ | — | — | — |
| G50 — génération | 50 | — | _à mesurer_ | — | — | — |

## Top 3 postes de lenteur (agrégé)

_À compléter après 3 exécutions médianes par scénario sur macOS._

1. **—**
2. **—**
3. **—**

## Seuils d'alerte indicatifs

| Métrique | Seuil |
|----------|-------|
| `bridge.python_cold_start` | > 1500 ms |
| `import.resolve_total` / track | > 800 ms |
| `import.delivery_total` / track | > 500 ms |
| `import.import_total` (30 morceaux) | > 60 s |
| `generate.generate_total` (20 morceaux) | > 15 s |

## Analyse Apple Music (développeur)

Voir `wiki/Phase-5-3-Performance.md` section « Limitation compte développeur Apple ».

**Certain** : production = AppleScript + iTunes Search (pas de token MusicKit requis).

**À vérifier** : part relative cold start bridge vs osascript vs iTunes HTTP.

## Prochaines étapes (5.3.2)

Quick wins uniquement si démontrés par ce baseline.
