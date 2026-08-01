# Week In Review, automação de Vault e podcast

Data: 2026-08-01
Autor: Hygor Beltrão Amorim

## Problema

O site estático (content → build.py → GitHub Pages) já está pronto e funcional.
Faltam os dois pedaços que o CLAUDE.md descreve como pendentes e locais:

1. **Acesso ao Vault**: hoje a montagem de `content/AAAA-MM-DD/` é 100% manual.
2. **Geração do podcast no NotebookLM**: o build gera o brief, mas nada envia ao
   NotebookLM nem publica o áudio.

Além disso, o Hygor quer que a rotina rode **sozinha toda sexta às 15h30**, quando
as transcrições automáticas da semana já entraram no Vault.

## Conexões verificadas (2026-08-01)

- **Vault** (MCP obsidian-vault): lista `Estudos/<Canal>/YouTube/` e lê transcrições
  completas. Cada nota tem frontmatter JSON: `video_id`, `url`, `date`, `channel`,
  `title`, `duration`, `tags`. Transcrições são grandes (~100k chars / ~25k tokens).
- **NotebookLM**: CLI `notebooklm-py` v0.3.4 instalada e autenticada
  (`~/.notebooklm/storage_state.json`, 17 cookies, `auth check` passa). Ainda não
  existe notebook "Week In Review" — será criado no primeiro run.

## Decisões (do brainstorming)

- Podcast: **notebook fixo** "Week In Review", as fontes (briefs) acumulam.
- Artefato: **só o mp3**, baixado localmente, com **player embutido na newsletter**.
- Hosting do mp3: **no próprio repo** (GitHub Pages), com **retenção dos 3 mais
  recentes** — o build apaga os antigos.
- Seleção da edição: **as 5 transcrições mais recentes** de qualquer canal.
- Conteúdo: além do esqueleto, **um texto de ~5 min por vídeo** (1.000–1.200
  palavras), análise/síntese, nunca paráfrase. Escrito por Claude na sessão.
- Agendamento: **pipeline completo automático**, **sexta 15h30**, no **Mac Mini**
  (que tem Vault + NotebookLM), via cron local chamando `claude -p`.

## Arquitetura, 4 peças isoladas

Tudo se pluga em `content/` + `build.py`. Sem dependências novas de Python além do
que a CLI do NotebookLM já traz. Nenhuma chave de API embutida no repo.

### Peça 1 — `tools/vault_intake.py`

Monta o esqueleto de uma edição a partir do Vault.

- Entrada: caminho do Vault (constante `VAULT` no topo, default no vault do Hygor;
  sobrescrevível por env `WIR_VAULT`).
- Varre `Estudos/*/YouTube/*.md`, lê o frontmatter JSON de cada nota, ordena por
  `date` (ignora `0000-00-00`), pega as **5 mais recentes**.
- Cria `content/AAAA-MM-DD/` (data = da transcrição mais nova):
  - `edicao.json`: para cada item preenche `slug` (do título), `numero`, `fonte`
    (channel), `titulo`/`resumo`/`porque`/`tags` como placeholders a preencher,
    `imagem` = `https://img.youtube.com/vi/<video_id>/hqdefault.jpg`,
    `transcricao` = caminho real no Vault, `links` = `[Watch <url>]`.
    Número da issue = maior issue existente em `content/` + 1.
  - `editorial.md`: placeholder.
  - `artigos/<slug>.md`: placeholder com `# <titulo>` só.
- Idempotente: se `content/AAAA-MM-DD/` já existe, não sobrescreve (avisa e sai 0),
  a menos que rode com `--force`.
- Modo `--dry-run`: imprime as 5 escolhidas sem escrever.
- Saída em stdout: JSON com a lista de itens (slug, fonte, caminho da transcrição)
  para o passo de redação consumir.

O script **só faz mecânica** (ler arquivos, montar JSON). A redação dos artigos e
do editorial é feita por Claude, lendo cada transcrição em subagente (por serem
grandes) e gravando os `.md`. Isso mantém "sem dependências além do python3".

### Peça 2 — player de áudio, muda `build.py` + `assets/revista.css`

- `edicao.json` ganha campo **opcional** `podcast_audio` (ex. `"2026-07-31.mp3"`).
- Quando presente, `render_edicao` insere `<audio controls>` logo abaixo do hero,
  na home e na página da edição. `src` relativo a `podcast/audio/<arquivo>`.
- Ausente → nada renderiza. Edições antigas seguem válidas.
- mp3 mora em `podcast/audio/AAAA-MM-DD.mp3`, commitado.
- `podar_audio()` no fim de `build()`: lista `podcast/audio/*.mp3`, ordena por data
  no nome, **apaga além dos 3 mais recentes**, e loga cada arquivo removido
  (sem corte silencioso). `git add -A` no publicar.sh remove do repo.
- `.gitignore`: garantir que `podcast/audio/` NÃO está ignorado.

### Peça 3 — `tools/notebooklm_bridge.py`

Orquestra a CLI do NotebookLM. Recebe a data da edição.

1. Acha o notebook "Week In Review" por título (`notebooklm list --json`); se não
   existe, cria (`notebooklm create`).
2. Adiciona `podcast/AAAA-MM-DD-brief.md` como fonte
   (`notebooklm source add --notebook <id>`).
3. Define idioma pt-BR e gera o Audio Overview
   (`notebooklm generate audio --notebook <id>`), aguarda
   (`notebooklm artifact wait -n <id>`).
4. Baixa o mp3 (`notebooklm download ... -n <id>`) para
   `podcast/audio/AAAA-MM-DD.mp3`.
5. Escreve `podcast_audio` no `edicao.json` da edição.
6. Não publica — quem publica é o pipeline/publicar.sh.

Sempre usa `--notebook <id>` explícito (regra de paralelismo da skill). Comandos
`generate`/`download` pedem confirmação por padrão na skill; no pipeline headless
rodam com as flags equivalentes de auto-confirmação. Erros de auth → falha clara
pedindo `notebooklm login`.

### Peça 4 — agendamento, `tools/sexta.sh` + `tools/pipeline.md` + cron

- `tools/pipeline.md`: o roteiro que o agente headless segue (os 7 passos).
- `tools/sexta.sh`: wrapper que faz `cd` no repo, `git pull`, e chama
  `claude -p "$(cat tools/pipeline.md)"` com permissões adequadas, logando em
  `~/Library/Logs/week-in-review-sexta.log`.
- Linha de cron (documentada, ativada pelo Hygor no Mini):
  `30 15 * * 5 /caminho/week-in-review/tools/sexta.sh`
- Pipeline completo: pull → vault_intake → escrever 5 artigos + editorial →
  build (gera brief) → notebooklm_bridge (mp3 + podcast_audio) → build (player +
  poda) → publicar.sh.

## Fluxo de dados

```
Vault (Estudos/*/YouTube/*.md, fm JSON)
   │  vault_intake.py
   ▼
content/AAAA-MM-DD/{edicao.json, editorial.md, artigos/*.md}
   │  Claude escreve os artigos + editorial (lê transcrições em subagente)
   ▼
build.py ──► podcast/AAAA-MM-DD-brief.md
   │  notebooklm_bridge.py (CLI NotebookLM)
   ▼
podcast/audio/AAAA-MM-DD.mp3  +  edicao.json.podcast_audio
   │  build.py (player + poda 3 mais recentes)
   ▼
index.html / editions/ (com <audio>)  ──► publicar.sh ──► GitHub Pages
```

## Ordem de implementação

1. Peça 2 (player + retenção) — testável no Air agora.
2. Peça 1 (vault_intake.py) — testável contra o Vault real no Air.
3. Peça 3 (notebooklm_bridge.py) — mecânica pronta; execução real no pipeline/Mini.
4. Peça 4 (sexta.sh + pipeline.md + cron doc) — costura.

O que se valida no Air: 1 e 2 (build + Vault). NotebookLM ponta-a-ponta e cron:
validação no Mac Mini.

## Testes

- Peça 2: rodar `build.py` com e sem `podcast_audio` no JSON; conferir `<audio>`
  presente/ausente; criar 4 mp3s falsos e conferir que a poda deixa 3.
- Peça 1: `--dry-run` lista as 5 corretas; run real cria `content/` válido que
  passa em `build.py --check`; `--force` e idempotência.
- Peça 3: dry-run que só resolve/cria o notebook e lista fontes, sem gerar áudio,
  para validar auth e o id, antes de gastar uma geração real.
- Peça 4: `sexta.sh` roda o pipeline num clone de teste sem publicar (flag de
  ensaio) antes de ligar o cron.

## Fora de escopo (YAGNI)

- Hosting externo do mp3 (Vercel Blob).
- Outros artefatos do NotebookLM (slides, quiz, relatório).
- Geração de artigo por API paga própria.
- Aprovação manual antes de publicar (o Hygor escolheu publicar direto).

## Riscos e mitigação

- **Notebook fixo acumula fontes sem limite**: aceitável por ora; se virar
  problema, adicionar poda de fontes antigas no bridge (fora de escopo agora).
- **Transcrição grande estoura contexto**: ler por subagente/fatia; nunca a nota
  inteira no contexto principal.
- **Cron depende do Mini ligado às sextas 15h30**: aceito pelo Hygor.
- **`claude -p` headless precisa da skill notebooklm e do MCP do Vault no Mini**:
  ambos já existem na máquina do Hygor; validar no primeiro ensaio.
