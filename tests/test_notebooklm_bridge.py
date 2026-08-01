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
