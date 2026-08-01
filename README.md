# Week In Review

Revista semanal montada a partir das transcrições que entram no Vault do Obsidian.
No ar em **https://hygoramorim.github.io/week-in-review/**

## Estrutura

```
index.html            edição atual (é o que abre na home)
arquivo.html          índice de todas as edições — GERADO, não editar à mão
editions/
  2026-07-31.html     cópias arquivadas, uma por semana
publicar.sh           arquiva + commita + publica
tools/arquivo.py      gerador do arquivo.html
.nojekyll             o GitHub serve o HTML cru, sem passar pelo Jekyll
```

## Rotina de sexta

1. Escreva a nova edição direto no `index.html`.
   Atualize a data na barra superior (`<div class="right">`) e o número em
   `<span class="pill">Issue 00N</span>` — o gerador lê esses dois campos.
2. Rode:

   ```bash
   ./publicar.sh
   ```

   Isso copia o `index.html` para `editions/AAAA-MM-DD.html`, regenera o
   `arquivo.html` com a edição nova no topo, commita e dá push.
   O Pages republica em cerca de um minuto.

Se a data da barra superior estiver errada ou você quiser forçar outra:

```bash
./publicar.sh 2026-08-07
```

## Comandos avulsos

```bash
python3 tools/arquivo.py build      # só regenera arquivo.html
python3 tools/arquivo.py arquivar   # só arquiva o index atual
python3 tools/arquivo.py data       # mostra a data lida do index.html
```

## Ver localmente antes de publicar

```bash
python3 -m http.server 8000
# abre http://localhost:8000
```

## Regras da publicação

- Nenhuma imagem gerada por IA. Thumbnails oficiais do YouTube e bancos com
  crédito (Unsplash) — o crédito vai no `<span class="credit">`.
- Todo destaque leva pelo menos um link para a fonte original.
