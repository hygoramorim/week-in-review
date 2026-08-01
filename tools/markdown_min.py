#!/usr/bin/env python3
"""Renderizador de Markdown sem dependencia externa.

Cobre o subconjunto que a revista usa. Se voce escrever algo fora desta
lista, sai como paragrafo comum:

  # ## ###        titulos
  paragrafos      separados por linha em branco
  **negrito**     *italico*  _italico_
  [texto](url)    `codigo`
  > citacao       (linhas seguidas viram um bloco so)
  - item          lista sem ordem
  1. item         lista numerada
  ---             linha divisoria
"""

import html
import re

_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODIGO = re.compile(r"`([^`]+)`")
_NEGRITO = re.compile(r"\*\*(.+?)\*\*")
_ITALICO_ASTERISCO = re.compile(r"(?<!\*)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\*)")
_ITALICO_UNDERLINE = re.compile(r"(?<![\w_])_(?!\s)([^_\n]+?)(?<!\s)_(?![\w_])")

_COMENTARIO = re.compile(r"<!--.*?-->", re.S)
_TITULO = re.compile(r"^(#{1,6})\s+(.*)$")
_ITEM = re.compile(r"^[-*]\s+(.*)$")
_ITEM_NUM = re.compile(r"^\d+[.)]\s+(.*)$")
_DIVISOR = re.compile(r"^\s*(?:-{3,}|\*{3,})\s*$")


def inline(texto):
    """Aplica a formatacao de dentro da linha, ja escapando o HTML."""
    saida = html.escape(texto, quote=False)
    # marcadores sao guardados fora do fluxo pra nao serem reprocessados
    guardados = []

    def guardar(fragmento):
        guardados.append(fragmento)
        return f"\x00{len(guardados) - 1}\x00"

    saida = _CODIGO.sub(lambda m: guardar(f"<code>{m.group(1)}</code>"), saida)
    saida = _LINK.sub(
        lambda m: guardar(f'<a href="{m.group(2)}">{m.group(1)}</a>'), saida
    )
    saida = _NEGRITO.sub(r"<strong>\1</strong>", saida)
    saida = _ITALICO_ASTERISCO.sub(r"<em>\1</em>", saida)
    saida = _ITALICO_UNDERLINE.sub(r"<em>\1</em>", saida)
    return re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], saida)


def _fechar(bloco, linhas, saida):
    """Despeja o bloco acumulado no formato certo."""
    if not linhas:
        return
    if bloco == "p":
        saida.append(f"<p>{inline(' '.join(linhas))}</p>")
    elif bloco == "citacao":
        saida.append(f"<blockquote><p>{inline(' '.join(linhas))}</p></blockquote>")
    elif bloco in ("ul", "ol"):
        itens = "".join(f"<li>{inline(i)}</li>" for i in linhas)
        saida.append(f"<{bloco}>{itens}</{bloco}>")


def render(texto):
    """Converte Markdown em HTML. Comentarios HTML sao descartados."""
    saida, linhas, bloco = [], [], None
    texto = _COMENTARIO.sub("", texto)

    for linha in texto.replace("\r\n", "\n").split("\n"):
        crua = linha.rstrip()
        nu = crua.strip()

        if not nu:
            _fechar(bloco, linhas, saida)
            linhas, bloco = [], None
            continue

        if _DIVISOR.match(crua):
            _fechar(bloco, linhas, saida)
            linhas, bloco = [], None
            saida.append("<hr>")
            continue

        titulo = _TITULO.match(nu)
        if titulo:
            _fechar(bloco, linhas, saida)
            linhas, bloco = [], None
            nivel = len(titulo.group(1))
            saida.append(f"<h{nivel}>{inline(titulo.group(2))}</h{nivel}>")
            continue

        if nu.startswith(">"):
            novo, conteudo = "citacao", nu.lstrip(">").strip()
        elif _ITEM.match(nu):
            novo, conteudo = "ul", _ITEM.match(nu).group(1)
        elif _ITEM_NUM.match(nu):
            novo, conteudo = "ol", _ITEM_NUM.match(nu).group(1)
        else:
            novo, conteudo = "p", nu

        if novo != bloco:
            _fechar(bloco, linhas, saida)
            linhas, bloco = [], novo
        linhas.append(conteudo)

    _fechar(bloco, linhas, saida)
    return "\n".join(saida)


def palavras(texto):
    """Conta palavras do Markdown, ignorando comentarios, marcadores e URLs."""
    limpo = _LINK.sub(r"\1", _COMENTARIO.sub("", texto))
    limpo = re.sub(r"[#>*_`\-]", " ", limpo)
    return len(limpo.split())


def minutos(texto, por_minuto=220):
    """Tempo de leitura em minutos, no minimo 1."""
    return max(1, round(palavras(texto) / por_minuto))
