"""Writing-style signals that need no model, so they run anywhere.

Each signal is a value from 0 to 1, where 1 means "reads like AI".
The phrase lists are tuned for English, with a smaller Vietnamese set.
Keep them in sync with the copy in aicheck/web.html.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# Words and phrases that AI assistants overuse.
CLICHES = [
    # English
    "delve", "delves", "delving", "tapestry", "testament to", "it's important to note",
    "it is important to note", "it's worth noting", "it is worth noting",
    "in today's fast-paced world", "in today's digital age", "in today's world",
    "ever-evolving", "ever-changing", "fast-paced", "navigate the complexities", "navigating",
    "landscape", "embark", "journey", "unlock", "unleash", "elevate", "seamless", "seamlessly",
    "vibrant", "plays a crucial role", "plays a vital role", "crucial", "pivotal", "foster",
    "fostering", "realm", "robust", "leverage", "harness", "empower", "empowering",
    "transformative", "game-changer", "game changer", "cutting-edge", "dive into", "let's dive",
    "a myriad of", "myriad", "plethora", "showcase", "showcasing", "underscore", "underscores",
    "intricate", "meticulous", "meticulously", "comprehensive", "holistic", "paramount",
    "resonate", "resonates", "bustling", "beacon", "symphony", "nestled", "look no further",
    "rest assured", "not only", "but also", "stands as", "serves as", "boasts", "captivating",
    "invaluable", "valuable insights", "to the next level", "embrace", "thrive", "endeavor",
    "unwavering", "profound", "enhance", "streamline", "optimize", "innovative", "dynamic",
    "whether you're", "in the world of", "when it comes to", "a wide range of",
    # Vietnamese
    "trong thế giới", "đóng vai trò quan trọng", "không chỉ", "mà còn", "hành trình",
    "khám phá", "trải nghiệm", "đầy ý nghĩa", "chìa khóa", "nâng tầm", "lan tỏa",
    "đa dạng", "tối ưu", "không thể phủ nhận", "đáp ứng nhu cầu", "hãy cùng", "đồng hành",
]

# Transition words that AI likes to open sentences with.
CONNECTORS = [
    "moreover", "furthermore", "additionally", "however", "overall", "in addition",
    "firstly", "secondly", "lastly", "finally", "ultimately", "in conclusion", "in summary",
    "to summarize", "consequently", "therefore", "thus", "notably", "importantly",
    "as a result", "on the other hand", "that said", "by contrast", "in essence",
    "bên cạnh đó", "hơn nữa", "ngoài ra", "tóm lại", "nhìn chung", "cuối cùng", "tuy nhiên",
]

# Signs of a real person talking: contractions, slang, first person, filler.
HUMAN_MARKERS = [
    "i'm", "i've", "i'd", "i'll", "don't", "can't", "won't", "didn't", "isn't", "wasn't",
    "couldn't", "wouldn't", "shouldn't", "gonna", "wanna", "gotta", "kinda", "sorta",
    "yeah", "yep", "nope", "lol", "lmao", "haha", "honestly", "tbh", "idk", "btw", "ok",
    "okay", "stuff", "anyway", "anyways", "dunno", "ugh", "wow", "damn", "pretty much",
    "i guess", "i mean", "you know", "i", "my", "me",
    "mình", "tui", "nhé", "nha", "nhỉ", "á", "thôi", "chả", "kiểu", "ủa",
]

# Weights used to combine the signals into one score (sum = 1).
WEIGHTS = {
    "burstiness": 0.22,
    "cliches": 0.28,
    "connectors": 0.15,
    "human_voice": 0.17,
    "diversity": 0.09,
    "repetition": 0.09,
}

SIGNAL_LABELS = {
    "burstiness": "Even sentence lengths",
    "cliches": "AI buzzwords",
    "connectors": "Stock transitions",
    "human_voice": "No personal voice",
    "diversity": "Repeated vocabulary",
    "repetition": "Repeated phrases",
}


def _alt(phrases: list[str]) -> str:
    return "|".join(re.escape(p) for p in sorted(set(phrases), key=len, reverse=True))


RE_CLICHE = re.compile(rf"(?<!\w)({_alt(CLICHES)})(?!\w)", re.IGNORECASE)
RE_HUMAN = re.compile(rf"(?<![\w'])({_alt(HUMAN_MARKERS)})(?![\w'])", re.IGNORECASE)
RE_CONNECTOR = re.compile(rf"(^|[.!?…\n]\s*)({_alt(CONNECTORS)})(?!\w)", re.IGNORECASE)
RE_WORD = re.compile(r"[\w']+")
RE_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")
RE_PUNCT = re.compile(r"[?!]|\.\.\.|…")


def normalize(text: str) -> str:
    """Straighten curly apostrophes. Same length, so character offsets stay valid."""
    return text.replace("’", "'").replace("‘", "'")


def words(text: str) -> list[str]:
    return RE_WORD.findall(text.lower())


@dataclass
class Sentence:
    text: str
    start: int
    end: int

    @property
    def n_words(self) -> int:
        return len(words(self.text))


def split_sentences(text: str) -> list[Sentence]:
    out, pos = [], 0
    for m in RE_SENT_SPLIT.finditer(text + "\n"):
        chunk = text[pos:m.start()]
        stripped = chunk.strip()
        if stripped and words(stripped):
            s = pos + chunk.index(stripped)
            out.append(Sentence(stripped, s, s + len(stripped)))
        pos = m.end()
    return out


def _lin(x: float, lo: float, hi: float) -> float:
    """0 when x <= lo, 1 when x >= hi, linear in between."""
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


@dataclass
class Highlight:
    start: int
    end: int
    kind: str  # "cliche" | "connector" | "human"


@dataclass
class HeuristicResult:
    n_words: int
    n_sentences: int
    sentence_lengths: list[int]
    stats: dict[str, float]
    signals: dict[str, float]
    score: float  # 0..1, 1 = reads like AI
    highlights: list[Highlight] = field(default_factory=list)


def find_highlights(text: str) -> list[Highlight]:
    text = normalize(text)
    found: list[Highlight] = []
    for m in RE_CONNECTOR.finditer(text):
        found.append(Highlight(m.start(2), m.end(2), "connector"))
    for m in RE_CLICHE.finditer(text):
        found.append(Highlight(m.start(), m.end(), "cliche"))
    for m in RE_HUMAN.finditer(text):
        found.append(Highlight(m.start(), m.end(), "human"))
    found.sort(key=lambda h: (h.start, -(h.end - h.start)))
    merged, pos = [], 0
    for h in found:
        if h.start >= pos:
            merged.append(h)
            pos = h.end
    return merged


def analyze(text: str) -> HeuristicResult:
    text = normalize(text)
    w = words(text)
    n = len(w)
    sents = split_sentences(text)
    lens = [s.n_words for s in sents]
    mean = sum(lens) / len(lens) if lens else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens)) if lens else 0.0
    cv = sd / mean if mean else 0.0

    # MATTR: share of distinct words, averaged over a sliding 50-word window
    win = min(50, n)
    mattr = 0.0
    if n >= 10:
        vals = [len(set(w[i:i + win])) / win for i in range(0, n - win + 1, 5)]
        mattr = sum(vals) / len(vals)

    tri: dict[tuple, int] = {}
    for i in range(n - 2):
        g = (w[i], w[i + 1], w[i + 2])
        tri[g] = tri.get(g, 0) + 1
    tri_rep = sum(c for c in tri.values() if c > 1) / max(1, n - 2)

    per100 = (lambda x: x / n * 100) if n else (lambda x: 0.0)
    n_cliche = len(RE_CLICHE.findall(text))
    n_conn = len(RE_CONNECTOR.findall(text))
    n_human = len(RE_HUMAN.findall(text)) + len(RE_PUNCT.findall(text))
    cliche_rate = per100(n_cliche)
    conn_rate = n_conn / len(sents) if sents else 0.0
    human_rate = per100(n_human)

    signals = {
        "burstiness": 1 - _lin(cv, 0.30, 0.75),
        "cliches": _lin(cliche_rate, 0.5, 4.0),
        "connectors": _lin(conn_rate, 0.05, 0.30),
        "human_voice": 1 - _lin(human_rate, 0.5, 4.0),
        "diversity": 1 - _lin(mattr, 0.62, 0.85),
        "repetition": _lin(tri_rep, 0.02, 0.15),
    }
    score = sum(WEIGHTS[k] * v for k, v in signals.items())
    stats = {
        "mean_sentence_len": mean,
        "sentence_len_cv": cv,
        "mattr": mattr,
        "trigram_repeat": tri_rep,
        "cliches": n_cliche,
        "cliches_per_100": cliche_rate,
        "connector_sentences": n_conn,
        "connector_ratio": conn_rate,
        "human_markers": n_human,
        "human_per_100": human_rate,
    }
    return HeuristicResult(n, len(sents), lens, stats, signals, score, find_highlights(text))
