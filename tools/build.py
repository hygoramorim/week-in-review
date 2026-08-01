#!/usr/bin/env python3
"""Gera o site da Week In Review a partir de content/.

  python3 tools/build.py            constroi tudo
  python3 tools/build.py --check    so valida, nao escreve nada

Entra:  content/AAAA-MM-DD/{edicao.json, editorial.md, artigos/*.md}
Sai:    index.html, arquivo.html, editions/AAAA-MM-DD/*.html,
        podcast/AAAA-MM-DD-brief.md

Nada dentro de editions/ e podcast/ deve ser editado a mao: o build
sobrescreve. O que voce edita vive em content/.
"""

import html
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markdown_min as md

RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"
EDITIONS = RAIZ / "editions"
PODCAST = RAIZ / "podcast"
AUDIO = PODCAST / "audio"

# um artigo com menos palavras que isso ainda e rascunho:
# o botao "Leia o artigo" nao aparece e a pagina avisa.
MINIMO_ARTIGO = 200

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

FONTES = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700'
    "&family=Libre+Baskerville:wght@400;700&family=Oswald:wght@500;600;700&display=swap\" rel=\"stylesheet\">"
)


def e(valor):
    """Escapa para uso dentro do HTML."""
    return html.escape(str(valor or ""), quote=True)


def por_extenso(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def cabeca(titulo, css, descricao=""):
    meta = f'\n  <meta name="description" content="{e(descricao)}">' if descricao else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titulo)}</title>{meta}
  {FONTES}
  <link rel="stylesheet" href="{css}">
</head>
<body>
<main class="page">"""


RODAPE = """</main>
</body>
</html>
"""


# ---------------------------------------------------------------- leitura

def carregar_edicoes():
    """Le content/ e devolve as edicoes da mais nova para a mais antiga."""
    if not CONTENT.exists():
        sys.exit("content/ nao existe. Nada para construir.")

    edicoes = []
    for pasta in sorted(CONTENT.iterdir(), reverse=True):
        if not pasta.is_dir() or not (pasta / "edicao.json").exists():
            continue
        try:
            dados = json.loads((pasta / "edicao.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            sys.exit(f"{pasta.name}/edicao.json tem JSON invalido: {erro}")

        dados["data"] = dados.get("data") or pasta.name
        try:
            date.fromisoformat(dados["data"])
        except ValueError:
            sys.exit(f"{pasta.name}: data invalida, use pastas no formato AAAA-MM-DD.")

        editorial = pasta / "editorial.md"
        dados["editorial_md"] = editorial.read_text(encoding="utf-8") if editorial.exists() else ""

        for item in dados.get("itens", []):
            item["artigo_md"] = ""
            item["pronto"] = False
            nome = item.get("artigo")
            if not nome:
                continue
            caminho = pasta / "artigos" / nome
            if not caminho.exists():
                print(f"  aviso: {pasta.name} -> artigos/{nome} nao existe")
                continue
            texto = caminho.read_text(encoding="utf-8")
            # a primeira linha "# Titulo" vira o titulo da pagina do artigo
            linhas = texto.strip().split("\n")
            if linhas and linhas[0].startswith("# "):
                item["artigo_titulo"] = linhas[0][2:].strip()
                texto = "\n".join(linhas[1:]).strip()
            item["artigo_md"] = texto
            item["palavras"] = md.palavras(texto)
            item["minutos"] = md.minutos(texto)
            item["pronto"] = item["palavras"] >= MINIMO_ARTIGO

        edicoes.append(dados)

    if not edicoes:
        sys.exit("nenhuma edicao encontrada em content/.")
    return edicoes


# ------------------------------------------------------------- a edicao

def render_edicao(ed, css, link_arquivo, link_artigo, prefixo_audio="."):
    d = ed["data"]
    barra = ed.get("barra", {})
    partes = [cabeca(f"{ed.get('titulo', 'Week In Review')} — Issue {ed.get('edicao', '')}",
                     css, ed.get("capa", {}).get("resumo", ""))]

    partes.append(f"""
  <div class="top">
    <div>{e(barra.get('esquerda', ''))}</div>
    <div class="mid">{e(barra.get('meio', ''))}</div>
    <div class="right"><a href="{link_arquivo}">Arquivo de edições</a> · {e(por_extenso(d))}</div>
  </div>""")

    capa = ed.get("capa", {})
    pills = "".join(f'\n        <span class="pill">{e(p)}</span>' for p in ed.get("pills", []))
    partes.append(f"""
  <header class="hero">
    <section>
      <div class="kicker">{e(ed.get('chapeu', ''))}</div>
      <h1>Week<br>In Review</h1>
      <div class="by">by {e(ed.get('autor', 'Hygor Beltrão Amorim'))}</div>
      <div class="pills">{pills}
      </div>
    </section>
    <aside class="cover">
      <img src="{e(capa.get('imagem', ''))}" alt="{e(capa.get('alt', ''))}">
      <h2>{e(capa.get('titulo', ''))}</h2>
      <p>{e(capa.get('resumo', ''))}</p>
    </aside>
  </header>""")

    audio = ed.get("podcast_audio")
    if audio:
        src = f"{prefixo_audio}/podcast/audio/{e(audio)}"
        partes.append(f"""
  <section class="podcast">
    <div class="section-title"><h2>Ouça a edição</h2></div>
    <audio controls preload="none" src="{src}"></audio>
    <p class="podcast-nota">Episódio gerado no NotebookLM a partir do resumo da semana.</p>
  </section>""")

    itens = ed.get("itens", [])
    toc = "".join(
        f'\n    <a href="#{e(i["slug"])}"><b>{e(i.get("numero", ""))}</b>'
        f'<span>{e(i.get("toc", i.get("fonte", "")))}</span></a>'
        for i in itens
    )
    partes.append(f'\n  <nav class="toc">{toc}\n  </nav>')

    if ed.get("editorial_md"):
        partes.append(f"""
  <section>
    <div class="section-title"><h2>Carta editorial</h2></div>
    <div class="editorial">
      <aside class="dek">{e(ed.get('dek', ''))}</aside>
      <article>
{md.render(ed['editorial_md'])}
      </article>
    </div>
  </section>""")

    if ed.get("signals"):
        cartoes = "".join(
            f'\n      <div class="signal"><div class="num">{e(s.get("num", ""))}</div>'
            f'<h3>{e(s.get("titulo", ""))}</h3><p>{e(s.get("texto", ""))}</p></div>'
            for s in ed["signals"]
        )
        partes.append(f"""
  <section>
    <div class="section-title"><h2>Signals</h2></div>
    <div class="signals">{cartoes}
    </div>
  </section>""")

    cards = []
    for item in itens:
        tags = "".join(f'<span class="tag">{e(t)}</span>' for t in item.get("tags", []))
        botoes = []
        if item["pronto"]:
            botoes.append(
                f'<a class="btn artigo" href="{link_artigo(item["slug"])}">Leia o artigo</a>'
                f'<span class="tempo">{item["minutos"]} min de leitura</span>'
            )
        for i, ln in enumerate(item.get("links", [])):
            classe = "btn primary" if i == 0 and not item["pronto"] else "btn"
            botoes.append(f'<a class="{classe}" href="{e(ln["url"])}" target="_blank" rel="noopener">{e(ln["texto"])}</a>')
        cards.append(f"""
      <article class="feature" id="{e(item['slug'])}">
        <div class="media">
          <img src="{e(item.get('imagem', ''))}" alt="{e(item.get('alt', item.get('fonte', '')))}">
          <span class="credit">{e(item.get('credito', ''))}</span>
        </div>
        <div class="copy">
          <div class="number">{e(item.get('numero', ''))} / {e(item.get('fonte', ''))}</div>
          <h3>{e(item.get('titulo', ''))}</h3>
          <div class="meta">{tags}</div>
          <p>{e(item.get('resumo', ''))}</p>
          <p class="why">Por que importa: {e(item.get('porque', ''))}</p>
          <div class="links">{''.join(botoes)}</div>
        </div>
      </article>""")
    partes.append(f"""
  <section>
    <div class="section-title"><h2>Os vídeos</h2></div>
    <div class="features">{''.join(cards)}
    </div>
  </section>""")

    if ed.get("leitura") or ed.get("canais"):
        leitura = "".join(f"\n          <li>{md.inline(i)}</li>" for i in ed.get("leitura", []))
        canais = "".join(
            f'\n          <div class="channel"><b>{e(c.get("nome", ""))}</b>'
            f'<p>{e(c.get("sobre", ""))}</p></div>'
            for c in ed.get("canais", [])
        )
        partes.append(f"""
  <section>
    <div class="section-title"><h2>Para expandir</h2></div>
    <div class="matrix">
      <div class="box">
        <h3>Reading list da edição</h3>
        <ul>{leitura}
        </ul>
      </div>
      <div class="box">
        <h3>Novos canais</h3>
        <div class="channels">{canais}
        </div>
      </div>
    </div>
  </section>""")

    if ed.get("pergunta"):
        partes.append(f"""
  <section class="question">
    <b>Pergunta da semana</b>
    <p>{e(ed['pergunta'])}</p>
  </section>""")

    fontes = "".join(
        f"\n      <code>{e(i['transcricao'])}</code><br>"
        for i in itens if i.get("transcricao")
    )
    partes.append(f"""
  <footer>
    <div><strong class="brand">Week In Review</strong><br>by {e(ed.get('autor', 'Hygor Beltrão Amorim'))}.
      Edição {e(ed.get('edicao', ''))}, publicada em {e(por_extenso(d))}.</div>
    <div><strong>Fontes no Vault:</strong><br>{fontes}
    </div>
  </footer>
{RODAPE}""")
    return "".join(partes)


# ------------------------------------------------------------ os artigos

def render_artigo(ed, item, anterior, proximo):
    css = "../../assets/revista.css"
    titulo = item.get("artigo_titulo", item.get("titulo", ""))
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in item.get("tags", []))

    if item["pronto"]:
        corpo = f'<div class="artigo-corpo">\n{md.render(item["artigo_md"])}\n  </div>'
    else:
        corpo = (
            '<div class="rascunho"><strong>Artigo em produção.</strong> '
            f'Este texto ainda não foi escrito — são {item.get("palavras", 0)} palavras de '
            f'{MINIMO_ARTIGO} necessárias. Escreva em '
            f'<code>content/{ed["data"]}/artigos/{e(item.get("artigo", ""))}</code> '
            "e rode <code>./publicar.sh</code>.</div>"
        )

    links = "".join(
        f'\n      <a class="btn" href="{e(l["url"])}" target="_blank" rel="noopener">{e(l["texto"])}</a>'
        for l in item.get("links", [])
    )
    nav = []
    for vizinho, rotulo, classe in ((anterior, "Anterior", ""), (proximo, "Próximo", " dir")):
        if vizinho:
            nav.append(f'\n    <a class="{classe.strip()}" href="{e(vizinho["slug"])}.html">'
                       f'<small>{rotulo}</small><b>{e(vizinho.get("titulo", ""))}</b></a>')
        else:
            nav.append("\n    <span></span>")

    return f"""{cabeca(f'{titulo} — Week In Review', css, item.get('resumo', ''))}
  <div class="top">
    <div><a href="index.html">← Voltar para a edição</a></div>
    <div class="mid">Issue {e(ed.get('edicao', ''))}</div>
    <div class="right"><a href="../../arquivo.html">Arquivo</a> · {e(por_extenso(ed['data']))}</div>
  </div>

  <header class="artigo-head">
    <div class="kicker">{e(item.get('numero', ''))} / {e(item.get('fonte', ''))}</div>
    <h1>{e(titulo)}</h1>
    <div class="artigo-meta">{tags}
      <span class="tempo">{item.get('minutos', 0)} min de leitura</span>
    </div>
  </header>

  {corpo}

  <section class="artigo-fontes">
    <h2>Fontes</h2>
    <p>{e(item.get('porque', ''))}</p>
    <div class="links">{links}
    </div>
  </section>

  <nav class="artigo-nav">{''.join(nav)}
  </nav>
{RODAPE}"""


# ------------------------------------------------------------- o arquivo

def render_arquivo(edicoes):
    total = f"{len(edicoes)} edição" if len(edicoes) == 1 else f"{len(edicoes)} edições"
    cartoes = []
    for i, ed in enumerate(edicoes):
        capa = ed.get("capa", {})
        prontos = sum(1 for x in ed.get("itens", []) if x["pronto"])
        selo = '\n        <div class="selo">Edição atual</div>' if i == 0 else ""
        cartoes.append(f"""
    <a class="edicao{' atual' if i == 0 else ''}" href="editions/{e(ed['data'])}/index.html">
      <div>
        <div class="num">{e(ed.get('edicao', ''))}</div>
        <div class="quando">{e(por_extenso(ed['data']))}</div>{selo}
      </div>
      <div>
        <h2>{e(capa.get('titulo', ''))}</h2>
        <p>{e(capa.get('resumo', ''))}</p>
        <p class="tempo">{len(ed.get('itens', []))} conteúdos · {prontos} artigos publicados</p>
      </div>
      <div class="abrir">Ler edição →</div>
    </a>""")

    return f"""{cabeca('Arquivo — Week In Review', 'assets/revista.css',
                       'Todas as edições da Week In Review.')}
  <div class="top">
    <div><a href="index.html">Edição atual</a></div>
    <div class="mid">No AI-generated imagery</div>
    <div class="right">{total}</div>
  </div>

  <header class="arquivo-head">
    <div class="kicker">A weekly magazine from the Obsidian Vault</div>
    <h1>Arquivo</h1>
    <p class="lede">Todas as edições da <strong>Week In Review</strong>, da mais recente à
      primeira. Cada semana começa nas transcrições que entram no Vault e termina aqui.</p>
  </header>

  <section class="lista">{''.join(cartoes)}
  </section>

  <footer>
    <div><strong class="brand">Week In Review</strong> — by Hygor Beltrão Amorim.</div>
    <div>Página gerada por <code>tools/build.py</code>.</div>
  </footer>
{RODAPE}"""


# ------------------------------------------------ o resumo para o podcast

def render_brief(ed):
    """Resumo da edicao no formato que alimenta o NotebookLM."""
    d = ed["data"]
    linhas = [
        f"# Week In Review — Issue {ed.get('edicao', '')} ({por_extenso(d)})",
        "",
        "## Direção do episódio",
        "",
        "- Duração alvo: **25 minutos**.",
        f"- Cobrir **todos os {len(ed.get('itens', []))} conteúdos**, na ordem abaixo, "
        "sem pular nenhum.",
        "- Orçamento aproximado: 2 min de abertura, "
        f"{max(1, round((25 - 4) / max(1, len(ed.get('itens', [])))))} min por conteúdo, "
        "2 min de fecho com a pergunta da semana.",
        "- Tom: conversa entre dois apresentadores, analítica, sem hype. Português do Brasil.",
        "- Abrir pela tese da edição e fechar devolvendo a pergunta ao ouvinte.",
        "",
        f"**Tese:** {ed.get('dek', '')}",
        "",
        "## Carta editorial",
        "",
        ed.get("editorial_md", "").strip(),
        "",
    ]

    for item in ed.get("itens", []):
        linhas += [
            f"## {item.get('numero', '')} — {item.get('fonte', '')}: {item.get('titulo', '')}",
            "",
            f"**Resumo:** {item.get('resumo', '')}",
            "",
            f"**Por que importa:** {item.get('porque', '')}",
            "",
            f"**Temas:** {', '.join(item.get('tags', []))}",
            "",
        ]
        if item["pronto"]:
            linhas += ["### Artigo completo", "", item["artigo_md"].strip(), ""]
        else:
            linhas += ["_Artigo ainda não escrito — usar apenas resumo acima._", ""]

    if ed.get("pergunta"):
        linhas += ["## Pergunta da semana", "", ed["pergunta"], ""]

    return "\n".join(linhas)


# ----------------------------------------------------------------- build

def podar_audio(dir_audio, manter=3):
    """Mantem os `manter` mp3 mais recentes (por nome AAAA-MM-DD.mp3), apaga o resto."""
    dir_audio = Path(dir_audio)
    if not dir_audio.exists():
        return []
    mp3s = sorted(dir_audio.glob("*.mp3"), key=lambda p: p.name, reverse=True)
    apagados = []
    for p in mp3s[manter:]:
        p.unlink()
        apagados.append(p.name)
    for nome in apagados:
        print(f"  áudio podado (retenção {manter}): {nome}")
    return apagados


def build(checar=False):
    edicoes = carregar_edicoes()
    escritos = 0

    if not checar:
        if EDITIONS.exists():
            shutil.rmtree(EDITIONS)
        EDITIONS.mkdir()
        PODCAST.mkdir(exist_ok=True)

    for ed in edicoes:
        d = ed["data"]
        itens = ed.get("itens", [])
        prontos = sum(1 for i in itens if i["pronto"])
        print(f"  {d}  issue {ed.get('edicao', '?'):>3}  "
              f"{len(itens)} conteúdos, {prontos} artigos prontos")

        if checar:
            continue

        pasta = EDITIONS / d
        pasta.mkdir(parents=True)

        (pasta / "index.html").write_text(
            render_edicao(ed, "../../assets/revista.css", "../../arquivo.html",
                          lambda slug: f"{slug}.html", prefixo_audio="../.."),
            encoding="utf-8")
        escritos += 1

        for i, item in enumerate(itens):
            anterior = itens[i - 1] if i > 0 else None
            proximo = itens[i + 1] if i + 1 < len(itens) else None
            (pasta / f"{item['slug']}.html").write_text(
                render_artigo(ed, item, anterior, proximo), encoding="utf-8")
            escritos += 1

        (PODCAST / f"{d}-brief.md").write_text(render_brief(ed), encoding="utf-8")
        escritos += 1

    if checar:
        print("ok — content/ está válido.")
        return

    atual = edicoes[0]
    (RAIZ / "index.html").write_text(
        render_edicao(atual, "assets/revista.css", "arquivo.html",
                      lambda slug: f"editions/{atual['data']}/{slug}.html",
                      prefixo_audio="."),
        encoding="utf-8")
    (RAIZ / "arquivo.html").write_text(render_arquivo(edicoes), encoding="utf-8")
    podar_audio(AUDIO, manter=3)
    print(f"  gerados {escritos + 2} arquivos · home aponta para a issue {atual.get('edicao', '')}")


if __name__ == "__main__":
    build(checar="--check" in sys.argv)
