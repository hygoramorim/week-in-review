#!/usr/bin/env bash
# Publica a edição que está em index.html:
# arquiva em editions/, regenera arquivo.html e manda pro GitHub Pages.
#
#   ./publicar.sh                 usa a data da barra superior do index.html
#   ./publicar.sh 2026-08-07      força a data da edição
set -euo pipefail
cd "$(dirname "$0")"

DATA="${1:-$(python3 tools/arquivo.py data)}"

python3 tools/arquivo.py arquivar "$DATA"

git add -A
if git diff --cached --quiet; then
  echo "nada mudou — nenhuma edição publicada."
  exit 0
fi

git commit -q -m "Publish Week In Review $DATA"
git push -q

echo
echo "no ar (leva ~1 min pra propagar):"
echo "  https://hygoramorim.github.io/week-in-review/"
echo "  https://hygoramorim.github.io/week-in-review/editions/$DATA.html"
