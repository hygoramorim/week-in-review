#!/usr/bin/env bash
# Constrói o site a partir de content/ e publica no GitHub Pages.
#
#   ./publicar.sh          build + commit + push
#   ./publicar.sh --check   só valida content/, não escreve nem publica
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--check" ]]; then
  python3 tools/build.py --check
  exit 0
fi

python3 tools/build.py

ATUAL=$(ls content 2>/dev/null | sort -r | head -1)

git add -A
if git diff --cached --quiet; then
  echo "nada mudou — nada publicado."
  exit 0
fi

git commit -q -m "Publish Week In Review $ATUAL"
git push -q

echo
echo "no ar (leva ~1 min pra propagar):"
echo "  https://hygoramorim.github.io/week-in-review/"
echo "  https://hygoramorim.github.io/week-in-review/editions/$ATUAL/"
echo
echo "resumo pro NotebookLM:  podcast/$ATUAL-brief.md"
