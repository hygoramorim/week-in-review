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
