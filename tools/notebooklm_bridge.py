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

def adicionar_fonte(nb_id, brief_path, runner=_run):
    # CLI real: o caminho do .md e' argumento posicional (CONTENT), tipo auto-detectado.
    # NAO existe flag --file. Ver `notebooklm source add --help`.
    saida = runner(["source", "add", str(brief_path),
                    "--notebook", nb_id, "--type", "text", "--json"])
    try:
        d = json.loads(saida)
        return d.get("source_id") or d.get("id")
    except json.JSONDecodeError:
        return ""

def gerar_e_baixar(nb_id, source_id, data, runner=_run, audio_dir=AUDIO):
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    gen = ["generate", "audio", "--notebook", nb_id,
           "--language", "pt-BR", "--wait"]
    if source_id:
        gen += ["-s", source_id]
    runner(gen)
    destino = audio_dir / f"{data}.mp3"
    runner(["download", "audio", str(destino), "--notebook", nb_id, "--latest"])
    return destino
