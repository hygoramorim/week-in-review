# Week In Review

Revista semanal escrita a partir das transcrições que entram no Vault do Obsidian.
Site estático publicado no GitHub Pages: **https://hygoramorim.github.io/week-in-review/**
Repositório: `hygoramorim/week-in-review`. Autor: Hygor Beltrão Amorim.

## A regra que importa mais

`content/` é a fonte. **Todo o resto é gerado e sobrescrito pelo build.**

```
content/AAAA-MM-DD/          ← EDITE AQUI
  edicao.json                metadados: capa, signals, os 5 conteúdos, links
  editorial.md               a carta editorial
  artigos/<slug>.md          um artigo por conteúdo, ~1.100 palavras

transcricoes/                fonte bruta do Vault. Fora do git, nunca publicada.

index.html                   GERADO — edição mais recente
arquivo.html                 GERADO — índice de todas as edições
editions/AAAA-MM-DD/         GERADO — index.html + uma página por artigo
podcast/AAAA-MM-DD-brief.md  GERADO — o resumo que alimenta o NotebookLM
assets/revista.css           folha de estilo única, compartilhada por todas as páginas
tools/build.py               o build
tools/markdown_min.py        renderizador de Markdown sem dependência externa
```

Nunca edite `index.html`, `arquivo.html`, `editions/` ou `podcast/` diretamente —
o próximo `./publicar.sh` apaga a alteração.

## Comandos

```bash
./publicar.sh              # build + commit + push
./publicar.sh --check      # só valida content/, não escreve nada
python3 tools/build.py     # só o build, sem git
python3 -m http.server 8000   # ver em http://localhost:8000 antes de publicar
```

Sem dependências além do `python3` do sistema. Não instale nada.

## A rotina da semana

1. As transcrições novas chegam no Vault (`Estudos/<Canal>/YouTube/AAAA-MM-DD...`).
2. Criar `content/AAAA-MM-DD/` com `edicao.json`, `editorial.md` e os artigos.
3. Escrever cada artigo a partir da transcrição correspondente.
4. `./publicar.sh`.
5. Mandar `podcast/AAAA-MM-DD-brief.md` para o NotebookLM gerar o episódio.

O jeito mais rápido de começar uma edição é copiar a pasta da anterior e
substituir o conteúdo — a forma do `edicao.json` já está certa.

## Como escrever os artigos

- **Alvo: 1.000 a 1.200 palavras** (~5 min de leitura).
- A primeira linha do `.md` é `# Título` — vira o título da página.
- Abaixo de **200 palavras** o artigo conta como rascunho: o botão "Leia o artigo"
  não aparece no card e a página mostra um aviso. É assim que se controla o que
  já está pronto para publicar.
- O texto é **análise e síntese** a partir da transcrição, com tese própria.
  Nunca a transcrição reescrita ou parafraseada de ponta a ponta — o site é
  público e as fontes são de terceiros.
- Markdown suportado: `#` a `###`, parágrafos, `**negrito**`, `*itálico*`,
  `[link](url)`, `` `código` ``, `>` citação, listas `-` e `1.`, `---`.
  Comentários `<!-- -->` são descartados na renderização.

## Regras editoriais

- **Nenhuma imagem gerada por IA.** Thumbnails oficiais do YouTube ou bancos com
  crédito (Unsplash). O crédito vai em `credito` no `edicao.json`.
- Todo conteúdo leva pelo menos um link para a fonte original em `links`.
- O campo `porque` é o "Por que importa" — a consequência prática, não o resumo.

## O podcast

O build gera `podcast/AAAA-MM-DD-brief.md`: direção de roteiro (25 min, todos os
conteúdos, orçamento de minutos por bloco, tom), a carta editorial, e para cada
conteúdo o resumo, o "por que importa" e o artigo completo quando pronto.

Esse arquivo é o payload. O sistema que conversa com o NotebookLM Studio roda no
**Mac Mini** e é ele quem envia o brief e gera o episódio — não existe API pública
do NotebookLM para isso, então a ponte é o sistema local.

## Onde as coisas rodam

- **MacBook Air:** edição do projeto, build, publicação. Não tem o Vault.
- **Mac Mini:** tem o Vault do Obsidian e o sistema que fala com o NotebookLM.
  É onde a integração do podcast é implementada e onde os artigos podem ser
  escritos com acesso direto às transcrições.

O git é o que sincroniza os dois. Antes de começar em qualquer máquina: `git pull`.
