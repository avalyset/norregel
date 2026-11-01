"""Token usage and API cost from Inspect logs (docs/RUN_PROTOCOL.md section 4). No model is called.

  python scripts/cost_usage.py logs/pilot logs/run_v1 [--cap 60] [--json out.json]

Cost per log file = usage in the log header (`stats.model_usage`, which counts every generate call
including retries); for a log that has no final stats (a run still going or killed) the sum of the
sample usages is used. Logs written by `inspect eval-retry` repeat the usage of their earlier
attempt, so the total can only overstate spend. Cached tokens are not used by these runs.
Reasoning tokens are part of output_tokens for Anthropic models and are billed as output.

Prices are USD per million tokens, read from https://platform.claude.com/docs/en/about-claude/pricing
on 2026-10-16 (see docs/MODELLER.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PRICE = {  # model -> (input, output) USD / MTok
    "anthropic/claude-haiku-4-5-20251001": (1.0, 5.0),
    "anthropic/claude-sonnet-4-6": (3.0, 15.0),
    "anthropic/claude-opus-5-5": (4.0, 20.0),
}


def usage_of_log(path: Path):
    from inspect_ai.log import read_eval_log
    log = read_eval_log(str(path))
    stats = getattr(log, "stats", None)
    mu = dict(getattr(stats, "model_usage", None) or {})
    src = "header"
    if not mu:
        src = "samples"
        for s in log.samples or []:
            for m, u in (s.model_usage or {}).items():
                a = mu.setdefault(m, {"input_tokens": 0, "output_tokens": 0})
                a["input_tokens"] += u.input_tokens or 0
                a["output_tokens"] += u.output_tokens or 0
        return log, mu, src
    return log, {m: {"input_tokens": u.input_tokens or 0, "output_tokens": u.output_tokens or 0} for m, u in mu.items()}, src


def collect(roots: list[str]) -> dict:
    out = {"files": [], "by_model": {}, "total_usd": 0.0}
    for root in roots:
        for p in sorted(Path(root).rglob("*.eval")):
            try:
                log, mu, src = usage_of_log(p)
            except Exception as e:  # file being written
                out["files"].append({"file": str(p), "error": repr(e)[:120]})
                continue
            n = len(log.samples or [])
            for m, u in mu.items():
                pin, pout = PRICE.get(m, (0.0, 0.0))
                usd = (u["input_tokens"] * pin + u["output_tokens"] * pout) / 1e6
                out["files"].append({"file": str(p), "task": log.eval.task, "model": m, "status": log.status,
                                     "samples": n, "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"],
                                     "usd": usd, "source": src})
                b = out["by_model"].setdefault(m, {"input_tokens": 0, "output_tokens": 0, "usd": 0.0})
                b["input_tokens"] += u["input_tokens"]
                b["output_tokens"] += u["output_tokens"]
                b["usd"] += usd
                out["total_usd"] += usd
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--cap", type=float)
    ap.add_argument("--json")
    a = ap.parse_args()
    r = collect(a.roots)
    for f in r["files"]:
        if "error" in f:
            print(f"  (unreadable) {f['file']}: {f['error']}")
        elif f["usd"] or f["model"] in PRICE:
            print(f"  {f['model']:40s} {f['task']:16s} {f['status']:8s} n={f['samples']:4d} in={f['input_tokens']:8d} "
                  f"out={f['output_tokens']:8d} ${f['usd']:.4f} [{f['source']}]")
    for m, b in r["by_model"].items():
        if b["usd"]:
            print(f"{m}: in={b['input_tokens']} out={b['output_tokens']} ${b['usd']:.4f}")
    print(f"TOTAL ${r['total_usd']:.4f}" + (f" (cap {a.cap})" if a.cap else ""))
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=1))
    return 1 if a.cap and r["total_usd"] >= a.cap else 0


if __name__ == "__main__":
    sys.exit(main())
