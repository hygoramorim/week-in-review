#!/usr/bin/env python3
"""Envia um aviso pelo bot do Kairos no Telegram.

  python3 tools/notificar_telegram.py "mensagem aqui"

Le TELEGRAM_BOT_TOKEN e OWNER_TELEGRAM_ID do .env do Kairos
(~/Projects/kairos/agent/.env). Nao guarda segredo neste repo.
Usa so a stdlib. Suporta Markdown do Telegram.
"""
import os
import re
import sys
import json
import urllib.request
from pathlib import Path

ENV = Path.home() / "Projects" / "kairos" / "agent" / ".env"


def _ler_env(chave):
    if not ENV.exists():
        return None
    txt = ENV.read_text(encoding="utf-8")
    m = re.search(rf"^{chave}=(.*)$", txt, re.M)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def enviar(mensagem, chat_id=None):
    token = _ler_env("TELEGRAM_BOT_TOKEN")
    chat = chat_id or _ler_env("OWNER_TELEGRAM_ID")
    if not token or not chat:
        raise RuntimeError("TELEGRAM_BOT_TOKEN ou OWNER_TELEGRAM_ID ausente no .env do Kairos")
    dados = json.dumps({
        "chat_id": chat,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=dados, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        resp = json.load(r)
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram recusou: {resp}")
    return resp


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('uso: notificar_telegram.py "mensagem"')
    enviar(sys.argv[1])
    print("aviso enviado no Telegram.")
