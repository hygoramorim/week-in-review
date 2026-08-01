#!/usr/bin/env python3
"""Ponte entre o brief da edicao e o NotebookLM (gera e baixa o mp3).

  python3 tools/notebooklm_bridge.py AAAA-MM-DD            # gera + baixa + grava
  python3 tools/notebooklm_bridge.py AAAA-MM-DD --dry-run  # so valida, nao cria nada

Usa a CLI notebooklm-py (ja autenticada em ~/.notebooklm). Um notebook novo por
semana (nome 'week in review DD MM AA'); o audio e limitado a fonte da semana via
-s <source_id>.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"
AUDIO = RAIZ / "podcast" / "audio"

def _run(args, capture=True):
    r = subprocess.run(["notebooklm", *args], capture_output=capture, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"notebooklm {' '.join(args)} falhou: {r.stderr or r.stdout}")
    return r.stdout if capture else ""

def nome_notebook(data):
    """Nome do notebook da semana: 'week in review DD MM AA' a partir de AAAA-MM-DD."""
    aaaa, mm, dd = data.split("-")
    return f"week in review {dd} {mm} {aaaa[2:]}"

def criar_notebook_semana(data, runner=_run):
    """Cria SEMPRE um notebook novo para a semana e devolve o id."""
    criado = json.loads(runner(["create", nome_notebook(data), "--json"]))
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
    if "--dry-run" in args:
        print(f"  dry-run: brief ok, notebook seria '{nome_notebook(data)}'. Nada criado.")
        return
    nb_id = criar_notebook_semana(data)
    print(f"  notebook: {nb_id}")
    src = adicionar_fonte(nb_id, brief)
    print(f"  fonte adicionada: {src}")
    mp3 = gerar_e_baixar(nb_id, src, data)
    gravar_podcast_audio(data, mp3.name)
    print(f"  mp3 em {mp3}, podcast_audio gravado. Rode build.py + publicar.sh.")

if __name__ == "__main__":
    main()
