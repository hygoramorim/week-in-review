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
    """Le o frontmatter da nota (YAML entre --- --- ou primeira linha JSON) e devolve o dict."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
    except OSError:
        return {}
    t = texto.lstrip("﻿")
    primeira = t.split("\n", 1)[0].strip()
    if primeira.startswith("{"):
        try:
            d = json.loads(primeira)
            return d.get("fm", d) if isinstance(d, dict) else {}
        except json.JSONDecodeError:
            return {}
    if t.startswith("---"):
        fim = t.find("\n---", 3)
        if fim != -1:
            return _yaml_frontmatter(t[3:fim].strip("\n"))
    return {}

def _yaml_frontmatter(bloco):
    """Parser minimo de frontmatter YAML: chave: valor e chave: [a, b]. Sem dependencias."""
    fm = {}
    for linha in bloco.split("\n"):
        if not linha.strip() or linha.lstrip().startswith("#") or ":" not in linha:
            continue
        chave, _, valor = linha.partition(":")
        chave, valor = chave.strip(), valor.strip()
        if valor.startswith("[") and valor.endswith("]"):
            itens = [x.strip().strip('"').strip("'") for x in valor[1:-1].split(",")]
            fm[chave] = [x for x in itens if x]
        else:
            fm[chave] = valor.strip('"').strip("'")
    return fm

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
