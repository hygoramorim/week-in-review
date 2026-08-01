#!/usr/bin/env python3
"""Ponte entre o brief da edicao e o NotebookLM (gera e baixa o mp3).

  python3 tools/notebooklm_bridge.py AAAA-MM-DD            # gera + baixa + grava
  python3 tools/notebooklm_bridge.py AAAA-MM-DD --dry-run  # so resolve o notebook

Usa a CLI notebooklm-py (ja autenticada em ~/.notebooklm). Notebook fixo, fontes
acumulam; o audio e limitado a fonte da semana via -s <source_id>.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"
AUDIO = RAIZ / "podcast" / "audio"
NOTEBOOK = "Week In Review"

def _run(args, capture=True):
    r = subprocess.run(["notebooklm", *args], capture_output=capture, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"notebooklm {' '.join(args)} falhou: {r.stderr or r.stdout}")
    return r.stdout if capture else ""

def _notebooks(payload):
    d = json.loads(payload)
    return d.get("notebooks", d) if isinstance(d, dict) else d

def resolver_notebook(titulo=NOTEBOOK, runner=_run):
    for n in _notebooks(runner(["list", "--json"])):
        if isinstance(n, dict) and n.get("title") == titulo:
            return n.get("id") or n.get("notebook_id")
    criado = json.loads(runner(["create", titulo, "--json"]))
    return criado.get("id") or criado.get("notebook_id")
