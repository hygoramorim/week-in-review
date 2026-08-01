# Week In Review

Revista semanal montada a partir das transcrições que entram no Vault do Obsidian.
No ar em **https://hygoramorim.github.io/week-in-review/**

Cada edição traz cinco conteúdos. Cada conteúdo tem um card na home e um artigo
próprio de ~1.100 palavras, aberto pelo botão **Leia o artigo**.

## Como funciona

Você escreve Markdown em `content/`. Um script gera todo o HTML.

```
content/2026-07-31/
  edicao.json        capa, signals, os 5 conteúdos, tags e links
  editorial.md       a carta editorial
  artigos/
    sam-harris.md    ~1.100 palavras, ~5 min de leitura
    ratos-de-ia.md
```

```bash
./publicar.sh
```

Isso constrói `index.html`, `arquivo.html`, `editions/2026-07-31/` com uma página
por artigo, e `podcast/2026-07-31-brief.md`: depois commita e publica.
O Pages republica em cerca de um minuto.

**Nada fora de `content/` deve ser editado à mão.** O build sobrescreve.

## Rotina da semana

Roda sozinha toda sexta às 15h30 no Mac Mini, via cron (`tools/sexta.sh`).

Manual, se precisar montar uma edição na mão:

1. Copie a pasta da edição anterior em `content/` e renomeie para a data nova
   (ou rode `python3 tools/vault_intake.py` para montar o esqueleto a partir
   das 5 transcrições mais recentes do Vault).
2. Atualize `edicao.json` e `editorial.md`.
3. Escreva os cinco artigos a partir das transcrições.
4. `./publicar.sh`
5. Rode `python3 tools/notebooklm_bridge.py AAAA-MM-DD` para gerar o episódio.

Um artigo com menos de 200 palavras conta como rascunho: o botão "Leia o artigo"
não aparece e a página mostra um aviso. É o controle de o que já está publicável.

## Comandos

```bash
./publicar.sh --check          # valida content/ sem escrever nem publicar
python3 tools/build.py         # só o build, sem git
python3 -m http.server 8000    # ver em http://localhost:8000
```

Só precisa do `python3` do sistema. Nenhuma dependência para instalar.

## Podcast

O build gera um resumo da edição em `podcast/AAAA-MM-DD-brief.md`, já com a
direção de roteiro: 25 minutos, todos os conteúdos, orçamento de minutos por
bloco e tom. Esse arquivo é o que vai para o NotebookLM.

A ponte automática (`tools/notebooklm_bridge.py`) roda no Mac Mini usando a
CLI do NotebookLM: ela gera o episódio em pt-BR a partir do brief, baixa o mp3
para `podcast/audio/` e grava o campo `podcast_audio` em `edicao.json`. Quando
esse campo existe, o build embute um player de áudio na página da edição.
O mp3 fica versionado no próprio repo, com retenção dos 3 episódios mais
recentes (os antigos são apagados a cada build).

## Regras editoriais

- Nenhuma imagem gerada por IA: thumbnails oficiais ou bancos com crédito.
- Todo conteúdo leva pelo menos um link para a fonte original.
- Artigo é análise e síntese a partir da transcrição, com tese própria, nunca a
  transcrição reescrita.

Detalhes de arquitetura e convenções: [CLAUDE.md](CLAUDE.md).
