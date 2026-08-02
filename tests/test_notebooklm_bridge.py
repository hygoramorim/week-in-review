import sys, json, unittest, tempfile
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

class TestNotebookSemana(unittest.TestCase):
    def test_nome_notebook_formata_data(self):
        self.assertEqual(nb.nome_notebook("2026-07-31"), "week in review 31 07 26")
        self.assertEqual(nb.nome_notebook("2026-01-05"), "week in review 05 01 26")

    def test_cria_sempre_novo(self):
        # formato aninhado do notebooklm-py >= 0.7: {"notebook": {"id": ...}}
        r = FakeRunner({"create": json.dumps({"notebook": {"id": "novo-1"}})})
        self.assertEqual(nb.criar_notebook_semana("2026-07-31", runner=r), "novo-1")
        # sempre chama create, nunca list
        self.assertIn("create", [c[0] for c in r.chamadas])
        self.assertNotIn("list", [c[0] for c in r.chamadas])

    def test_cria_formato_plano_antigo(self):
        # tolera o formato plano de versoes antigas da CLI
        r = FakeRunner({"create": json.dumps({"id": "plano-1"})})
        self.assertEqual(nb.criar_notebook_semana("2026-07-31", runner=r), "plano-1")

class TestFonteEAudio(unittest.TestCase):
    def test_adicionar_fonte_devolve_id(self):
        # formato aninhado do 0.7: {"source": {"id": ...}}
        r = FakeRunner({"source": json.dumps({"source": {"id": "src-9"}})})
        with tempfile.TemporaryDirectory() as d:
            brief = Path(d) / "b.md"; brief.write_text("x")
            self.assertEqual(nb.adicionar_fonte("wir-1", brief, runner=r), "src-9")
            chamada = r.chamadas[0]
            self.assertEqual(chamada[0], "source")
            # CRITICO: precisa ser --type file (le o arquivo). Com --type text
            # o caminho vira a fonte e o podcast sai vazio.
            self.assertIn("--type", chamada)
            self.assertEqual(chamada[chamada.index("--type") + 1], "file")
            self.assertIn(str(brief), chamada)

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

    def test_gerar_e_baixar_falha_com_source_vazio(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                nb.gerar_e_baixar("wir-1", "", "2026-07-31",
                                  runner=lambda a, capture=True: "{}",
                                  audio_dir=Path(d))

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

if __name__ == "__main__":
    unittest.main()
