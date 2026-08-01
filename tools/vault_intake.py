#!/usr/bin/env python3
"""Monta o esqueleto de uma edicao a partir das transcricoes do Vault.

  python3 tools/vault_intake.py --dry-run   # lista as 5 escolhidas
  python3 tools/vault_intake.py             # cria content/AAAA-MM-DD/
  python3 tools/vault_intake.py --force     # sobrescreve se ja existir

O Vault fica em WIR_VAULT (env) ou na constante VAULT abaixo. O script so faz a
mecanica: descobrir, extrair frontmatter e montar o esqueleto. A redacao dos
artigos e do editorial e feita por Claude, lendo as transcricoes apontadas.
"""
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

VAULT = Path(os.environ.get("WIR_VAULT", str(Path.home() / "ObsidianVault")))
RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"

def ler_frontmatter(caminho):
    """Le a primeira linha JSON da nota e devolve o dict fm (ou {})."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
        dados = json.loads(texto if texto.lstrip().startswith("{")
                           else texto.split("\n", 1)[0])
        return dados.get("fm", {}) if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def slugificar(titulo):
    t = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "item"

def descobrir_recentes(raiz_estudos, n=5):
    raiz_estudos = Path(raiz_estudos)
    achados = []
    for nota in raiz_estudos.glob("*/YouTube/*.md"):
        fm = ler_frontmatter(nota)
        data = fm.get("date", "")
        if not data or data == "0000-00-00":
            continue
        achados.append({"caminho": nota, "fm": fm, "data": data})
    achados.sort(key=lambda x: x["data"], reverse=True)
    return achados[:n]
