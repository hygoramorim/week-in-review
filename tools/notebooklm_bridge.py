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
    if not source_id:
        raise RuntimeError(
            "source_id vazio: geraria audio de todas as fontes do notebook. "
            "Verifique adicionar_fonte / o --json do source add.")
    gen = ["generate", "audio", "--notebook", nb_id,
           "--language", "pt-BR", "--wait", "-s", source_id]
    runner(gen)
    destino = audio_dir / f"{data}.mp3"
    runner(["download", "audio", str(destino), "--notebook", nb_id, "--latest"])
    return destino

def gravar_podcast_audio(data, nome_mp3, content_dir=CONTENT):
    arq = Path(content_dir) / data / "edicao.json"
    dados = json.loads(arq.read_text(encoding="utf-8"))
    dados["podcast_audio"] = nome_mp3
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("uso: notebooklm_bridge.py AAAA-MM-DD [--dry-run]")
    data = args[0]
    brief = RAIZ / "podcast" / f"{data}-brief.md"
    if not brief.exists():
        sys.exit(f"brief não encontrado: {brief}. Rode build.py antes.")
    nb_id = resolver_notebook()
    print(f"  notebook: {nb_id}")
    if "--dry-run" in args:
        print("  dry-run: parando antes de gerar áudio.")
        return
    src = adicionar_fonte(nb_id, brief)
    print(f"  fonte adicionada: {src}")
    mp3 = gerar_e_baixar(nb_id, src, data)
    gravar_podcast_audio(data, mp3.name)
    print(f"  mp3 em {mp3}, podcast_audio gravado. Rode build.py + publicar.sh.")

if __name__ == "__main__":
    main()
