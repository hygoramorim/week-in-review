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

class TestCssEditorialNaoSobrepoe(unittest.TestCase):
    """Trava a regressão do título gigante do editorial sobrepondo o texto.

    Causa raiz do bug (2026-08-03): uma regra global `h1{ font-size:clamp(...) }`
    feita pro hero vazava pro `<h1>` que o markdown do editorial gera. O conserto
    foi escopar pra `.hero h1` e dar ao editorial um tamanho contido. Estes testes
    garantem que ninguém reintroduza a regra global."""

    def _css(self):
        import re
        css = (Path(__file__).resolve().parent.parent / "assets" / "revista.css").read_text(encoding="utf-8")
        return css, re

    def test_nao_ha_regra_global_h1_com_font_size(self):
        css, re = self._css()
        # procura um seletor que seja exatamente `h1` (não `.hero h1`, `.x h1`)
        # abrindo um bloco. Ex.: "h1{" ou "h1 {" no começo de regra.
        globais = re.findall(r'(?:^|[},])\s*h1\s*\{', css)
        self.assertEqual(globais, [],
            "Regra global `h1{...}` reintroduzida: escope pra `.hero h1` "
            "senão o tamanho display vaza pro título do editorial e o sobrepõe.")

    def test_hero_h1_existe_e_editorial_h1_contido(self):
        css, re = self._css()
        self.assertRegex(css, r'\.hero\s+h1\s*\{', "faltou a regra `.hero h1`")
        self.assertRegex(css, r'\.editorial\s+article\s+h1\s*\{',
            "faltou a regra que contém o h1 do editorial")


if __name__ == "__main__":
    unittest.main()
