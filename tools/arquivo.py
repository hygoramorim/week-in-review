#!/usr/bin/env python3
"""Ferramentas do Week In Review.

  arquivar [AAAA-MM-DD]  copia index.html para editions/AAAA-MM-DD.html
  build                  regenera arquivo.html a partir de editions/

A data, quando omitida, sai do proprio index.html (barra superior).
"""

import html
import re
import shutil
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
EDICOES = RAIZ / "editions"
ARQUIVO = RAIZ / "arquivo.html"

MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
MESES_EN = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
            "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
            "november": 11, "december": 12}


def texto(fragmento):
    """Remove tags e normaliza espacos de um trecho de HTML."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragmento)).strip()


def busca(padrao, fonte, padrao_alternativo=None):
    achado = re.search(padrao, fonte, re.S | re.I)
    if not achado and padrao_alternativo:
        achado = re.search(padrao_alternativo, fonte, re.S | re.I)
    return texto(achado.group(1)) if achado else ""


def data_do_index(fonte):
    """Le a data da barra superior do index (ex.: '31 July 2026')."""
    barra = busca(r'<div class="right">(.*?)</div>', fonte)
    achado = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", barra)
    if achado:
        dia, mes, ano = achado.groups()
        if mes.lower() in MESES_EN:
            return date(int(ano), MESES_EN[mes.lower()], int(dia)).isoformat()
    return date.today().isoformat()


def por_extenso(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def ler_edicao(caminho):
    fonte = caminho.read_text(encoding="utf-8")
    capa = re.search(r'<aside class="cover">(.*?)</aside>', fonte, re.S)
    capa = capa.group(1) if capa else fonte
    return {
        "arquivo": f"editions/{caminho.name}",
        "data": caminho.stem,
        "edicao": busca(r'class="pill">\s*Issue\s*(\d+)\s*<', fonte) or "—",
        "tema": busca(r"<h2>(.*?)</h2>", capa) or busca(r"<title>(.*?)</title>", fonte),
        "resumo": busca(r"<h2>.*?</h2>\s*<p>(.*?)</p>", capa),
    }


def arquivar(iso=None):
    if not INDEX.exists():
        sys.exit("index.html nao encontrado.")
    fonte = INDEX.read_text(encoding="utf-8")
    iso = iso or data_do_index(fonte)
    try:
        date.fromisoformat(iso)
    except ValueError:
        sys.exit(f"Data invalida: {iso!r}. Use o formato AAAA-MM-DD.")

    EDICOES.mkdir(exist_ok=True)
    destino = EDICOES / f"{iso}.html"
    # dentro de editions/ os links relativos da raiz sobem um nivel
    copia = re.sub(r'href="(?!https?:|#|/|\.\./)', 'href="../', fonte)
    destino.write_text(copia, encoding="utf-8")
    print(f"arquivada  editions/{iso}.html")
    return destino


CABECA = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Arquivo — Week In Review</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --paper:#f4eedf;--cream:#fff9ec;--ink:#161514;--muted:#625b4f;
      --red:#c6462d;--navy:#112f45;--card:#fbf4e4;
      --serif:'Libre Baskerville',Georgia,serif;
      --sans:'IBM Plex Sans',Arial,sans-serif;
      --cond:'Oswald',Impact,sans-serif;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      background:
        linear-gradient(90deg,rgba(22,21,20,.045) 1px,transparent 1px) 0 0/64px 64px,
        radial-gradient(circle at 15% 2%,rgba(198,70,45,.16),transparent 36%),
        var(--paper);
      color:var(--ink);font-family:var(--sans);line-height:1.6;
    }
    a{color:inherit;text-underline-offset:4px}
    .page{max-width:1180px;margin:auto;padding:24px 18px 64px}
    .top{
      display:grid;grid-template-columns:1fr auto 1fr;gap:14px;
      border-top:6px solid var(--ink);border-bottom:2px solid var(--ink);
      padding:10px 0;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)
    }
    .top .mid{color:var(--red);font-weight:700;text-align:center}.top .right{text-align:right}
    header{padding:26px 0 30px;border-bottom:3px solid var(--ink)}
    .kicker{font-family:var(--cond);color:var(--red);letter-spacing:.13em;text-transform:uppercase}
    h1{
      font-family:var(--cond);font-size:clamp(56px,11vw,116px);line-height:.84;
      margin:10px 0 0;text-transform:uppercase;letter-spacing:-.05em
    }
    .lede{font-family:var(--serif);font-size:clamp(18px,2.4vw,24px);color:var(--navy);margin-top:16px;max-width:60ch}
    .lista{display:grid;gap:18px;margin-top:34px}
    .edicao{
      display:grid;grid-template-columns:150px 1fr auto;gap:24px;align-items:start;
      border:1px solid var(--ink);background:var(--card);padding:22px 24px;
      text-decoration:none;box-shadow:0 14px 34px rgba(22,21,20,.10)
    }
    .edicao .num{font-family:var(--cond);font-size:52px;color:var(--red);line-height:.9}
    .edicao .quando{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-top:4px}
    .edicao h2{font-family:var(--serif);font-size:clamp(21px,2.4vw,28px);line-height:1.14;margin:0 0 8px}
    .edicao p{margin:0;color:var(--muted)}
    .abrir{font-family:var(--cond);font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--red);white-space:nowrap;padding-top:8px}
    .atual{border-left:9px solid var(--red)}
    .selo{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--red);font-weight:700}
    .vazio{border:1px dashed var(--ink);padding:34px;text-align:center;color:var(--muted);margin-top:34px}
    footer{border-top:4px solid var(--ink);margin-top:48px;padding-top:18px;color:var(--muted);font-size:13px}
    .brand{font-family:var(--cond);color:var(--red);letter-spacing:.04em}
    @media(max-width:860px){
      .top,.edicao{grid-template-columns:1fr}
      .top .mid,.top .right{text-align:left}
      .abrir{padding-top:0}
    }
  </style>
</head>
<body>
<main class="page">
  <div class="top">
    <div><a href="index.html">Edição atual</a></div>
    <div class="mid">No AI-generated imagery</div>
    <div class="right">__TOTAL__</div>
  </div>

  <header>
    <div class="kicker">A weekly magazine from the Obsidian Vault</div>
    <h1>Arquivo</h1>
    <p class="lede">Todas as edições da <strong>Week In Review</strong>, da mais recente à primeira. Cada semana começa nas transcrições que entram no Vault e termina aqui.</p>
  </header>

__LISTA__

  <footer>
    <strong class="brand">Week In Review</strong> — by Hygor Beltrão Amorim.<br>
    Página gerada automaticamente por <code>tools/arquivo.py</code>.
  </footer>
</main>
</body>
</html>
"""

CARTAO = """    <a class="edicao{destaque}" href="{arquivo}">
      <div>
        <div class="num">{edicao}</div>
        <div class="quando">{quando}</div>{selo}
      </div>
      <div>
        <h2>{tema}</h2>
        <p>{resumo}</p>
      </div>
      <div class="abrir">Ler edição →</div>
    </a>"""


def build():
    caminhos = sorted(EDICOES.glob("*.html"), reverse=True) if EDICOES.exists() else []
    edicoes = [ler_edicao(p) for p in caminhos]

    if edicoes:
        cartoes = []
        for i, e in enumerate(edicoes):
            cartoes.append(CARTAO.format(
                destaque=" atual" if i == 0 else "",
                selo='\n        <div class="selo">Edição atual</div>' if i == 0 else "",
                arquivo=html.escape(e["arquivo"]),
                edicao=html.escape(e["edicao"]),
                quando=html.escape(por_extenso(e["data"])),
                tema=html.escape(e["tema"]),
                resumo=html.escape(e["resumo"]),
            ))
        lista = '  <section class="lista">\n' + "\n".join(cartoes) + "\n  </section>"
    else:
        lista = '  <div class="vazio">Nenhuma edição arquivada ainda.</div>'

    total = f"{len(edicoes)} edição" if len(edicoes) == 1 else f"{len(edicoes)} edições"
    ARQUIVO.write_text(
        CABECA.replace("__LISTA__", lista).replace("__TOTAL__", total),
        encoding="utf-8",
    )
    print(f"gerado     arquivo.html ({total})")


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else "build"
    if comando == "arquivar":
        arquivar(sys.argv[2] if len(sys.argv) > 2 else None)
        build()
    elif comando == "build":
        build()
    elif comando == "data":
        print(data_do_index(INDEX.read_text(encoding="utf-8")))
    else:
        sys.exit(__doc__)
