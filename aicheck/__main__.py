"""Dòng lệnh:  python -m aicheck {check,serve,calibrate} ..."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .detector import Detector, calibrate


def build_scorer(args):
    if args.no_model:
        return None
    from .model import PRESETS, BinocularsScorer
    observer, performer = PRESETS[args.preset]
    observer = args.observer or observer
    performer = args.performer or (performer if not args.observer else None)
    if args.single:
        performer = None
    print(f"Đang tải mô hình {observer}" + (f" + {performer}" if performer else "") + " ...", file=sys.stderr)
    return BinocularsScorer(observer, performer, device=args.device, max_tokens=args.max_tokens)


def read_inputs(paths: list[str]) -> list[tuple[str, str]]:
    if not paths or paths == ["-"]:
        return [("stdin", sys.stdin.read())]
    out = []
    for p in paths:
        path = Path(p)
        files = sorted(x for x in path.rglob("*.txt")) if path.is_dir() else [path]
        out += [(str(f), f.read_text("utf-8")) for f in files]
    return out


def bar(p: float, width: int = 30) -> str:
    k = round(p * width)
    return "█" * k + "░" * (width - k)


def print_report(name: str, r) -> None:
    print(f"\n=== {name} ===")
    print(f"Xác suất do AI viết: {r.ai_probability * 100:5.1f}%  {bar(r.ai_probability)}  {r.verdict}")
    print(f"{r.words} chữ, {r.sentences_count} câu. Điểm dấu hiệu văn phong: {r.heuristic_score * 100:.0f}/100")
    if r.model:
        m = r.model
        print(f"Mô hình: Binoculars = {m['binoculars']:.3f} (ngưỡng {m['threshold']:.3f}"
              f"{'' if m['calibrated'] else ', chưa hiệu chỉnh'}), perplexity = {m['perplexity']:.1f}")
    names = {"burstiness": "Câu dài đều nhau", "cliches": "Cụm từ sáo rỗng", "connectors": "Từ nối đầu câu",
             "human_voice": "Thiếu giọng nói thật", "diversity": "Lặp từ vựng", "repetition": "Lặp cụm 3 chữ"}
    for k, v in r.signals.items():
        print(f"  {names[k]:<22} {bar(v, 15)} {v * 100:3.0f}")
    scored = [s for s in r.sentences if s.ai_probability is not None]
    if scored:
        print("Câu giống AI nhất:")
        for s in sorted(scored, key=lambda s: -s.ai_probability)[:3]:
            print(f"  {s.ai_probability * 100:4.0f}%  {s.text[:110]}")
    for w in r.warnings:
        print(f"! {w}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="aicheck", description="Kiểm tra văn bản do AI hay người viết.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def model_opts(p):
        p.add_argument("--no-model", action="store_true", help="chỉ dùng dấu hiệu văn phong, không tải mô hình")
        p.add_argument("--preset", choices=["nhe", "chuan", "manh"], default="nhe", help="cặp mô hình (mặc định: nhe)")
        p.add_argument("--observer", help="tên hoặc thư mục mô hình base (ghi đè preset)")
        p.add_argument("--performer", help="tên hoặc thư mục mô hình instruct (ghi đè preset)")
        p.add_argument("--single", action="store_true", help="chỉ dùng một mô hình, tiết kiệm bộ nhớ")
        p.add_argument("--device", help="cpu, cuda hoặc mps (mặc định tự chọn)")
        p.add_argument("--max-tokens", type=int, default=4096)

    c = sub.add_parser("check", help="kiểm tra tệp .txt, thư mục, hoặc văn bản từ bàn phím")
    c.add_argument("paths", nargs="*", help="tệp hoặc thư mục; bỏ trống để đọc từ stdin")
    c.add_argument("--json", action="store_true", help="in kết quả dạng JSON")
    model_opts(c)

    s = sub.add_parser("serve", help="mở giao diện web")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    model_opts(s)

    k = sub.add_parser("calibrate", help="hiệu chỉnh ngưỡng bằng văn mẫu của bạn")
    k.add_argument("--human", required=True, help="thư mục chứa các tệp .txt do người viết")
    k.add_argument("--ai", required=True, help="thư mục chứa các tệp .txt do AI viết")
    model_opts(k)

    args = ap.parse_args(argv)

    if args.cmd == "calibrate":
        if args.no_model:
            ap.error("hiệu chỉnh cần mô hình")
        scorer = build_scorer(args)
        hum = [t for _, t in read_inputs([args.human])]
        ai = [t for _, t in read_inputs([args.ai])]
        if len(hum) < 2 or len(ai) < 2:
            ap.error("cần ít nhất 2 tệp mỗi loại (nên có từ 20 tệp trở lên)")
        d = calibrate(scorer, hum, ai)
        print(f"Ngưỡng mới: {d['threshold']:.3f}  (độ chính xác cân bằng trên mẫu: {d['balanced_accuracy'] * 100:.0f}%)")
        print(f"Trung bình Binoculars: người viết {d['human_mean']:.3f}, AI {d['ai_mean']:.3f}")
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
