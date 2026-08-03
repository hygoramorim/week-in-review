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

index.html                   GERADO (edição mais recente)
arquivo.html                 GERADO (índice de todas as edições)
editions/AAAA-MM-DD/         GERADO: index.html + uma página por artigo
podcast/AAAA-MM-DD-brief.md  GERADO: o resumo que alimenta o NotebookLM
podcast/audio/AAAA-MM-DD.mp3 GERADO, committed: o episódio, retenção de 3 (poda a cada build)
assets/revista.css           folha de estilo única, compartilhada por todas as páginas, mobile-first
tools/build.py               o build (player de áudio + poda de mp3 antigos)
tools/markdown_min.py        renderizador de Markdown sem dependência externa
tools/vault_intake.py        monta content/AAAA-MM-DD/ a partir das 5 transcrições mais recentes do Vault
tools/notebooklm_bridge.py   gera e baixa o episódio no NotebookLM, grava podcast_audio
tools/pipeline.md            o roteiro do pipeline semanal (o que o cron executa via claude -p)
tools/sexta.sh               wrapper do cron: roda tools/pipeline.md toda sexta
```

Nunca edite `index.html`, `arquivo.html`, `editions/` ou `podcast/` diretamente:
o próximo `./publicar.sh` apaga a alteração.

**CSS (mobile-first):** o editorial e os artigos vêm de markdown, então emitem
`h1..h3` crus. Nunca estilize tags soltas (`h1{...}`) com tamanhos display: escope
por classe (`.hero h1`, `.artigo-head h1`), senão o estilo vaza pro título do
editorial e o sobrepõe (já aconteceu, ver [docs/APRENDIZADOS.md](docs/APRENDIZADOS.md)).
Ao mexer no CSS, cheque o editorial em desktop E mobile antes de publicar.

## Comandos

```bash
./publicar.sh              # build + commit + push
./publicar.sh --check      # só valida content/, não escreve nada
python3 tools/build.py     # só o build, sem git
python3 -m http.server 8000   # ver em http://localhost:8000 antes de publicar
```

Sem dependências além do `python3` do sistema. Não instale nada.

## A rotina da semana

Roda sozinha toda sexta às 15h30 no Mac Mini via `tools/sexta.sh` (cron).

Manual, se precisar rodar fora do horário ou depurar um passo:

1. `python3 tools/vault_intake.py` monta `content/AAAA-MM-DD/` com as 5
   transcrições mais recentes do Vault.
2. Escrever os artigos (e `editorial.md`) a partir das transcrições apontadas.
3. `python3 tools/build.py` gera o brief.
4. `python3 tools/notebooklm_bridge.py AAAA-MM-DD` gera e baixa o episódio.
5. `python3 tools/build.py` de novo, agora com o player de áudio.
6. `./publicar.sh`.

O jeito mais rápido de começar uma edição sem o `vault_intake.py` é copiar a
pasta da anterior e substituir o conteúdo: a forma do `edicao.json` já está certa.

## Como escrever os artigos

- **Alvo: 1.000 a 1.200 palavras** (~5 min de leitura).
- A primeira linha do `.md` é `# Título`: vira o título da página.
- Abaixo de **200 palavras** o artigo conta como rascunho: o botão "Leia o artigo"
  não aparece no card e a página mostra um aviso. É assim que se controla o que
  já está pronto para publicar.
- O texto é **análise e síntese** a partir da transcrição, com tese própria.
  Nunca a transcrição reescrita ou parafraseada de ponta a ponta: o site é
  público e as fontes são de terceiros.
- Markdown suportado: `#` a `###`, parágrafos, `**negrito**`, `*itálico*`,
  `[link](url)`, `` `código` ``, `>` citação, listas `-` e `1.`, `---`.
  Comentários `<!-- -->` são descartados na renderização.

## Regras editoriais

- **Nenhuma imagem gerada por IA.** Thumbnails oficiais do YouTube ou bancos com
  crédito (Unsplash). O crédito vai em `credito` no `edicao.json`.
- Todo conteúdo leva pelo menos um link para a fonte original em `links`.
- O campo `porque` é o "Por que importa" (a consequência prática, não o resumo).

## O podcast

O build gera `podcast/AAAA-MM-DD-brief.md`: direção de roteiro (25 min, todos os
conteúdos, orçamento de minutos por bloco, tom), a carta editorial, e para cada
conteúdo o resumo, o "por que importa" e o artigo completo quando pronto.

A ponte com o NotebookLM está **implementada**: `tools/notebooklm_bridge.py` usa
a CLI `notebooklm` (pacote `notebooklm-py`, precisa estar logada: `notebooklm
login`) para criar um notebook novo a cada semana (nome `week in review DD MM AA`),
adicionar o brief da semana como fonte, gerar o áudio em pt-BR limitado àquela
fonte (`-s <source_id>`), baixar o mp3 para `podcast/audio/` e gravar o campo
`podcast_audio` em `edicao.json`. A partir daí o build embute um player na
página da edição automaticamente.

**CRÍTICO:** o brief é enviado com `--type file` (o CLI lê o arquivo e manda o
conteúdo). NUNCA `--type text`, que trata o argumento como texto literal e faz o
caminho do arquivo virar a "fonte", gerando um podcast vazio. Há teste travando
isso. Idioma é `pt_BR` (underscore). A geração de áudio tem cota diária no Google.
Lições completas em [docs/APRENDIZADOS.md](docs/APRENDIZADOS.md).

O mp3 fica hospedado no próprio repo (`podcast/audio/AAAA-MM-DD.mp3`,
committed), com retenção de 3 episódios: a cada `build.py`, os mais antigos
são apagados.

**Auth do NotebookLM (master token, não precisa relogar):** desde 2026-08-03 a
auth usa **master token** na conta Oz `hygor@ozprodutora.com.br`, com o CLI
`notebooklm-py` **0.8.0** (extra `[headless]`). É uma credencial durável (vale
meses) que re-minta a sessão sozinha, sem navegador, quando os cookies expiram.
O pipeline de sexta não precisa mais de relogin manual.

O token vive em `~/.notebooklm/profiles/default/master_token.json` (`0600`,
**nunca committar nem logar**, é credencial de conta inteira). Forçar re-mint na
mão (sem browser): `notebooklm login --master-token-refresh`. Confirmar com
`notebooklm list`. Se um dia o token parar (raro), refazer o bootstrap:
`cd ~/projetos/notebooklm-skill && .venv/bin/python -m notebooklm login
--master-token --account hygor@ozprodutora.com.br` (abre o navegador uma vez).
O `tools/checar_auth.py` (cron de quinta 10h) segue como rede de segurança e
avisa no Telegram se a sessão cair mesmo assim.

## Onde as coisas rodam

- **MacBook Air:** edição do projeto, build, publicação. Não tem o Vault.
- **Mac Mini:** tem o Vault do Obsidian, a CLI `notebooklm` autenticada e o
  cron do pipeline semanal (`tools/sexta.sh`, sexta às 15h30, chamando
  `claude -p` com `tools/pipeline.md`). É onde os artigos podem ser escritos
  com acesso direto às transcrições e onde o episódio é gerado e baixado.

O git é o que sincroniza os dois. Antes de começar em qualquer máquina: `git pull`.

## Segurança do cron

`tools/sexta.sh` roda o pipeline via `claude -p` sem supervisão, então NÃO usa
`--permission-mode bypassPermissions` (libera comando demais). Usa `acceptEdits`
mais uma allowlist estrita via `--allowedTools` (só `git`, `python3`,
`notebooklm`, e as ferramentas de arquivo) e `--add-dir` apontando só para o
Vault. No modo `--ensaio`, o `publicar.sh` fica fora da allowlist, então é
impossível publicar durante um teste. Ao mexer no `sexta.sh`, preserve isso.
