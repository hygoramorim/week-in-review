#!/usr/bin/env bash
# tools/sexta.sh - dispara o pipeline semanal via Claude Code headless.
# Cron (Mac Mini):  30 15 * * 5  /CAMINHO/week-in-review/tools/sexta.sh
set -euo pipefail
cd "$(dirname "$0")/.."

LOG="$HOME/Library/Logs/week-in-review-sexta.log"
echo "===== $(date) pipeline iniciado =====" >> "$LOG"

# --ensaio: roda tudo menos o publicar (para testar sem publicar)
PROMPT="$(cat tools/pipeline.md)"
if [[ "${1:-}" == "--ensaio" ]]; then
  PROMPT="$PROMPT

MODO ENSAIO: execute os passos 1 a 6 mas NAO rode o passo 7 (publicar.sh). So reporte o que publicaria."
fi

claude -p "$PROMPT" --permission-mode acceptEdits >> "$LOG" 2>&1
echo "===== $(date) pipeline terminado =====" >> "$LOG"
