#!/usr/bin/env python3
"""Verifica se a sessao do NotebookLM ainda esta valida e, se nao estiver,
avisa no Telegram para relogar ANTES da sexta.

  python3 tools/checar_auth.py

Roda `notebooklm list`. Se falhar (sessao expirada, o caso comum), dispara um
aviso no Telegram com o comando de relogin pronto. Se estiver ok, so imprime e
sai 0, sem incomodar. A ideia e rodar na quinta pelo cron, com folga para o
Hygor relogar antes do pipeline de sexta 15h30.

So stdlib. Reaproveita tools/notificar_telegram.py para o envio.
"""
import subprocess
import sys
from pathlib import Path

# importa a funcao de envio do modulo irmao
sys.path.insert(0, str(Path(__file__).resolve().parent))
from notificar_telegram import enviar  # noqa: E402

CONTA = "hygor@ozprodutora.com.br"

AVISO = f"""*Login do NotebookLM expirou* 🔑

A sessao do NotebookLM caiu. Se nao relogar, o pipeline de sexta publica a \
newsletter normal mas o *podcast da semana nao vai gerar*.

Pra destravar (no Mac Mini):
```
cd ~/projetos/notebooklm-skill
.venv/bin/python -m notebooklm login --browser-cookies chrome --account {CONTA}
```
Depois confirme com `notebooklm list`. Leva 1 minuto."""


def sessao_valida():
    """True se `notebooklm list` roda sem erro de auth."""
    try:
        r = subprocess.run(
            ["notebooklm", "list"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"nao consegui rodar notebooklm list: {e}"
    saida = (r.stdout + r.stderr).lower()
    # o CLI as vezes sai 0 mesmo com a auth expirada; olhar o texto e o que vale.
    if "authentication expired" in saida or "re-authenticate" in saida:
        return False, "sessao expirada"
    if r.returncode != 0:
        return False, f"notebooklm list falhou (rc={r.returncode})"
    return True, "sessao valida"


def main():
    ok, motivo = sessao_valida()
    if ok:
        print(f"NotebookLM: {motivo}, nada a fazer.")
        return 0
    print(f"NotebookLM: {motivo}. Avisando no Telegram.")
    try:
        enviar(AVISO)
        print("aviso enviado no Telegram.")
    except Exception as e:  # nao deixa o cron quebrar por causa do aviso
        print(f"falha ao avisar no Telegram: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
