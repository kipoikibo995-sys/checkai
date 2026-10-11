"""Dấu hiệu văn phong, không cần mô hình: chạy được ở mọi máy, kể cả không có GPU.

Mỗi dấu hiệu trả về một giá trị 0..1, trong đó 1 nghĩa là "giống văn AI".
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

CLICHES = [
    "trong thế giới", "ngày nay", "đóng vai trò quan trọng", "vai trò quan trọng",
    "không chỉ", "mà còn", "hành trình", "khám phá", "trải nghiệm", "đầy ý nghĩa",
    "sâu sắc", "tỉ mỉ", "chìa khóa", "chìa khoá", "nâng tầm", "lan tỏa", "lan toả",
    "giá trị tích cực", "đa dạng", "tối ưu", "hiệu quả", "một cách",
    "không thể phủ nhận", "điều quan trọng là", "đáp ứng nhu cầu", "ngày càng",
    "tuyệt vời", "tuyệt đẹp", "hấp dẫn", "đồng hành", "nguồn cảm hứng",
    "truyền cảm hứng", "động lực", "hãy cùng", "đừng quên", "bất kỳ", "góp phần",
    "mang đến", "mang lại", "nhằm", "giúp bạn", "tìm thấy", "kết nối", "thông điệp",
    "bí quyết", "toàn diện", "vượt trội", "đột phá",
    "in today's world", "delve", "tapestry", "it's important to note",
    "it is important to note", "in conclusion", "navigate", "landscape", "embark",
    "journey", "unlock", "elevate", "seamless", "vibrant", "testament",
    "plays a crucial role", "crucial", "pivotal", "foster", "realm",
]

CONNECTORS = [
    "bên cạnh đó", "hơn nữa", "ngoài ra", "tóm lại", "nhìn chung", "cuối cùng",
    "thêm vào đó", "đặc biệt", "không những thế", "vì vậy", "do đó", "tuy nhiên",
    "nói tóm lại", "trước hết", "đầu tiên", "thứ hai",
    "moreover", "furthermore", "additionally", "however", "overall", "in addition",
    "firstly", "finally", "ultimately",
]

HUMAN_MARKERS = [
    "mình", "tui", "tớ", "bọn mình", "tụi mình", "nhé", "nha", "nhỉ", "ạ", "á",
    "hả", "hở", "đấy", "đó", "thôi", "luôn", "chả", "chẳng", "kiểu", "ủa", "ơi",
    "trời", "haha", "hihi", "kkk", "lol", "chứ", "mà", "vậy", "chắc", "hồi", "đứa",
    "tao", "mày",
]

# Trọng số khi gộp các dấu hiệu thành một điểm (tổng = 1).
WEIGHTS = {
    "burstiness": 0.22,
    "cliches": 0.28,
    "connectors": 0.15,
    "human_voice": 0.17,
    "diversity": 0.09,
    "repetition": 0.09,
}


def _alt(phrases: list[str]) -> str:
    return "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))


RE_CLICHE = re.compile(rf"(?<!\w)({_alt(CLICHES)})(?!\w)", re.IGNORECASE)
RE_HUMAN = re.compile(rf"(?<!\w)({_alt(HUMAN_MARKERS)})(?!\w)", re.IGNORECASE)
RE_CONNECTOR = re.compile(rf"(^|[.!?…\n]\s*)({_alt(CONNECTORS)})(?!\w)", re.IGNORECASE)
RE_WORD = re.compile(r"[\w']+")
RE_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")
RE_PUNCT = re.compile(r"[?!]|\.\.\.|…")


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
    """0 khi x <= lo, 1 khi x >= hi, tuyến tính ở giữa."""
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
    score: float  # 0..1, 1 = giống AI
    highlights: list[Highlight] = field(default_factory=list)


def find_highlights(text: str) -> list[Highlight]:
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
    w = words(text)
    n = len(w)
    sents = split_sentences(text)
    lens = [s.n_words for s in sents]
    mean = sum(lens) / len(lens) if lens else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens)) if lens else 0.0
    cv = sd / mean if mean else 0.0

    # MATTR: tỉ lệ chữ khác nhau, trung bình trên cửa sổ trượt 50 chữ
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
