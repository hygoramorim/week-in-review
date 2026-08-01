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
