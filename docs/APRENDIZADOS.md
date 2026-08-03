# Aprendizados do projeto

Registro vivo das lições que custaram tempo ou quase quebraram algo. A ideia é
que cada tropeço vire uma linha aqui, para o projeto evoluir sem repetir erro.
Acrescente ao final quando aprender algo novo, com a data.

Formato de cada item: **o que aconteceu**, **por que**, **como evitar/o que fazer**.

---

## Vault e transcrições

- **As transcrições no disco são YAML, não JSON** (2026-08-01). O plano original
  assumiu JSON e o intake quebrava silenciosamente (tratava toda nota como sem
  data). O MCP `obsidian-vault` devolve a nota como JSON, mas o arquivo no disco
  usa frontmatter YAML (`--- ... ---`). `tools/vault_intake.py` parseia os dois.
  Ao mexer no parser, mantenha os dois formatos.

- **Transcrições são grandes** (ate ~100k chars). Ao escrever artigos a partir
  delas, leia em subagente/fatia, nunca a nota inteira no contexto principal.

## NotebookLM (o que mais deu trabalho)

- **Auth durável: master token, não cookies de navegador** (2026-08-03). O modo
  `--browser-cookies` (cookies do Chrome) caduca em POUCAS HORAS, então o login
  vivia expirando e o pipeline de sexta corria risco de sair sem podcast. A
  solução certa (o que o Hygor lembrava de outra integração): **master token**,
  o modo de auth do `notebooklm-py` feito pra servidor/CI. Uma credencial durável
  (vale meses) que re-minta os cookies sozinha, sem navegador. Requer CLI 0.8.0
  com o extra `[headless]`. Setup (uma vez, abre o browser):
  `notebooklm login --master-token --account <conta>`. Re-mint manual sem browser:
  `notebooklm login --master-token-refresh`. Vive em
  `~/.notebooklm/profiles/default/master_token.json` (0600). CUIDADO: é credencial
  de conta INTEIRA ("infostealer-grade"), a doc recomenda conta dedicada; usamos
  a Oz por escolha consciente (praticidade + cota). Nunca committar/logar o token.

- **Upgrade 0.7.x -> 0.8.0 é seguro pra quem usa o CLI por subprocess** (2026-08-03).
  O guia `upgrading-to-0.8.0.md` lista muitas quebras, mas TODAS são na API Python
  (`.get()` que agora levanta, `.share()` removido etc.). Nosso `notebooklm_bridge.py`
  chama o CLI por subprocess (`source add --type file --json`, `generate audio
  --language pt_BR --wait -s`, `delete -n -y`), e esses flags não mudaram. Os 19
  testes passaram após o upgrade. Regra: ao subir versão do CLI, rodar
  `python3 -m unittest discover -s tests` antes de confiar.

- **Manter o CLI atualizado** (2026-08-02). O `notebooklm-py` 0.3.4 não reconhecia
  o NotebookLM renomeado pelo Google (a URL perdeu o "lm", virou
  `notebook.google.com`). Sintoma: login salva cookies mas `list` dá
  "Authentication expired". NÃO era a conta nem o timing do login. Correção:
  atualizar o CLI (0.7.3+). Se auth falhar de novo depois de um login limpo,
  suspeite da versão antes de qualquer outra coisa.

- **A fonte do podcast precisa de `--type file`, NUNCA `--type text`** (2026-08-02).
  Este foi o pior: os episódios saíam vazios/incoerentes porque a "fonte" enviada
  ao NotebookLM era o CAMINHO do arquivo (83 chars), não o conteúdo. Com
  `--type text` o CLI trata o argumento como texto literal; com `--type file` ele
  LÊ o arquivo e envia os 46KB do brief. Há um teste que trava isso em
  `tests/test_notebooklm_bridge.py`. Para conferir o que entrou de verdade:
  `notebooklm source fulltext <src> -n <nb> -o /tmp/x.txt` e olhe o tamanho.

- **O `--json` do 0.7.x aninha o resultado**: `{"notebook": {"id": ...}}`,
  `{"source": {"id": ...}}`. O `_extrair_id` em `notebooklm_bridge.py` cobre
  aninhado e plano. `delete` virou `notebooklm delete -n <id> -y` (não posicional).

- **Código de idioma é `pt_BR` (underscore), não `pt-BR`** no 0.7.x
  (`notebooklm language list` para conferir).

- **Cota diária de geração de áudio** (2026-08-02). O Google limita gerações de
  Audio Overview por dia ("Audio generation rate limited... try again in 1-24h").
  Gerar várias edições no mesmo dia estoura. Não é bug: espaçar, ou usar `--retry`.
  Sintoma alternativo do mesmo limite: o artefato "disappeared from list /
  treating as removed" durante o `--wait` (não é erro de rede, é a cota).

- **Colisão de nome ao rebaixar o mp3 por cima do antigo** (2026-08-02). Ao
  regerar o áudio de uma edição cujo mp3 antigo ainda existia em `podcast/audio/`,
  o download do NotebookLM salvou como `AAAA-MM-DD (2).mp3` em vez de sobrescrever.
  O `edicao.json` seguia apontando pro nome sem `(2)`, ou seja, pro áudio VELHO
  (bugado). Aconteceu nas duas edições (002 e 003). Sintoma: publica "com sucesso"
  mas o player toca o áudio antigo; um `(2).mp3` sobra na pasta. Correção manual:
  `mv -f "podcast/audio/AAAA-MM-DD (2).mp3" "podcast/audio/AAAA-MM-DD.mp3"`,
  rebuild, republicar. A fazer: o `notebooklm_bridge.py` devia apagar o mp3
  antigo da mesma data antes de baixar (ou baixar pra nome temporário e mover por
  cima), pra nunca gerar o `(2)`.

- **A sessão do NotebookLM expira no meio de um batch** (2026-08-02). Ao regerar
  os dois áudios em sequência, o primeiro (003) passou e o segundo (002) falhou
  com "Authentication expired or invalid. Redirected to accounts.google.com". Não
  é bug de conteúdo nem cota: a sessão (cookies do Chrome) caducou entre uma
  geração e outra. Login via `--browser-cookies` dura pouco. Como destravar:
  `cd ~/projetos/notebooklm-skill && .venv/bin/python -m notebooklm login
  --browser-cookies chrome --account hygor@ozprodutora.com.br`, conferir com
  `notebooklm list`. Regra prática: antes de um batch, rodar `notebooklm list`
  para validar a sessão; e não confiar que ela sobrevive a várias gerações
  seguidas com esperas longas.

## Fluxo de edição

- **Subagente pode falhar silenciosamente: confira o ARQUIVO no disco, não o texto de retorno** (2026-08-03). Ao escrever os 5 artigos da Issue 004 em paralelo (um subagente por vídeo), um deles retornou em ~8s com 0 tool_uses e um texto corrompido, sem ter escrito o arquivo. Os outros 4 escreveram de verdade. Regra: depois de fan-out de subagentes que escrevem arquivos, SEMPRE validar no disco (`ls`, `wc -w`, primeira linha = `# Titulo`, grep de travessão) antes de montar o edicao.json. Não confiar no JSON/resumo que o agente devolve. O que falhou foi refeito à mão (transcrição pequena, mais rápido que respawnar).

- **Anti-repetição e filtro temático: por ID de vídeo, e data pelo NOME do arquivo** (2026-08-03). Para a "edição extra" (5 vídeos novos de IA/Filosofia/Liderança, sem repetir os já usados): a chave confiável de repetição é o `video_id` (11 chars), extraído do frontmatter ou do link, comparado com os IDs já em `content/*/edicao.json` (campo `imagem`, `/vi/<id>/`). CUIDADO: `find -mtime -7` traz milhares de arquivos (mtime é toque no disco, não data do vídeo) e há CÓPIAS do mesmo vídeo com datas diferentes no nome (original 2021/2023 e republicação 2026). A data de "últimos 7 dias" tem que sair do NOME do arquivo (`AAAA-MM-DD - Titulo.md`), não do mtime. O intake não faz nada disso: é processo manual (curadoria + aprovação do Hygor antes de escrever).


- **Edição retroativa (fora da mais recente) não é suportada pelo intake**
  (2026-08-02). `vault_intake.py` só pega as 5 MAIS recentes. Montar uma edição
  de conteúdo antigo exige processo manual. CUIDADO: a data da edição vira o nome
  da pasta em `content/`; se colidir com uma edição existente, o `--force`
  SOBRESCREVE (já quase destruiu uma edição publicada, recuperada do git). Ao
  montar manual, force uma data que não colida e trave contra sobrescrita.

- **`--force` do intake acumula órfãos** se não limpar a pasta `artigos/` antes de
  remontar (corrigido: agora limpa). O build só lê os artigos referenciados no
  `edicao.json`, mas órfãos poluem o repo.

## Segurança e operação

- **Cron nunca com `bypassPermissions`** (2026-08-02). Security review reprovou.
  `sexta.sh` usa allowlist estrita (`--allowedTools`) + `--add-dir` só no Vault.
  No `--ensaio`, `publicar.sh` fica fora da allowlist (publicar impossível no teste).

- **Loops de sessão morrem quando o terminal fecha.** Regenerações agendadas via
  `/loop` só rodam com a sessão aberta. Para algo durável, o cron do Mac Mini ou
  `/schedule` (nuvem).

## Ideias de evolução (backlog)

- Suporte nativo a edição retroativa no `vault_intake.py` (flag `--desde <data>`
  ou `--pular N`), com trava anti-colisão de data embutida.
- Curadoria: hoje pega as 5 mais recentes cegamente; poderia deixar o Hygor
  aprovar/trocar antes de montar.
- Regerar podcast de uma edição existente sem remexer no conteúdo (subcomando).
- Verificação automática de que a fonte do NotebookLM tem o conteúdo esperado
  (comparar tamanho do fulltext com o brief) antes de gastar uma geração de áudio.
