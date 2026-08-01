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

class TestPodarAudio(unittest.TestCase):
    def test_mantem_os_tres_mais_recentes(self):
        import tempfile
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
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            dir_audio = Path(d)
            (dir_audio / "2026-07-31.mp3").write_bytes(b"x")
            self.assertEqual(build.podar_audio(dir_audio, manter=3), [])

if __name__ == "__main__":
    unittest.main()
