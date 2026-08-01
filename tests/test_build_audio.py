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
