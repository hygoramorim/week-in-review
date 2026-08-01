Execute o pipeline semanal da Week In Review, nesta ordem, parando e reportando se algum passo falhar:

1. `git pull` no repositório.
2. `python3 tools/vault_intake.py` para montar `content/<data>/` com as 5 transcrições mais recentes. Se a pasta já existir, pare e reporte (não use --force sem eu pedir).
3. Para cada item em `content/<data>/edicao.json`, leia a transcrição apontada em `transcricao` (arquivo grande: leia em subagente, nunca a nota inteira no contexto principal) e escreva o artigo em `content/<data>/artigos/<slug>.md`: análise e síntese com tese própria, 1.000 a 1.200 palavras, nunca paráfrase da fonte, sem travessão. Preencha também `resumo`, `porque`, `tags`, `dek`, `pills`, `capa` e `editorial.md`.
4. `python3 tools/build.py` para gerar o brief.
5. `python3 tools/notebooklm_bridge.py <data>` para gerar e baixar o mp3 e gravar `podcast_audio`.
6. `python3 tools/build.py` de novo (agora com o player), a poda dos 3 mp3 roda aqui.
7. `./publicar.sh` para commitar e publicar. Reporte o link de preview.

Regras: sem citar Claude no conteúdo nem nos commits. Conventional Commits. Se o NotebookLM falhar por auth, pare e avise para rodar `notebooklm login`.
