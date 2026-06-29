#!/bin/zsh
cd "$(dirname "$0")/.."
latest=$(ls -t reports/catalog_matches_*.html 2>/dev/null | head -n 1)
if [[ -z "$latest" ]]; then
  echo "Aucun rapport HTML trouvé. Lance d'abord: python3 check_catalog.py"
  exit 1
fi
open "$latest"
