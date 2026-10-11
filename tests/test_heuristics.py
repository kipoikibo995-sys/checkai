from pathlib import Path
import unittest

from aicheck import Detector, analyze
from aicheck.heuristics import split_sentences

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class HeuristicsTest(unittest.TestCase):
    def test_ai_sample_scores_higher_than_human(self):
        ai = analyze((SAMPLES / "ai-sample.txt").read_text("utf-8"))
        human = analyze((SAMPLES / "human-sample.txt").read_text("utf-8"))
        self.assertGreater(ai.score, 0.6)
        self.assertLess(human.score, 0.35)

    def test_sentence_offsets_point_at_text(self):
        text = "First one.  Second is longer!\nThird?"
        sents = split_sentences(text)
        self.assertEqual([s.text for s in sents], ["First one.", "Second is longer!", "Third?"])
        for s in sents:
            self.assertEqual(text[s.start:s.end], s.text)

    def test_word_boundaries(self):
        # "me" is a human marker but must not match inside "embrace"
        hl = analyze("We embrace the journey.").highlights
        self.assertFalse(any(h.kind == "human" for h in hl))
        self.assertTrue(any(h.kind == "cliche" for h in hl))

    def test_curly_apostrophes_count_as_contractions(self):
        hl = analyze("I’m sure it’s fine.").highlights
        self.assertTrue(any(h.kind == "human" and h.end - h.start == 3 for h in hl))

    def test_detector_without_model(self):
        r = Detector().check((SAMPLES / "ai-sample.txt").read_text("utf-8"))
        self.assertEqual(r.verdict, "Likely AI-written")
        self.assertIsNone(r.model)
        self.assertTrue(r.warnings)


if __name__ == "__main__":
    unittest.main()
