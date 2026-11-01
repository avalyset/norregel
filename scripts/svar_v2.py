"""Build the v2 answer file and tables T1, T2 and T18 from the Inspect logs (docs/PREREG_V2.md, sections 6 and 11).

Log layout: logs/run_v2/<model id with / and : replaced by __ and _>/k<r>/*.eval for run r (r = 1..R; r = 2 is the control
run for a model with R = 1). A directory may hold a file GRUNN.md whose first line gives the reason for every log in it
that is not primary (table T2).

Both tasks run as `norregel_v2` in src/norregel/inspect_task_v2.py; the main task with the default items (dataset name
`items`) and H3 with `-T items=data/items_h3_v2.jsonl -T shuffle_seed=20261117` (dataset name `items_h3_v2`).

Primary log per (model, task, run): the first complete log in file-name order. Complete = log status `success`, exactly
the expected sample ids, and every sample scored or in error (v1 run protocol 3.4). Expected ids: main task = the 916 ids
of data/items.jsonl; H3 = the ids of data/items_h3_v2.jsonl; control run = the 100 control ids on the main task only.
A model without a complete primary log for run 1 of a task is not complete for that task (no other run takes its place).

Model settings: docs/v2_modeller.json as amended by the pilot rules (logs/run_v2/pilot_utfall.json from
scripts/pilot_regler_v2.py: temperature, R, models taken out). A model taken out is listed in T1 with the reason and has no runs.

Outputs (into --out-dir): v2_modeller_komplette.json (the models complete on both tasks in run 1, with the amended settings
and `komplette_kjøringer`, the runs complete on every task they cover: the model list for scripts/analysis_v2.py); answers_v2.jsonl {"model", "id", "run", "completion", "error", "stop_reason"}; svar_v2_tabeller.json
with T1 (status per model, task and run), T2 (every log that is not primary, with classes under scorer v2) and T18 (tokens
and USD per model, prices from docs/v2_kandidater.json). No model is called.

  .venv/bin/python -I scripts/svar_v2.py --logs logs/run_v2 --out-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_v2 as A2  # noqa: E402

TASKS = {"main": ("norregel_v2", "items"), "h3": ("norregel_v2", "items_h3_v2")}  # (Inspect task, dataset name)
CONTROL_SEED, CONTROL_N = 20261118, 100


def safe_dir(model_id: str) -> str:
    return model_id.replace("/", "__").replace(":", "_")


def utc(t: str | None) -> str | None:
    return datetime.fromisoformat(t).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if t else None


def control_ids() -> list[str]:
    items = [i["id"] for i in A2.load("items.jsonl")]
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    return random.Random(CONTROL_SEED).sample(sorted(i for i in items if i not in set(ex["excluded_items"])), CONTROL_N)


def main() -> None:
    from inspect_ai.log import read_eval_log
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="logs/run_v2")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--pilot-utfall", default="logs/run_v2/pilot_utfall.json")
    a = ap.parse_args()
    logs, out = ROOT / a.logs, Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    models = json.loads((ROOT / "docs" / "v2_modeller.json").read_text(encoding="utf-8"))
    pu = ROOT / a.pilot_utfall
    eff = {e["id"]: e for e in json.loads(pu.read_text(encoding="utf-8"))["modeller"]} if pu.exists() else {}
    taken_out = []
    for m in models:
        e = eff.get(m["id"])
        if e:
            m["temperature0"], m["runs"] = e["temperature0"], e["runs"]
            if e["tatt_ut"]:
                taken_out.append((m, e["grunn"]))
    models = [m for m in models if m not in [x for x, _ in taken_out]]
    items = {i["id"]: i for i in A2.load("items.jsonl")}
    h3 = {i["id"]: i for i in (json.loads(l) for l in (ROOT / "data" / "items_h3_v2.jsonl").open(encoding="utf-8"))}
    pool = {**items, **h3}
    rejected = A2.rejected_values({i["serie_id"] for i in items.values()})
    ctrl = set(control_ids())
    prices = {c["inspect_id"]: c.get("price_usd_per_mtok") for c in
              json.loads((ROOT / "docs" / "v2_kandidater.json").read_text(encoding="utf-8"))["candidates"]}
    answers, t1, t2, tokens = [], [], [], Counter()
    for m in models:
        n_runs = m["runs"] + (1 if m["runs"] == 1 else 0)
        for r in range(1, n_runs + 1):
            control = m["runs"] == 1 and r == 2
            d = logs / safe_dir(m["id"]) / f"k{r}"
            reason = (d / "GRUNN.md").read_text(encoding="utf-8").splitlines()[0] if (d / "GRUNN.md").exists() else "ikke oppgitt"
            matched = set()
            for key, (task, dataset) in TASKS.items():
                if control and key != "main":
                    continue
                expected = ctrl if control else (set(items) if key == "main" else set(h3))
                logs_k = [p for p in sorted(d.glob("*.eval"))] if d.exists() else []
                primary = None
                attempts = []
                for p in logs_k:
                    lg = read_eval_log(str(p))
                    if lg.eval.task != task or lg.eval.dataset.name != dataset:
                        continue
                    matched.add(p)
                    attempts.append((p, lg))
                    got = {s.id for s in lg.samples or []}
                    ok = lg.status == "success" and got == expected and all(s.scores or s.error for s in lg.samples)
                    if ok and primary is None:
                        primary = (p, lg)
                for p, lg in attempts:
                    u = lg.stats.model_usage or {}
                    for mu in u.values():
                        tokens[(m["id"], "inn")] += mu.input_tokens or 0
                        tokens[(m["id"], "ut")] += mu.output_tokens or 0
                    if primary and p == primary[0]:
                        continue
                    cls = Counter(A2.classify({"completion": s.output.completion if (s.output and not s.error) else "", "error": s.error is not None},
                                              pool[s.id], rejected)["klasse"] for s in lg.samples or [] if s.id in pool)
                    t2.append({"logg": p.name, "eval_id": lg.eval.eval_id, "oppgave": f"{task} ({dataset})", "modell": m["id"], "kjøring": r,
                               "start": utc(lg.stats.started_at), "slutt": utc(lg.stats.completed_at), "status": lg.status,
                               "samples": len(lg.samples or []), "feil": sum(1 for s in lg.samples or [] if s.error),
                               "avkortet": sum(1 for s in lg.samples or [] if not s.error and s.output and s.output.stop_reason == "max_tokens"),
                               "klasser": {c: cls[c] for c in A2.CLASSES}, "grunn": reason})
                row = {"modell": m["id"], "oppgave": f"{task} ({dataset})", "kjøring": r, "kontrollkjøring": control, "forsøk": len(attempts),
                       "komplett": primary is not None}
                if primary:
                    p, lg = primary
                    row.update(logg=p.name, start=utc(lg.stats.started_at), slutt=utc(lg.stats.completed_at), samples=len(lg.samples),
                               endelige_feil=sum(1 for s in lg.samples if s.error),
                               avkortet=sum(1 for s in lg.samples if not s.error and s.output and s.output.stop_reason == "max_tokens"))
                    for s in lg.samples:
                        answers.append({"model": m["id"], "id": s.id, "run": r,
                                        "completion": s.output.completion if (s.output and not s.error) else "",
                                        "error": s.error is not None, "stop_reason": None if s.error or not s.output else s.output.stop_reason})
                t1.append(row)
            for p in sorted(d.glob("*.eval")) if d.exists() else []:  # every log is reported: one of no expected task too
                if p not in matched:
                    lg = read_eval_log(str(p), header_only=True)
                    t2.append({"logg": p.name, "eval_id": lg.eval.eval_id, "oppgave": f"{lg.eval.task} ({lg.eval.dataset.name})",
                               "modell": m["id"], "kjøring": r, "start": utc(lg.stats.started_at), "slutt": utc(lg.stats.completed_at),
                               "status": lg.status, "samples": None, "feil": None, "avkortet": None, "klasser": None,
                               "grunn": f"ingen forventet oppgave i k{r}; {reason}"})
    for m, why in taken_out:
        t1.append({"modell": m["id"], "oppgave": None, "kjøring": None, "kontrollkjøring": False, "forsøk": 0, "komplett": False,
                   "tatt_ut": why})
    t18 = {}
    for m in models:
        pr = prices.get(m["id"]) or {"input": 0, "output": 0}
        i, o = tokens[(m["id"], "inn")], tokens[(m["id"], "ut")]
        t18[m["id"]] = {"inn": i, "ut": o, "usd": (i * pr["input"] + o * pr["output"]) / 1e6}
    with (out / "answers_v2.jsonl").open("w", encoding="utf-8") as f:
        for x in answers:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    (out / "svar_v2_tabeller.json").write_text(json.dumps({"T1": t1, "T2": t2, "T18": t18}, ensure_ascii=False, indent=1), encoding="utf-8")
    # The model list for the analysis: the models complete on both tasks in run 1 (the others are only in T1, as in v1).
    complete = []
    for m in models:
        rows = [r for r in t1 if r["modell"] == m["id"]]
        if all(r["komplett"] for r in rows if r["kjøring"] == 1):
            runs = sorted({r["kjøring"] for r in rows})
            complete.append({**m, "komplette_kjøringer": [k for k in runs if all(r["komplett"] for r in rows if r["kjøring"] == k)]})
    (out / "v2_modeller_komplette.json").write_text(json.dumps(complete, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"answers: {len(answers)}; T1 rows: {len(t1)} ({sum(r['komplett'] for r in t1)} complete); T2 rows: {len(t2)}")


if __name__ == "__main__":
    main()
