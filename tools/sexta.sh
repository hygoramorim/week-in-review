#!/usr/bin/env bash
# tools/sexta.sh - dispara o pipeline semanal via Claude Code headless.
# Cron (Mac Mini):  30 15 * * 5  "/CAMINHO/Week Review/week-in-review/tools/sexta.sh"
#
#   sexta.sh            roda o pipeline completo (ate o publicar.sh)
#   sexta.sh --ensaio   roda tudo menos publicar (publicar.sh fica FORA do allowlist)
set -euo pipefail
cd "$(dirname "$0")/.."

LOG="$HOME/Library/Logs/week-in-review-sexta.log"
echo "===== $(date) pipeline iniciado =====" >> "$LOG"

PROMPT="$(cat tools/pipeline.md)"

# Allowlist estrita: so os comandos que o pipeline realmente usa rodam sem prompt.
# Em vez de bypassPermissions (que libera tudo), listamos o conjunto minimo.
# git: pull/add/commit/push. python3: os scripts do projeto. notebooklm: a ponte
# do podcast. Read/Write/Edit/Glob/Grep: ler transcricoes e escrever artigos.
# Task: subagentes para ler transcricoes grandes. O publicar.sh so entra no modo
# normal, nunca no ensaio.
ALLOW="Bash(git:*) Bash(python3:*) Bash(notebooklm:*) Read Write Edit Glob Grep Task"
if [[ "${1:-}" == "--ensaio" ]]; then
  PROMPT="$PROMPT

MODO ENSAIO: execute os passos 1 a 6 mas NAO rode o passo 7 (publicar.sh). So reporte o que publicaria."
  # No ensaio, publicar.sh nem entra no allowlist: publicar fica impossivel,
  # nao depende do modelo obedecer a instrucao textual acima.
else
  ALLOW="$ALLOW Bash(./publicar.sh) Bash(bash publicar.sh:*)"
fi

# Vault fica fora do diretorio do projeto; --add-dir libera so ele (escopo minimo).
VAULT_DIR="${WIR_VAULT:-$HOME/ObsidianVault}"

claude -p "$PROMPT" \
  --permission-mode acceptEdits \
  --allowedTools $ALLOW \
  --add-dir "$VAULT_DIR" >> "$LOG" 2>&1
echo "===== $(date) pipeline terminado =====" >> "$LOG"
