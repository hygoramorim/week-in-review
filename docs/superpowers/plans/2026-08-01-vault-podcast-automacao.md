# Automação de Vault e Podcast — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar as duas frentes pendentes do CLAUDE.md — acesso ao Vault e geração do podcast no NotebookLM — com player de áudio na newsletter e um pipeline que roda sozinho toda sexta 15h30 no Mac Mini.

**Architecture:** Tudo se pluga no fluxo existente `content/ → build.py → GitHub Pages`. Três scripts Python novos em `tools/` (intake do Vault, ponte do NotebookLM) mais mudanças cirúrgicas em `build.py`/`revista.css` para o player. Um wrapper de shell + roteiro Markdown costuram o pipeline sob cron. A redação dos artigos é feita por Claude na execução; os scripts fazem só a mecânica repetível.

**Tech Stack:** Python 3 do sistema (sem pip), CLI `notebooklm-py` v0.3.4 (já instalada e autenticada), bash/cron, MCP obsidian-vault para leitura das transcrições na hora da redação.

## Global Constraints

- **Sem dependências novas de Python.** Só a stdlib e o `python3` do sistema. (CLAUDE.md do repo: "Não instale nada.")
- **`content/` é a única fonte editável.** `index.html`, `arquivo.html`, `editions/`, `podcast/` são gerados e sobrescritos pelo build.
- **Nenhuma imagem gerada por IA.** Thumbnails oficiais do YouTube (`img.youtube.com/vi/<video_id>/hqdefault.jpg`) ou bancos com crédito.
- **Artigo é análise/síntese com tese própria, nunca paráfrase da transcrição.** Alvo 1.000–1.200 palavras (~5 min). Abaixo de 200 palavras conta como rascunho.
- **Sem travessão (— em-dash) em texto de saída.** Vírgula, parênteses, dois-pontos ou ponto.
- **Não citar Claude no conteúdo entregue. Sem `Co-Authored-By: Claude` nos commits.**
- **Commits em Conventional Commits** (`feat(escopo):`, `fix:`, `docs:`, `chore:`).
- **mp3 mora em `podcast/audio/AAAA-MM-DD.mp3`**, commitado, retenção dos **3 mais recentes**.
- **Notebook fixo** "Week In Review", fontes acumulam; geração de áudio limitada à fonte da semana via `-s <source_id>`.
- **Nenhuma chave/segredo no repo.** A auth do NotebookLM vive em `~/.notebooklm/`.

## Estrutura de arquivos

- Create `tools/vault_intake.py` — lê o Vault, monta o esqueleto de `content/AAAA-MM-DD/`.
- Modify `tools/build.py` — campo `podcast_audio` vira `<audio>`; `podar_audio()` mantém 3 mp3.
- Modify `assets/revista.css` — estilo do bloco `.podcast`.
- Create `tools/notebooklm_bridge.py` — orquestra a CLI do NotebookLM, baixa o mp3, grava `podcast_audio`.
- Create `tools/pipeline.md` — roteiro dos 7 passos que o agente headless segue.
- Create `tools/sexta.sh` — wrapper de cron que chama `claude -p`.
- Create `tests/test_build_audio.py`, `tests/test_vault_intake.py`, `tests/test_notebooklm_bridge.py` — testes com stdlib `unittest`.
- Modify `CLAUDE.md` / `README.md` — documentar as peças novas e a linha de cron.

**Ordem:** Task 1–2 (player) → Task 3–5 (intake) → Task 6–8 (bridge) → Task 9 (pipeline+cron) → Task 10 (docs). Tasks 1–5 são validáveis no MacBook Air; 6–9 têm partes que só fecham no Mac Mini.

---

### Task 1: Player de áudio no build (campo `podcast_audio`)

**Files:**
- Modify: `tools/build.py` (função `render_edicao`, após o bloco `<header class="hero">`)
- Test: `tests/test_build_audio.py`

**Interfaces:**
- Consumes: `edicao.json` com campo opcional `podcast_audio` (string, ex. `"2026-07-31.mp3"`).
- Produces: HTML com `<div class="podcast"><audio controls src="<prefixo>/podcast/audio/<arquivo>">` quando o campo existe; nada quando ausente. `render_edicao` ganha param novo `prefixo_audio` (str) — caminho relativo de `podcast/audio/` a partir da página. Home usa `"."`, páginas de edição usam `"../.."`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_build_audio.py
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build

class TestPodcastPlayer(unittest.TestCase):
    def _ed(self, **extra):
        base = {"data": "2026-07-31", "edicao": "001", "titulo": "Week In Review",
                "capa": {}, "itens": [], "barra": {}}
        base.update(extra)
        return base

    def test_audio_presente_renderiza_player(self):
        html = build.render_edicao(self._ed(podcast_audio="2026-07-31.mp3"),
                                   "assets/revista.css", "arquivo.html",
                                   lambda s: f"{s}.html", prefixo_audio=".")
        self.assertIn('class="podcast"', html)
        self.assertIn('<audio', html)
        self.assertIn('podcast/audio/2026-07-31.mp3', html)

    def test_audio_ausente_nao_renderiza(self):
        html = build.render_edicao(self._ed(), "assets/revista.css", "arquivo.html",
                                   lambda s: f"{s}.html", prefixo_audio=".")
        self.assertNotIn('<audio', html)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd "<repo>" && python3 -m unittest tests.test_build_audio -v`
Expected: FAIL — `render_edicao()` não aceita `prefixo_audio` (TypeError).

- [ ] **Step 3: Implementar**

Em `tools/build.py`, mudar a assinatura e adicionar o bloco. A assinatura vira:

```python
def render_edicao(ed, css, link_arquivo, link_artigo, prefixo_audio="."):
```

Logo após o `partes.append(...)` que fecha `</header>` do hero (por volta da linha 160), inserir:

```python
    audio = ed.get("podcast_audio")
    if audio:
        src = f"{prefixo_audio}/podcast/audio/{e(audio)}"
        partes.append(f"""
  <section class="podcast">
    <div class="section-title"><h2>Ouça a edição</h2></div>
    <audio controls preload="none" src="{src}"></audio>
    <p class="podcast-nota">Episódio gerado no NotebookLM a partir do resumo da semana.</p>
  </section>""")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_build_audio -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Commit**

```bash
git add tools/build.py tests/test_build_audio.py
git commit -m "feat(build): player de áudio quando edicao.json tem podcast_audio"
```

---

### Task 2: Retenção dos 3 mp3 mais recentes + ligar o player nas chamadas do build

**Files:**
- Modify: `tools/build.py` (função `build`, chamadas a `render_edicao` e fim de `build`)
- Test: `tests/test_build_audio.py` (adicionar classe de poda)

**Interfaces:**
- Consumes: diretório `podcast/audio/*.mp3`.
- Produces: função `podar_audio(dir_audio, manter=3)` que apaga mp3 além dos `manter` mais recentes (ordem por nome do arquivo, que começa com a data ISO) e retorna a lista de nomes apagados. Chamada no fim de `build()` quando não é `--check`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# adicionar a tests/test_build_audio.py
import tempfile, os

class TestPodarAudio(unittest.TestCase):
    def test_mantem_os_tres_mais_recentes(self):
        with tempfile.TemporaryDirectory() as d:
            dir_audio = Path(d)
            for nome in ["2026-07-10.mp3", "2026-07-17.mp3",
                         "2026-07-24.mp3", "2026-07-31.mp3"]:
                (dir_audio / nome).write_bytes(b"x")
            apagados = build.podar_audio(dir_audio, manter=3)
            restantes = sorted(p.name for p in dir_audio.glob("*.mp3"))
            self.assertEqual(apagados, ["2026-07-10.mp3"])
            self.assertEqual(restantes,
                ["2026-07-17.mp3", "2026-07-24.mp3", "2026-07-31.mp3"])

    def test_nada_a_podar_quando_ha_tres_ou_menos(self):
        with tempfile.TemporaryDirectory() as d:
            dir_audio = Path(d)
            (dir_audio / "2026-07-31.mp3").write_bytes(b"x")
            self.assertEqual(build.podar_audio(dir_audio, manter=3), [])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_build_audio.TestPodarAudio -v`
Expected: FAIL — `build` não tem `podar_audio`.

- [ ] **Step 3: Implementar**

Em `tools/build.py`, após as constantes de path (perto da linha 28) adicionar:

```python
AUDIO = PODCAST / "audio"
```

E antes de `def build(...)` adicionar a função:

```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_build_audio -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Ligar o `prefixo_audio` nas chamadas reais e chamar a poda**

Em `build()`, na chamada que gera a página de edição (`editions/<d>/index.html`):

```python
        (pasta / "index.html").write_text(
            render_edicao(ed, "../../assets/revista.css", "../../arquivo.html",
                          lambda slug: f"{slug}.html", prefixo_audio="../.."),
            encoding="utf-8")
```

Na chamada da home (fim de `build`):

```python
    (RAIZ / "index.html").write_text(
        render_edicao(atual, "assets/revista.css", "arquivo.html",
                      lambda slug: f"editions/{atual['data']}/{slug}.html",
                      prefixo_audio="."),
        encoding="utf-8")
```

E logo após escrever a home, antes do `print` final:

```python
    podar_audio(AUDIO, manter=3)
```

- [ ] **Step 6: Verificar build completo real**

Run: `python3 tools/build.py && python3 -m unittest tests.test_build_audio -v`
Expected: build imprime a edição, testes PASS. `git status` não deve mostrar mp3 apagados indevidamente (não há mp3 ainda).

- [ ] **Step 7: Commit**

```bash
git add tools/build.py tests/test_build_audio.py
git commit -m "feat(build): retenção dos 3 mp3 mais recentes e player nas páginas"
```

---

### Task 3: CSS do bloco de podcast

**Files:**
- Modify: `assets/revista.css` (fim do arquivo)

**Interfaces:**
- Consumes: markup `.podcast`, `.podcast audio`, `.podcast-nota` gerado na Task 1.
- Produces: estilo visível; sem teste automatizado (é CSS), validado a olho no navegador.

- [ ] **Step 1: Adicionar o estilo**

Ao final de `assets/revista.css`:

```css
/* ---- podcast player ---- */
.podcast { margin: 2rem 0; }
.podcast audio { width: 100%; margin-top: .75rem; }
.podcast-nota { font-size: .85rem; opacity: .7; margin-top: .5rem; }
```

- [ ] **Step 2: Verificar no navegador**

Adicionar `"podcast_audio": "2026-07-31.mp3"` temporariamente ao `content/2026-07-31/edicao.json`, criar um mp3 de teste (`mkdir -p podcast/audio && printf x > podcast/audio/2026-07-31.mp3`), rodar `python3 tools/build.py`, servir com `python3 -m http.server 8000` e conferir o player na home. Depois **reverter** o campo do JSON e apagar o mp3 de teste.

Run: `python3 tools/build.py && python3 -m http.server 8000`
Expected: bloco "Ouça a edição" com player abaixo do hero.

- [ ] **Step 3: Commit**

```bash
git checkout content/2026-07-31/edicao.json  # reverte o campo de teste
rm -f podcast/audio/2026-07-31.mp3
git add assets/revista.css
git commit -m "feat(css): estilo do player de podcast"
```

---

### Task 4: `vault_intake.py` — descoberta das 5 transcrições mais recentes

**Files:**
- Create: `tools/vault_intake.py`
- Test: `tests/test_vault_intake.py`

**Interfaces:**
- Consumes: diretório do Vault com `Estudos/<Canal>/YouTube/*.md`, cada nota começando com uma linha JSON `{"fm": {...}, "content": "..."}`.
- Produces:
  - `ler_frontmatter(caminho) -> dict` — devolve o dict `fm` da nota (`{}` se falhar).
  - `slugificar(titulo) -> str` — minúsculas, sem acento, hífens.
  - `descobrir_recentes(raiz_estudos, n=5) -> list[dict]` — cada dict tem
    `caminho` (Path), `fm` (dict), `data` (str ISO). Ordenado da mais nova para a
    mais antiga, ignorando notas cuja `date` seja `0000-00-00` ou ausente.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_vault_intake.py
import sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import vault_intake as vi

def _nota(dir_canal, data, titulo, video_id="ABC123"):
    p = dir_canal / f"{data} - {titulo}.md"
    fm = {"title": titulo, "video_id": video_id, "url": f"https://youtu.be/{video_id}",
          "date": data, "channel": dir_canal.parent.name}
    p.write_text(json.dumps({"fm": fm, "content": f"# {titulo}\n\ntexto"}), encoding="utf-8")
    return p

class TestDescoberta(unittest.TestCase):
    def _vault(self, d):
        estudos = Path(d) / "Estudos"
        for canal, data, tit in [
            ("Sam Harris", "2026-07-31", "Is AI Conscious"),
            ("Simon Sinek", "2026-07-30", "Great Employee"),
            ("Salesforce", "2026-07-29", "Military Program"),
            ("Ratos de IA", "2026-07-28", "Agentes"),
            ("New Thinking Allowed", "2026-07-27", "Maps"),
            ("Velho", "2020-01-01", "Antigo"),
            ("SemData", "0000-00-00", "Placeholder"),
        ]:
            yt = estudos / canal / "YouTube"
            yt.mkdir(parents=True, exist_ok=True)
            _nota(yt, data, tit)
        return estudos

    def test_pega_as_cinco_mais_recentes_ignora_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            estudos = self._vault(d)
            itens = vi.descobrir_recentes(estudos, n=5)
            datas = [i["data"] for i in itens]
            self.assertEqual(datas, ["2026-07-31", "2026-07-30", "2026-07-29",
                                     "2026-07-28", "2026-07-27"])
            self.assertEqual(itens[0]["fm"]["channel"], "Sam Harris")

    def test_slug(self):
        self.assertEqual(vi.slugificar("Is AI Already Conscious?"), "is-ai-already-conscious")
        self.assertEqual(vi.slugificar("Ratos de IA: Ação"), "ratos-de-ia-acao")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_vault_intake -v`
Expected: FAIL — módulo `vault_intake` não existe.

- [ ] **Step 3: Implementar o topo do módulo e as três funções**

```python
# tools/vault_intake.py
#!/usr/bin/env python3
"""Monta o esqueleto de uma edição a partir das transcrições do Vault.

  python3 tools/vault_intake.py --dry-run   # lista as 5 escolhidas
  python3 tools/vault_intake.py             # cria content/AAAA-MM-DD/
  python3 tools/vault_intake.py --force     # sobrescreve se já existir

O Vault fica em WIR_VAULT (env) ou na constante VAULT abaixo. O script só faz a
mecânica: descobrir, extrair frontmatter e montar o esqueleto. A redação dos
artigos e do editorial é feita por Claude, lendo as transcrições apontadas.
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
    """Le a primeira linha JSON da nota e devolve o dict fm (ou {})."""
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
        dados = json.loads(texto if texto.lstrip().startswith("{")
                           else texto.split("\n", 1)[0])
        return dados.get("fm", {}) if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_vault_intake -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Commit**

```bash
git add tools/vault_intake.py tests/test_vault_intake.py
git commit -m "feat(intake): descoberta das 5 transcrições mais recentes do Vault"
```

---

### Task 5: `vault_intake.py` — montar o esqueleto de `content/` e CLI

**Files:**
- Modify: `tools/vault_intake.py`
- Test: `tests/test_vault_intake.py`

**Interfaces:**
- Consumes: `descobrir_recentes`, `slugificar`, `ler_frontmatter` da Task 4.
- Produces:
  - `proxima_issue(content_dir) -> str` — maior `edicao` existente + 1, com zero à esquerda (ex. `"002"`); `"001"` se vazio.
  - `montar_item(indice, achado) -> dict` — um item do `edicao.json`.
  - `criar_edicao(achados, content_dir, force=False) -> Path` — escreve
    `edicao.json`, `editorial.md` e `artigos/<slug>.md` (placeholders). Levanta
    `FileExistsError` se a pasta existe e `force=False`.
  - `main()` com `--dry-run`, `--force`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# adicionar a tests/test_vault_intake.py
class TestMontagem(unittest.TestCase):
    def _achados(self):
        with tempfile.TemporaryDirectory() as d:
            estudos = TestDescoberta()._vault(d)
            return vi.descobrir_recentes(estudos, n=5)

    def test_proxima_issue(self):
        with tempfile.TemporaryDirectory() as d:
            content = Path(d)
            self.assertEqual(vi.proxima_issue(content), "001")
            (content / "2026-07-31").mkdir()
            (content / "2026-07-31" / "edicao.json").write_text('{"edicao":"007"}')
            self.assertEqual(vi.proxima_issue(content), "008")

    def test_montar_item_usa_frontmatter(self):
        achado = self._achados()[0]
        item = vi.montar_item(0, achado)
        self.assertEqual(item["numero"], "01")
        self.assertEqual(item["fonte"], "Sam Harris")
        self.assertEqual(item["slug"], "is-ai-conscious")
        self.assertIn("img.youtube.com/vi/ABC123", item["imagem"])
        self.assertTrue(item["artigo"].endswith(".md"))
        self.assertIn("YouTube", item["transcricao"])

    def test_criar_edicao_escreve_arquivos_e_valida(self):
        achados = self._achados()
        with tempfile.TemporaryDirectory() as d:
            content = Path(d)
            pasta = vi.criar_edicao(achados, content)
            dados = json.loads((pasta / "edicao.json").read_text())
            self.assertEqual(len(dados["itens"]), 5)
            self.assertTrue((pasta / "editorial.md").exists())
            for it in dados["itens"]:
                self.assertTrue((pasta / "artigos" / it["artigo"]).exists())
            with self.assertRaises(FileExistsError):
                vi.criar_edicao(achados, content)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_vault_intake.TestMontagem -v`
Expected: FAIL — funções não existem.

- [ ] **Step 3: Implementar**

Adicionar ao `tools/vault_intake.py`:

```python
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
        "resumo": "",   # Claude preenche na redação
        "porque": "",   # Claude preenche na redação
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
        raise FileExistsError(f"{pasta} já existe (use --force para sobrescrever)")
    (pasta / "artigos").mkdir(parents=True, exist_ok=True)
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
        sys.exit(f"Vault não encontrado em {estudos}. Ajuste WIR_VAULT.")
    achados = descobrir_recentes(estudos, n=5)
    if len(achados) < 5:
        print(f"  aviso: só {len(achados)} transcrições com data encontradas.")
    if not achados:
        sys.exit("nenhuma transcrição com data no Vault.")
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_vault_intake -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Ensaio contra o Vault real (só dry-run, não escreve)**

Run: `WIR_VAULT="$HOME/ObsidianVault" python3 tools/vault_intake.py --dry-run`
Expected: lista 5 linhas com datas recentes e canais reais (ex. Sam Harris 2026-07-31). Se o path do Vault diferir, ajustar a constante `VAULT`.

- [ ] **Step 6: Commit**

```bash
git add tools/vault_intake.py tests/test_vault_intake.py
git commit -m "feat(intake): monta content/ (edicao.json, editorial, artigos) das transcrições"
```

---

### Task 6: `notebooklm_bridge.py` — resolver/criar o notebook fixo

**Files:**
- Create: `tools/notebooklm_bridge.py`
- Test: `tests/test_notebooklm_bridge.py`

**Interfaces:**
- Consumes: CLI `notebooklm` no PATH; `notebooklm list --json`, `notebooklm create --json`.
- Produces:
  - `_run(args, capture=True) -> str` — executa `notebooklm <args>`, devolve stdout, levanta `RuntimeError` no non-zero (injetável nos testes via `runner`).
  - `resolver_notebook(titulo, runner=_run) -> str` — devolve o id do notebook com esse título; cria se não existe. `runner` é injetável para teste.

Nome do notebook: constante `NOTEBOOK = "Week In Review"`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_notebooklm_bridge.py
import sys, json, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import notebooklm_bridge as nb

class FakeRunner:
    def __init__(self, respostas):
        self.respostas = respostas   # dict: primeiro arg -> saida
        self.chamadas = []
    def __call__(self, args, capture=True):
        self.chamadas.append(args)
        chave = args[0]
        val = self.respostas.get(chave, "")
        return val() if callable(val) else val

class TestResolver(unittest.TestCase):
    def test_acha_notebook_existente(self):
        r = FakeRunner({"list": json.dumps(
            {"notebooks": [{"title": "Outro", "id": "x"},
                           {"title": "Week In Review", "id": "wir-123"}]})})
        self.assertEqual(nb.resolver_notebook("Week In Review", runner=r), "wir-123")
        self.assertNotIn("create", [c[0] for c in r.chamadas])

    def test_cria_quando_nao_existe(self):
        r = FakeRunner({"list": json.dumps({"notebooks": []}),
                        "create": json.dumps({"id": "novo-456"})})
        self.assertEqual(nb.resolver_notebook("Week In Review", runner=r), "novo-456")
        self.assertIn("create", [c[0] for c in r.chamadas])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_notebooklm_bridge -v`
Expected: FAIL — módulo não existe.

- [ ] **Step 3: Implementar**

```python
# tools/notebooklm_bridge.py
#!/usr/bin/env python3
"""Ponte entre o brief da edição e o NotebookLM (gera e baixa o mp3).

  python3 tools/notebooklm_bridge.py AAAA-MM-DD            # gera + baixa + grava
  python3 tools/notebooklm_bridge.py AAAA-MM-DD --dry-run  # só resolve o notebook

Usa a CLI notebooklm-py (já autenticada em ~/.notebooklm). Notebook fixo, fontes
acumulam; o áudio é limitado à fonte da semana via -s <source_id>.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTENT = RAIZ / "content"
AUDIO = RAIZ / "podcast" / "audio"
NOTEBOOK = "Week In Review"

def _run(args, capture=True):
    r = subprocess.run(["notebooklm", *args], capture_output=capture, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"notebooklm {' '.join(args)} falhou: {r.stderr or r.stdout}")
    return r.stdout if capture else ""

def _notebooks(payload):
    d = json.loads(payload)
    return d.get("notebooks", d) if isinstance(d, dict) else d

def resolver_notebook(titulo=NOTEBOOK, runner=_run):
    for n in _notebooks(runner(["list", "--json"])):
        if isinstance(n, dict) and n.get("title") == titulo:
            return n.get("id") or n.get("notebook_id")
    criado = json.loads(runner(["create", titulo, "--json"]))
    return criado.get("id") or criado.get("notebook_id")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_notebooklm_bridge -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Commit**

```bash
git add tools/notebooklm_bridge.py tests/test_notebooklm_bridge.py
git commit -m "feat(podcast): resolver/criar notebook fixo no NotebookLM"
```

---

### Task 7: `notebooklm_bridge.py` — adicionar fonte, gerar e baixar o mp3

**Files:**
- Modify: `tools/notebooklm_bridge.py`
- Test: `tests/test_notebooklm_bridge.py`

**Interfaces:**
- Consumes: `resolver_notebook`, `_run`; brief em `podcast/AAAA-MM-DD-brief.md`.
- Produces:
  - `adicionar_fonte(nb_id, brief_path, runner=_run) -> str` — sobe o brief como
    fonte, devolve o `source_id` (parseado do `--json` do `source add`).
  - `gerar_e_baixar(nb_id, source_id, data, runner=_run) -> Path` — gera o audio
    (pt-BR, `-s source_id`, `--wait`), baixa para `podcast/audio/AAAA-MM-DD.mp3`,
    devolve o Path.

- [ ] **Step 1: Escrever o teste que falha**

```python
# adicionar a tests/test_notebooklm_bridge.py
import tempfile

class TestFonteEAudio(unittest.TestCase):
    def test_adicionar_fonte_devolve_id(self):
        r = FakeRunner({"source": json.dumps({"source_id": "src-9"})})
        with tempfile.TemporaryDirectory() as d:
            brief = Path(d) / "b.md"; brief.write_text("x")
            self.assertEqual(nb.adicionar_fonte("wir-1", brief, runner=r), "src-9")
            self.assertEqual(r.chamadas[0][0], "source")

    def test_gerar_e_baixar_usa_source_e_idioma(self):
        chamadas = []
        def runner(args, capture=True):
            chamadas.append(args)
            return "{}"
        with tempfile.TemporaryDirectory() as d:
            audio_dir = Path(d)
            p = nb.gerar_e_baixar("wir-1", "src-9", "2026-07-31",
                                  runner=runner, audio_dir=audio_dir)
            gen = next(c for c in chamadas if c[0] == "generate")
            self.assertIn("-s", gen); self.assertIn("src-9", gen)
            self.assertIn("--language", gen)
            self.assertTrue(any(c[0] == "download" for c in chamadas))
            self.assertEqual(p, audio_dir / "2026-07-31.mp3")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_notebooklm_bridge.TestFonteEAudio -v`
Expected: FAIL — funções não existem.

- [ ] **Step 3: Implementar**

Adicionar ao módulo:

```python
def adicionar_fonte(nb_id, brief_path, runner=_run):
    saida = runner(["source", "add", "--notebook", nb_id,
                    "--file", str(brief_path), "--json"])
    try:
        d = json.loads(saida)
        return d.get("source_id") or d.get("id")
    except json.JSONDecodeError:
        return ""

def gerar_e_baixar(nb_id, source_id, data, runner=_run, audio_dir=AUDIO):
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    gen = ["generate", "audio", "--notebook", nb_id,
           "--language", "pt-BR", "--wait"]
    if source_id:
        gen += ["-s", source_id]
    runner(gen)
    destino = audio_dir / f"{data}.mp3"
    runner(["download", "audio", str(destino), "--notebook", nb_id, "--latest"])
    return destino
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_notebooklm_bridge -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Commit**

```bash
git add tools/notebooklm_bridge.py tests/test_notebooklm_bridge.py
git commit -m "feat(podcast): adicionar fonte, gerar áudio pt-BR e baixar o mp3"
```

---

### Task 8: `notebooklm_bridge.py` — gravar `podcast_audio` e CLI `main`

**Files:**
- Modify: `tools/notebooklm_bridge.py`
- Test: `tests/test_notebooklm_bridge.py`

**Interfaces:**
- Consumes: as funções anteriores; `content/AAAA-MM-DD/edicao.json`.
- Produces:
  - `gravar_podcast_audio(data, nome_mp3, content_dir=CONTENT) -> None` — escreve
    a chave `podcast_audio` no `edicao.json` da edição, preservando o resto.
  - `main()` — `<data> [--dry-run]`: resolve notebook; em dry-run para aí; senão
    adiciona fonte, gera+baixa, grava `podcast_audio`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# adicionar a tests/test_notebooklm_bridge.py
class TestGravar(unittest.TestCase):
    def test_grava_campo_preservando_json(self):
        with tempfile.TemporaryDirectory() as d:
            content = Path(d); (content / "2026-07-31").mkdir()
            arq = content / "2026-07-31" / "edicao.json"
            arq.write_text(json.dumps({"edicao": "001", "itens": []}), encoding="utf-8")
            nb.gravar_podcast_audio("2026-07-31", "2026-07-31.mp3", content_dir=content)
            d2 = json.loads(arq.read_text())
            self.assertEqual(d2["podcast_audio"], "2026-07-31.mp3")
            self.assertEqual(d2["edicao"], "001")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python3 -m unittest tests.test_notebooklm_bridge.TestGravar -v`
Expected: FAIL — função não existe.

- [ ] **Step 3: Implementar**

```python
def gravar_podcast_audio(data, nome_mp3, content_dir=CONTENT):
    arq = Path(content_dir) / data / "edicao.json"
    dados = json.loads(arq.read_text(encoding="utf-8"))
    dados["podcast_audio"] = nome_mp3
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("uso: notebooklm_bridge.py AAAA-MM-DD [--dry-run]")
    data = args[0]
    brief = RAIZ / "podcast" / f"{data}-brief.md"
    if not brief.exists():
        sys.exit(f"brief não encontrado: {brief}. Rode build.py antes.")
    nb_id = resolver_notebook()
    print(f"  notebook: {nb_id}")
    if "--dry-run" in args:
        print("  dry-run: parando antes de gerar áudio.")
        return
    src = adicionar_fonte(nb_id, brief)
    print(f"  fonte adicionada: {src}")
    mp3 = gerar_e_baixar(nb_id, src, data)
    gravar_podcast_audio(data, mp3.name)
    print(f"  mp3 em {mp3}, podcast_audio gravado. Rode build.py + publicar.sh.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python3 -m unittest tests.test_notebooklm_bridge -v`
Expected: PASS (5 testes).

- [ ] **Step 5: Ensaio real de auth (dry-run, não gera áudio)**

Run: `python3 tools/build.py && python3 tools/notebooklm_bridge.py 2026-07-31 --dry-run`
Expected: imprime um id de notebook (cria "Week In Review" se necessário). Se der erro de auth, rodar `notebooklm login`. **Nota:** isso pode criar o notebook fixo de verdade, o que é desejado.

- [ ] **Step 6: Commit**

```bash
git add tools/notebooklm_bridge.py tests/test_notebooklm_bridge.py
git commit -m "feat(podcast): grava podcast_audio no edicao.json e CLI da ponte"
```

---

### Task 9: Pipeline e agendamento (sexta 15h30, Mac Mini)

**Files:**
- Create: `tools/pipeline.md`
- Create: `tools/sexta.sh`

**Interfaces:**
- Consumes: `vault_intake.py`, `build.py`, `notebooklm_bridge.py`, `publicar.sh`.
- Produces: roteiro que o `claude -p` executa e o wrapper de cron. Sem teste
  unitário (integração); validação por ensaio.

- [ ] **Step 1: Escrever o roteiro do pipeline**

```markdown
<!-- tools/pipeline.md -->
Execute o pipeline semanal da Week In Review, nesta ordem, parando e reportando se algum passo falhar:

1. `git pull` no repositório.
2. `python3 tools/vault_intake.py` para montar `content/<data>/` com as 5 transcrições mais recentes. Se a pasta já existir, pare e reporte (não use --force sem eu pedir).
3. Para cada item em `content/<data>/edicao.json`, leia a transcrição apontada em `transcricao` (arquivo grande: leia em subagente, nunca a nota inteira no contexto principal) e escreva o artigo em `content/<data>/artigos/<slug>.md`: análise e síntese com tese própria, 1.000 a 1.200 palavras, nunca paráfrase da fonte, sem travessão. Preencha também `resumo`, `porque`, `tags`, `dek`, `pills`, `capa` e `editorial.md`.
4. `python3 tools/build.py` para gerar o brief.
5. `python3 tools/notebooklm_bridge.py <data>` para gerar e baixar o mp3 e gravar `podcast_audio`.
6. `python3 tools/build.py` de novo (agora com o player) — a poda dos 3 mp3 roda aqui.
7. `./publicar.sh` para commitar e publicar. Reporte o link de preview.

Regras: sem citar Claude no conteúdo nem nos commits. Conventional Commits. Se o NotebookLM falhar por auth, pare e avise para rodar `notebooklm login`.
```

- [ ] **Step 2: Escrever o wrapper de cron**

```bash
#!/usr/bin/env bash
# tools/sexta.sh — dispara o pipeline semanal via Claude Code headless.
# Cron (Mac Mini):  30 15 * * 5  /CAMINHO/week-in-review/tools/sexta.sh
set -euo pipefail
cd "$(dirname "$0")/.."

LOG="$HOME/Library/Logs/week-in-review-sexta.log"
echo "===== $(date) pipeline iniciado =====" >> "$LOG"

# --ensaio: roda tudo menos o publicar (para testar sem publicar)
PROMPT="$(cat tools/pipeline.md)"
if [[ "${1:-}" == "--ensaio" ]]; then
  PROMPT="$PROMPT

MODO ENSAIO: execute os passos 1 a 6 mas NÃO rode o passo 7 (publicar.sh). Só reporte o que publicaria."
fi

claude -p "$PROMPT" --permission-mode acceptEdits >> "$LOG" 2>&1
echo "===== $(date) pipeline terminado =====" >> "$LOG"
```

- [ ] **Step 3: Tornar executável e validar sintaxe**

Run: `chmod +x tools/sexta.sh && bash -n tools/sexta.sh && echo "sintaxe ok"`
Expected: `sintaxe ok`.

- [ ] **Step 4: Commit**

```bash
git add tools/pipeline.md tools/sexta.sh
git commit -m "feat(pipeline): roteiro do pipeline semanal e wrapper de cron"
```

- [ ] **Step 5: Documentar a ativação do cron (não ativa aqui)**

A ativação roda **no Mac Mini** pelo Hygor (não no Air):

```bash
# no Mac Mini:
crontab -l 2>/dev/null | { cat; echo "30 15 * * 5 $HOME/projetos/week-in-review/tools/sexta.sh"; } | crontab -
# ensaio manual antes de confiar no cron:
tools/sexta.sh --ensaio && tail -30 ~/Library/Logs/week-in-review-sexta.log
```

Registrar isso na doc (Task 10). Nenhum comando de cron é executado no Air.

---

### Task 10: Documentação (CLAUDE.md + README)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: tudo. Produces: doc atualizada; sem teste.

- [ ] **Step 1: Atualizar `CLAUDE.md`**

Na seção "A rotina da semana", substituir os passos manuais por: "Roda sozinho toda sexta 15h30 no Mac Mini via `tools/sexta.sh` (cron). Manual: `vault_intake.py` → escrever artigos → `build.py` → `notebooklm_bridge.py` → `build.py` → `publicar.sh`."

Na seção "Onde as coisas rodam", registrar que a ponte do NotebookLM é a CLI `notebooklm-py` (não mais "a implementar") e o mp3 fica em `podcast/audio/` com retenção de 3. Adicionar à árvore de arquivos: `tools/vault_intake.py`, `tools/notebooklm_bridge.py`, `tools/sexta.sh`, `tools/pipeline.md`, `podcast/audio/`.

- [ ] **Step 2: Atualizar `README.md`**

Na seção "Podcast", registrar que o build agora embute um player quando há `podcast_audio`, e que a ponte automática usa a CLI do NotebookLM no Mac Mini. Na "Rotina da semana", mencionar o agendamento de sexta 15h30.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: automação de Vault, podcast e agendamento de sexta"
```

---

## Self-Review

**Cobertura do spec:**
- Peça 1 (intake) → Tasks 4, 5. ✓
- Peça 2 (player + retenção) → Tasks 1, 2, 3. ✓
- Peça 3 (bridge) → Tasks 6, 7, 8. ✓
- Peça 4 (agendamento) → Task 9. ✓
- Frontmatter JSON → Task 4 (`ler_frontmatter`). ✓
- Transcrição grande / subagente → pipeline.md passo 3. ✓
- Notebook fixo + `-s source_id` → Tasks 6, 7. ✓
- Retenção 3 mp3 sem corte silencioso → Task 2 (`podar_audio` loga). ✓
- Idempotência/--force/--dry-run intake → Task 5. ✓
- Docs → Task 10. ✓

**Consistência de tipos:** `render_edicao(..., prefixo_audio=".")` usado igual nas Tasks 1 e 2. `podar_audio(dir, manter=3)` idem. `resolver_notebook`/`adicionar_fonte`/`gerar_e_baixar`/`gravar_podcast_audio` com assinaturas estáveis entre Tasks 6–8. `runner` injetável consistente. `AUDIO` definido na Task 2 e reusado na 6+. ✓

**Placeholders:** nenhum TODO/TBD; todo passo tem código real. ✓

**Nota de ambiente:** Tasks 1–5 validáveis no MacBook Air (Vault acessível). Tasks 6–8 têm testes com runner falso (rodam em qualquer lugar) e um ensaio de auth real; a geração de áudio ponta-a-ponta e o cron da Task 9 validam-se no Mac Mini.
