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

def proxima_issue(content_dir):
    content_dir = Path(content_dir)
    maior = 0
    if content_dir.exists():
        for pasta in content_dir.iterdir():
            arq = pasta / "edicao.json"
            if arq.exists():
                try:
                    n = int(json.loads(arq.read_text(encoding="utf-8")).get("edicao", 0))
                    maior = max(maior, n)
                except (ValueError, json.JSONDecodeError):
                    pass
    return f"{maior + 1:03d}"

def montar_item(indice, achado):
    fm = achado["fm"]
    titulo = fm.get("title", achado["caminho"].stem)
    vid = fm.get("video_id", "")
    rel = achado["caminho"]
    # caminho relativo ao Vault, para o campo "transcricao"
    try:
        transcricao = str(rel.relative_to(VAULT))
    except ValueError:
        transcricao = str(rel)
    return {
        "slug": slugificar(titulo),
        "numero": f"{indice + 1:02d}",
        "fonte": fm.get("channel", ""),
        "toc": titulo[:24],
        "titulo": titulo,
        "resumo": "",   # Claude preenche na redacao
        "porque": "",   # Claude preenche na redacao
        "tags": fm.get("tags", []),
        "imagem": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else "",
        "alt": titulo,
        "credito": "Imagem: thumbnail oficial / YouTube",
        "artigo": f"{slugificar(titulo)}.md",
        "transcricao": transcricao,
        "links": [{"texto": "Watch", "url": fm.get("url", "")}] if fm.get("url") else [],
    }

def criar_edicao(achados, content_dir, force=False):
    content_dir = Path(content_dir)
    data = achados[0]["data"]
    pasta = content_dir / data
    if pasta.exists() and not force:
        raise FileExistsError(f"{pasta} ja existe (use --force para sobrescrever)")
    artigos_dir = pasta / "artigos"
    # com --force a pasta pode ter artigos de uma montagem anterior com outros
    # slugs; limpa os .md orfaos antes de recriar para nao acumular lixo.
    if artigos_dir.exists():
        for antigo in artigos_dir.glob("*.md"):
            antigo.unlink()
    artigos_dir.mkdir(parents=True, exist_ok=True)
    itens = [montar_item(i, a) for i, a in enumerate(achados)]
    edicao = {
        "edicao": proxima_issue(content_dir),
        "data": data,
        "titulo": "Week In Review",
        "autor": "Hygor Beltrão Amorim",
        "chapeu": "A weekly magazine from the Obsidian Vault",
        "barra": {"esquerda": "Vault Edition / Friday Intake",
                  "meio": "No AI-generated imagery"},
        "pills": [], "dek": "",
        "capa": {"imagem": itens[0]["imagem"], "alt": itens[0]["alt"],
                 "titulo": "", "resumo": ""},
        "signals": [], "itens": itens, "leitura": [], "canais": [], "pergunta": "",
    }
    (pasta / "edicao.json").write_text(
        json.dumps(edicao, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "editorial.md").write_text(
        "<!-- Editorial a escrever a partir das transcrições. -->\n", encoding="utf-8")
    for it in itens:
        (pasta / "artigos" / it["artigo"]).write_text(
            f"# {it['titulo']}\n", encoding="utf-8")
    return pasta

def main():
    args = sys.argv[1:]
    estudos = VAULT / "Estudos"
    if not estudos.exists():
        sys.exit(f"Vault nao encontrado em {estudos}. Ajuste WIR_VAULT.")
    achados = descobrir_recentes(estudos, n=5)
    if len(achados) < 5:
        print(f"  aviso: so {len(achados)} transcricoes com data encontradas.")
    if not achados:
        sys.exit("nenhuma transcricao com data no Vault.")
    if "--dry-run" in args:
        for a in achados:
            print(f"  {a['data']}  {a['fm'].get('channel','?'):<22} {a['fm'].get('title','')}")
        return
    pasta = criar_edicao(achados, CONTENT, force="--force" in args)
    print(f"  criado {pasta} com {len(achados)} itens. Agora escreva os artigos.")
    print(json.dumps(
        [{"slug": slugificar(a["fm"].get("title", "")),
          "fonte": a["fm"].get("channel", ""),
          "transcricao": str(a["caminho"])} for a in achados], ensure_ascii=False))

if __name__ == "__main__":
    main()
