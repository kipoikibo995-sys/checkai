"""Command line:  python -m aicheck {check,serve,calibrate} ..."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .detector import Detector, calibrate
from .heuristics import SIGNAL_LABELS


def build_scorer(args):
    if args.no_model:
        return None
    from .model import PRESETS, BinocularsScorer
    observer, performer = PRESETS[args.preset]
    observer = args.observer or observer
    performer = args.performer or (performer if not args.observer else None)
    if args.single:
        performer = None
    print(f"Loading {observer}" + (f" + {performer}" if performer else "") + " ...", file=sys.stderr)
    return BinocularsScorer(observer, performer, device=args.device, max_tokens=args.max_tokens)


def read_inputs(paths: list[str]) -> list[tuple[str, str]]:
    if not paths or paths == ["-"]:
        return [("stdin", sys.stdin.read())]
    out = []
    for p in paths:
        path = Path(p)
        files = sorted(path.rglob("*.txt")) if path.is_dir() else [path]
        out += [(str(f), f.read_text("utf-8")) for f in files]
    return out


def bar(p: float, width: int = 30) -> str:
    k = round(p * width)
    return "█" * k + "░" * (width - k)


def print_report(name: str, r) -> None:
    print(f"\n=== {name} ===")
    print(f"AI probability: {r.ai_probability * 100:5.1f}%  {bar(r.ai_probability)}  {r.verdict}")
    print(f"{r.words} words, {r.sentences_count} sentences. Style score: {r.heuristic_score * 100:.0f}/100")
    if r.model:
        m = r.model
        print(f"Model: Binoculars = {m['binoculars']:.3f} (threshold {m['threshold']:.3f}"
              f"{'' if m['calibrated'] else ', not calibrated'}), perplexity = {m['perplexity']:.1f}")
    for k, v in r.signals.items():
        print(f"  {SIGNAL_LABELS[k]:<22} {bar(v, 15)} {v * 100:3.0f}")
    scored = [s for s in r.sentences if s.ai_probability is not None]
    if scored:
        print("Most AI-like sentences:")
        for s in sorted(scored, key=lambda s: -s.ai_probability)[:3]:
            print(f"  {s.ai_probability * 100:4.0f}%  {s.text[:110]}")
    for w in r.warnings:
        print(f"! {w}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="aicheck", description="Check whether text was written by AI or a person.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def model_opts(p):
        p.add_argument("--no-model", action="store_true", help="use writing-style signals only, no model download")
        p.add_argument("--preset", choices=["light", "standard", "strong"], default="light",
                       help="model pair (default: light)")
        p.add_argument("--observer", help="base model name or folder (overrides the preset)")
        p.add_argument("--performer", help="instruct model name or folder (overrides the preset)")
        p.add_argument("--single", action="store_true", help="use one model only, half the memory")
        p.add_argument("--device", help="cpu, cuda or mps (default: auto)")
        p.add_argument("--max-tokens", type=int, default=4096)

    c = sub.add_parser("check", help="check .txt files, folders, or text from stdin")
    c.add_argument("paths", nargs="*", help="files or folders; leave empty to read stdin")
    c.add_argument("--json", action="store_true", help="print results as JSON")
    model_opts(c)

    s = sub.add_parser("serve", help="open the web app")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    model_opts(s)

    k = sub.add_parser("calibrate", help="tune the threshold with your own samples")
    k.add_argument("--human", required=True, help="folder of .txt files written by people")
    k.add_argument("--ai", required=True, help="folder of .txt files written by AI")
    model_opts(k)

    args = ap.parse_args(argv)

    if args.cmd == "calibrate":
        if args.no_model:
            ap.error("calibration needs a model")
        scorer = build_scorer(args)
        hum = [t for _, t in read_inputs([args.human])]
        ai = [t for _, t in read_inputs([args.ai])]
        if len(hum) < 2 or len(ai) < 2:
            ap.error("need at least 2 files of each kind (20+ recommended)")
        d = calibrate(scorer, hum, ai)
        print(f"New threshold: {d['threshold']:.3f}  (balanced accuracy on your samples: {d['balanced_accuracy'] * 100:.0f}%)")
        print(f"Mean Binoculars score: human {d['human_mean']:.3f}, AI {d['ai_mean']:.3f}")
        return

    detector = Detector(build_scorer(args))

    if args.cmd == "serve":
        from .server import serve
        serve(detector, args.host, args.port)
        return

    results = []
    for name, text in read_inputs(args.paths):
        r = detector.check(text)
        if args.json:
            results.append({"file": name, **r.to_dict()})
        else:
            print_report(name, r)
    if args.json:
        print(json.dumps(results if len(results) != 1 else results[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
