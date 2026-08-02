import sys, json, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import vault_intake as vi

def _nota(dir_canal, data, titulo, video_id="ABC123"):
    p = dir_canal / f"{data} - {titulo}.md"
    p.write_text(
        "---\n"
        f'title: "{titulo}"\n'
        f"video_id: {video_id}\n"
        f"url: https://youtu.be/{video_id}\n"
        f"date: {data}\n"
        f"channel: {dir_canal.parent.name}\n"
        "tags: [a, b]\n"
        "---\n\n"
        f"# {titulo}\n\ntexto real da transcricao\n",
        encoding="utf-8")
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
        self.assertEqual(vi.slugificar("Ratos de IA: Acao"), "ratos-de-ia-acao")

    def test_ler_frontmatter_json_primeira_linha_com_corpo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "n.md"
            p.write_text('{"fm": {"title": "X", "date": "2026-07-31"}, "content": "..."}\n# X\n\ncorpo',
                         encoding="utf-8")
            fm = vi.ler_frontmatter(p)
            self.assertEqual(fm["title"], "X")
            self.assertEqual(fm["date"], "2026-07-31")

    def test_ler_frontmatter_yaml_com_corpo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "n.md"
            p.write_text('---\ntitle: "Y"\ndate: 2026-07-31\ntags: [x, y]\n---\n\n# Y\n\ncorpo longo',
                         encoding="utf-8")
            fm = vi.ler_frontmatter(p)
            self.assertEqual(fm["title"], "Y")
            self.assertEqual(fm["tags"], ["x", "y"])

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

    def test_force_limpa_artigos_orfaos(self):
        achados = self._achados()
        with tempfile.TemporaryDirectory() as d:
            content = Path(d)
            pasta = vi.criar_edicao(achados, content)
            # simula um artigo orfao de uma montagem anterior (slug antigo)
            orfao = pasta / "artigos" / "slug-antigo-que-nao-existe-mais.md"
            orfao.write_text("# velho\n")
            self.assertTrue(orfao.exists())
            vi.criar_edicao(achados, content, force=True)
            # o orfao some; so ficam os artigos referenciados no edicao.json
            self.assertFalse(orfao.exists())
            dados = json.loads((pasta / "edicao.json").read_text())
            refs = {it["artigo"] for it in dados["itens"]}
            no_disco = {p.name for p in (pasta / "artigos").glob("*.md")}
            self.assertEqual(no_disco, refs)

if __name__ == "__main__":
    unittest.main()
