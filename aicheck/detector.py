"""Combine the model score and the style score into one verdict, with threshold calibration."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import heuristics

CALIBRATION_FILE = Path(os.environ.get("AICHECK_CALIBRATION", Path.home() / ".aicheck" / "calibration.json"))

# Threshold used before calibration. The Binoculars paper uses ~0.90 with a Falcon-7B pair;
# other models drift from that, so run `python -m aicheck calibrate`.
DEFAULT_THRESHOLD = 0.90
DEFAULT_SCALE = 0.05
MODEL_WEIGHT = 0.7  # share of the model score when combined with the style score
MIN_WORDS = 120


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-max(-60.0, min(60.0, x))))


def load_calibration(model_key: str) -> dict | None:
    try:
        return json.loads(CALIBRATION_FILE.read_text("utf-8")).get(model_key)
    except (OSError, ValueError):
        return None


def save_calibration(model_key: str, data: dict) -> Path:
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        allc = json.loads(CALIBRATION_FILE.read_text("utf-8"))
    except (OSError, ValueError):
        allc = {}
    allc[model_key] = data
    CALIBRATION_FILE.write_text(json.dumps(allc, ensure_ascii=False, indent=2), "utf-8")
    return CALIBRATION_FILE


def verdict(p: float) -> str:
    if p >= 0.75:
        return "Likely AI-written"
    if p >= 0.55:
        return "Leans AI"
    if p > 0.40:
        return "Mixed signals"
    if p > 0.25:
        return "Leans human"
    return "Likely human-written"


@dataclass
class SentenceReport:
    start: int
    end: int
    text: str
    words: int
    ai_probability: float | None = None
    binoculars: float | None = None


@dataclass
class Report:
    ai_probability: float
    verdict: str
    words: int
    sentences_count: int
    heuristic_score: float
    signals: dict
    stats: dict
    highlights: list[dict]
    sentences: list[SentenceReport]
    model: dict | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class Detector:
    def __init__(self, scorer=None):
        """scorer: a BinocularsScorer, or None to use style signals only."""
        self.scorer = scorer
        self.calibration = load_calibration(scorer.model_key) if scorer else None

    @property
    def threshold(self) -> float:
        return (self.calibration or {}).get("threshold", DEFAULT_THRESHOLD)

    @property
    def scale(self) -> float:
        return (self.calibration or {}).get("scale", DEFAULT_SCALE)

    def prob_from_binoculars(self, b: float) -> float:
        return _sigmoid((self.threshold - b) / self.scale)

    def check(self, text: str) -> Report:
        text = heuristics.normalize(text)
        h = heuristics.analyze(text)
        sents = heuristics.split_sentences(text)
        warnings = []
        if h.n_words < MIN_WORDS:
            warnings.append(f"Only {h.n_words} words. Results under {MIN_WORDS} words are unreliable.")

        sent_reports = [SentenceReport(s.start, s.end, s.text, s.n_words) for s in sents]
        model_info = None
        prob = h.score
        if self.scorer and h.n_words >= 5:
            lm = self.scorer.score(text, [(s.start, s.end) for s in sents])
            p_model = self.prob_from_binoculars(lm.binoculars)
            prob = MODEL_WEIGHT * p_model + (1 - MODEL_WEIGHT) * h.score
            by_span = {(s.start, s.end): s for s in lm.sentences}
            for sr in sent_reports:
                s = by_span.get((sr.start, sr.end))
                if s:
                    sr.binoculars = s.binoculars
                    sr.ai_probability = self.prob_from_binoculars(s.binoculars)
            model_info = {
                "observer": self.scorer.observer_name,
                "performer": self.scorer.performer_name,
                "device": self.scorer.device,
                "tokens": lm.tokens,
                "perplexity": lm.perplexity,
                "binoculars": lm.binoculars,
                "threshold": self.threshold,
                "calibrated": self.calibration is not None,
                "model_probability": p_model,
            }
            if lm.truncated:
                warnings.append(f"Long text: the model only scored the first {lm.tokens} tokens.")
            if not self.calibration:
                warnings.append("The model threshold is not calibrated yet. See Calibration in the README.")
        elif not self.scorer:
            warnings.append("Running without a language model, using writing-style signals only.")

        return Report(
            ai_probability=prob,
            verdict=verdict(prob),
            words=h.n_words,
            sentences_count=h.n_sentences,
            heuristic_score=h.score,
            signals=h.signals,
            stats=h.stats,
            highlights=[asdict(x) for x in h.highlights],
            sentences=sent_reports,
            model=model_info,
            warnings=warnings,
        )


def calibrate(scorer, human_texts: list[str], ai_texts: list[str]) -> dict:
    """Find the Binoculars threshold that best separates your own two sample sets."""
    hs = [scorer.score(t).binoculars for t in human_texts]
    ais = [scorer.score(t).binoculars for t in ai_texts]
    cands = sorted(hs + ais)
    best = (0.0, DEFAULT_THRESHOLD)
    for i in range(len(cands) - 1):
        thr = (cands[i] + cands[i + 1]) / 2
        tpr = sum(b < thr for b in ais) / len(ais)
        tnr = sum(b >= thr for b in hs) / len(hs)
        bal = (tpr + tnr) / 2
        if bal > best[0]:
            best = (bal, thr)

    def sd(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1))

    spread = (sd(hs) + sd(ais)) / 2 if len(hs) > 1 and len(ais) > 1 else DEFAULT_SCALE
    data = {
        "threshold": best[1],
        "scale": max(0.01, spread / 2),
        "balanced_accuracy": best[0],
        "n_human": len(hs),
        "n_ai": len(ais),
        "human_mean": sum(hs) / len(hs),
        "ai_mean": sum(ais) / len(ais),
    }
    save_calibration(scorer.model_key, data)
    return data
