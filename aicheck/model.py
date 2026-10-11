"""Score text with a real language model, using the Binoculars method.

Idea (Hans et al., 2024, "Spotting LLMs With Binoculars"):
  - log-perplexity: how predictable the text is to the model. AI text is usually very predictable.
  - cross-perplexity: how predictable the model expects text to be at each position.
  - Binoculars score = log-perplexity / cross-perplexity. Lower means more AI-like.

Dividing by cross-perplexity avoids false alarms on topics that are naturally predictable
(boilerplate, formal writing), because both numbers drop together. A base/instruct pair that
shares one vocabulary works best; a single model also works but is less accurate.

Requires: pip install torch transformers
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Suggested model pairs. Qwen2.5 handles English well and ships base and instruct versions.
PRESETS = {
    "light": ("Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B-Instruct"),     # ~4 GB RAM, runs on CPU
    "standard": ("Qwen/Qwen2.5-1.5B", "Qwen/Qwen2.5-1.5B-Instruct"),  # ~12 GB RAM or an 8 GB GPU
    "strong": ("Qwen/Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),        # needs a 24 GB+ GPU
}


@dataclass
class LMSentence:
    start: int
    end: int
    tokens: int
    log_ppl: float
    x_ppl: float

    @property
    def binoculars(self) -> float:
        return self.log_ppl / self.x_ppl if self.x_ppl else float("nan")


@dataclass
class LMResult:
    tokens: int
    log_ppl: float
    x_ppl: float
    truncated: bool
    sentences: list[LMSentence] = field(default_factory=list)

    @property
    def perplexity(self) -> float:
        import math
        return math.exp(self.log_ppl)

    @property
    def binoculars(self) -> float:
        return self.log_ppl / self.x_ppl if self.x_ppl else float("nan")


class BinocularsScorer:
    def __init__(self, observer: str, performer: str | None = None, device: str | None = None,
                 max_tokens: int = 4096, window: int = 512):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("Model libraries are not installed. Run: pip install torch transformers") from e

        self.torch = torch
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        dtype = torch.bfloat16 if device == "cuda" else torch.float32

        self.observer_name = observer
        self.performer_name = performer or observer
        self.tokenizer = AutoTokenizer.from_pretrained(observer)
        if not self.tokenizer.is_fast:
            raise RuntimeError("A 'fast' tokenizer is required to score individual sentences.")

        def load(name):
            try:
                m = AutoModelForCausalLM.from_pretrained(name, dtype=dtype)
            except TypeError:  # transformers older than 4.56
                m = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dtype)
            return m.to(device).eval()

        self.observer = load(observer)
        self.performer = load(performer) if performer and performer != observer else self.observer
        if self.observer.config.vocab_size != self.performer.config.vocab_size:
            raise RuntimeError("Both models must share a vocabulary (use the same model family).")
        self.max_tokens = max_tokens
        self.window = window

    @property
    def model_key(self) -> str:
        return f"{self.observer_name}|{self.performer_name}"

    def _token_scores(self, ids):
        """Per-token (loss, cross-entropy), computed in windows so long texts fit in memory."""
        torch = self.torch
        F = torch.nn.functional
        losses, xents = [], []
        # Windows overlap by one token so every token except the first has context.
        for s in range(0, len(ids) - 1, self.window):
            chunk = ids[s:s + self.window + 1].unsqueeze(0).to(self.device)
            if chunk.shape[1] < 2:
                break
            with torch.inference_mode():
                obs = self.observer(chunk).logits[0, :-1].float()
                perf = obs if self.performer is self.observer else self.performer(chunk).logits[0, :-1].float()
            target = chunk[0, 1:]
            losses.append(F.cross_entropy(perf, target, reduction="none").cpu())
            xents.append(-(F.softmax(obs, -1) * F.log_softmax(perf, -1)).sum(-1).cpu())
        return torch.cat(losses), torch.cat(xents)

    def score(self, text: str, spans: list[tuple[int, int]] | None = None) -> LMResult:
        torch = self.torch
        enc = self.tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        ids = enc["input_ids"]
        offsets = enc["offset_mapping"]
        truncated = len(ids) > self.max_tokens
        ids, offsets = ids[:self.max_tokens], offsets[:self.max_tokens]
        bos = self.tokenizer.bos_token_id
        if bos is None:
            bos = self.tokenizer.eos_token_id
        # Prepend a start token so the first real token is scored too.
        ids_t = torch.tensor([bos] + ids, dtype=torch.long)
        loss, xent = self._token_scores(ids_t)  # loss[i] belongs to ids[i]
        n = min(len(ids), len(loss))
        if n == 0:
            raise ValueError("Text is too short to score with the model.")
        loss, xent = loss[:n], xent[:n]
        result = LMResult(n, float(loss.mean()), float(xent.mean()), truncated)

        for (a, b) in spans or []:
            idx = [i for i in range(n) if offsets[i][1] > a and offsets[i][0] < b]
            if len(idx) >= 3:
                sel = torch.tensor(idx)
                result.sentences.append(LMSentence(a, b, len(idx), float(loss[sel].mean()), float(xent[sel].mean())))
        return result
