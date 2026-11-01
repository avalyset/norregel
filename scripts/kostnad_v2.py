"""API cost of the v2 runs from the Inspect logs (docs/PREREG_V2.md, section 9). No model is called.

Usage per log is read as in v1 (scripts/cost_usage.py: the header's `stats.model_usage`, or the sum over the samples for
a log without final stats). Prices are USD per million tokens from docs/v2_kandidater.json (the providers' price pages,
fetched 17.10.2026). Output tokens include thinking tokens for both providers (Anthropic: docs/MODELLER.md; Google:
Inspect adds `thoughts_token_count` to `output_tokens`). Gemma 4 and the local models cost 0.

  .venv/bin/python -I scripts/kostnad_v2.py logs/run_v2 [--stop 380]

Exit code 1 when the total has reached --stop (the guard in scripts/run_v2.sh stops the API runs then).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cost_usage as cu  # noqa: E402

CAP, STOP = 400.0, 380.0  # cap (section 9) and the guard's stop level (95 % of the cap, as 56 of 60 in v1)


def prices() -> dict[str, tuple[float, float]]:
    cand = json.loads((ROOT / "docs" / "v2_kandidater.json").read_text(encoding="utf-8"))["candidates"]
    return {c["inspect_id"]: (c["price_usd_per_mtok"]["input"], c["price_usd_per_mtok"]["output"])
            for c in cand if c.get("price_usd_per_mtok")}


def collect(roots: list[Path]) -> dict:
    pr = prices()
    out = {"filer": [], "per_modell": {}, "usd": 0.0, "uleselige": 0}
    for root in roots:
        for p in sorted(root.rglob("*.eval")):
            try:
                log, mu, src = cu.usage_of_log(p)
            except Exception:  # a file still being written
                out["uleselige"] += 1
                continue
            for m, u in mu.items():
                pin, pout = pr.get(m, (0.0, 0.0))
                usd = (u["input_tokens"] * pin + u["output_tokens"] * pout) / 1e6
                out["filer"].append({"fil": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name, "modell": m,
                                     "status": log.status, "samples": len(log.samples or []), "inn": u["input_tokens"],
                                     "ut": u["output_tokens"], "usd": usd, "kilde": src})
                b = out["per_modell"].setdefault(m, {"inn": 0, "ut": 0, "usd": 0.0})
                b["inn"] += u["input_tokens"]; b["ut"] += u["output_tokens"]; b["usd"] += usd
                out["usd"] += usd
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--stop", type=float, default=STOP)
    a = ap.parse_args()
    r = collect([Path(x).resolve() for x in a.roots])
    for m, b in sorted(r["per_modell"].items()):
        print(f"{m}: inn={b['inn']} ut={b['ut']} {b['usd']:.4f} USD")
    print(f"TOTAL {r['usd']:.4f} USD (stopp {a.stop:.0f}, tak {CAP:.0f}; uleselige filer {r['uleselige']})")
    return 1 if r["usd"] >= a.stop else 0


if __name__ == "__main__":
    sys.exit(main())
