from pathlib import Path
import unittest

from aicheck import Detector, analyze
from aicheck.heuristics import split_sentences

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class HeuristicsTest(unittest.TestCase):
    def test_ai_sample_scores_higher_than_human(self):
        ai = analyze((SAMPLES / "mau-ai.txt").read_text("utf-8"))
        human = analyze((SAMPLES / "mau-nguoi-viet.txt").read_text("utf-8"))
        self.assertGreater(ai.score, 0.6)
        self.assertLess(human.score, 0.35)

    def test_sentence_offsets_point_at_text(self):
        text = "Câu một.  Câu hai rất dài!\nCâu ba?"
        sents = split_sentences(text)
        self.assertEqual([s.text for s in sents], ["Câu một.", "Câu hai rất dài!", "Câu ba?"])
        for s in sents:
            self.assertEqual(text[s.start:s.end], s.text)

    def test_vietnamese_word_boundaries(self):
        # "đó" là tiểu từ, nhưng không được khớp bên trong "đóng"
        hl = analyze("Kênh đóng vai trò quan trọng.").highlights
        self.assertFalse(any(h.kind == "human" for h in hl))
        self.assertTrue(any(h.kind == "cliche" for h in hl))

    def test_detector_without_model(self):
        r = Detector().check((SAMPLES / "mau-ai.txt").read_text("utf-8"))
        self.assertEqual(r.verdict, "Rất có thể do AI viết")
        self.assertIsNone(r.model)
        self.assertTrue(r.warnings)


if __name__ == "__main__":
    unittest.main()
