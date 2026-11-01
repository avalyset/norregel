"""Driver for the norregel v1 analysis (docs/RUN_PROTOCOL.md sections 3.4, 3.5 and 6).

Reads the Inspect logs in logs/run_v1/<model>/, decides per model and task whether the run is complete,
writes the answers file, applies the «X år og Y måneder» decision (scripts/norm_aar_maaneder.py), calls the
reference implementation scripts/analysis_v1.py unchanged, and writes docs/RESULTS.md and docs/RESULTS.json.
No model is called, and no test or statistic is computed here that analysis_v1.py does not compute.

  python scripts/run_analysis.py [--logs logs/run_v1] [--out docs/RESULTS.md] [--json docs/RESULTS.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_v1 as A  # noqa: E402
import cost_usage  # noqa: E402
from norm_aar_maaneder import normalise  # noqa: E402

TASKS = {"main": "norregel_v2", "h3": "norregel_h3_v2"}
EXPECTED = {"main": 916, "h3": 400}
LOCKED_ANALYSIS_SHA = "78904e13e950e360346b6e8c654421a8f451160d0c58259017a3372f7a257c1d"
# The primary analysis ran at ANALYSIS_HEAD (A6), and its output was committed in RESULTS_COMMIT. While the analysis
# inputs are byte-identical to RESULTS_COMMIT, section 0 reports that binding; otherwise it reports the current HEAD.
ANALYSIS_HEAD = "1fd3406ba6e97f090937b478416d9ff70b6df6a9"
RESULTS_COMMIT = "8d2b7a07a2fa02a649c59706ea01ccdf87857a1e"
# docs/PILOT.md and docs/RESULTS_NOTES.md are text that goes into the report; they do not change any number.
ANALYSIS_INPUTS = ["scripts/analysis_v1.py", "scripts/norm_aar_maaneder.py", "scripts/cost_usage.py", "src", "data",
                   "docs/modeller.json", "logs"]
PUBLISHED_V11 = {"doi": "10.5281/zenodo.23432124",
                 "sha_modeller_md": "aa01a7c66f9463507ac72512853bb4cb25a199dcd2ecfabc53fcd9e03253b9da",
                 "sha_modeller_json": "cb76c3d02d0b0bf70f643ae05004b85d647d610449bc4ecf4a40e6d8b42db837"}
SHORT = {"anthropic/claude-haiku-4-5-20251001": "Haiku", "anthropic/claude-sonnet-4-6": "Sonnet",
         "anthropic/claude-opus-5-5": "Opus", "ollama/nb-llama-3.1-8b-instruct-cardtmpl:latest": "nb-llama",
         "ollama/normistral-7b-warm-instruct-cardtmpl:latest": "NorMistral"}
WORDS = {1: "én", 2: "to", 3: "tre", 4: "fire", 5: "fem", 6: "seks", 7: "sju", 8: "åtte", 9: "ni", 10: "ti"}
EARLIER_LOGS: dict = {}  # (model, task) -> [(log name, status, samples)] for the logs before the primary one
RUN_TIMES: dict = {}  # (model, task) -> (started_at, completed_at) of the primary log
PATHS_NOTE = ("Stier som `logs/`, `data/`, `docs/`, `scripts/` og `.venv/` viser til det lokale repoet. Logg- og datafilene og "
              "`.venv/` publiseres ikke; de filene under `docs/` og `scripts/` som er publisert, ligger med flate filnavn i "
              "Zenodo-postene for preregistreringen.")  # the same sentence heads docs/UTOLKET_REVISJON.md
MONTHS = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]
B_TOTAL = 10000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop_of(s) -> str | None:
    """stop_reason of a sample's output, None for a sample that ended in error (its output has no choices)."""
    return None if (s.error or not s.output or not s.output.choices) else s.output.stop_reason


def safe_dir(model_id: str) -> str:
    return model_id.replace("/", "__").replace(":", "_")


# ---------------------------------------------------------------------------------------- logs

def scan(logs_root: Path, models: list[dict]) -> tuple[dict, list[dict]]:
    """status[model][task] and the answers of the primary (first complete) log per model and task."""
    from inspect_ai.log import read_eval_log
    ids = {"main": {json.loads(l)["id"] for l in (ROOT / "data" / "items.jsonl").open(encoding="utf-8")},
           "h3": {json.loads(l)["id"] for l in (ROOT / "data" / "items_h3.jsonl").open(encoding="utf-8")}}
    status, answers = {}, []
    for m in models:
        status[m["id"]] = {}
        d = logs_root / safe_dir(m["id"])
        for key, task in TASKS.items():
            logs = []
            for p in sorted(d.glob("*.eval")) if d.exists() else []:
                try:
                    lg = read_eval_log(str(p))
                except Exception as e:  # unreadable log: counted as an attempt that did not complete
                    logs.append((p, None, repr(e)[:100]))
                    continue
                if lg.eval.task == task:
                    logs.append((p, lg, None))
            st = {"attempts": len(logs), "complete": False, "log": None, "status": "ikke kjørt", "samples": 0,
                  "errors": 0, "truncated": 0, "seconds": None, "all_logs": [str(p.relative_to(ROOT)) for p, _, _ in logs]}
            for p, lg, err in logs:
                got = {s.id for s in (lg.samples or [])} if lg else set()
                ok = (lg is not None and lg.status == "success" and got == ids[key]
                      and all(s.scores or s.error for s in lg.samples))
                st["status"], st["samples"] = (lg.status if lg else "uleselig"), len(got)
                if not ok:
                    EARLIER_LOGS.setdefault((m["id"], key), []).append((p.name, st["status"], st["samples"]))
                if ok:
                    st.update(complete=True, log=str(p.relative_to(ROOT)), status="komplett")
                    st["errors"] = sum(1 for s in lg.samples if s.error)
                    st["truncated"] = sum(1 for s in lg.samples if stop_of(s) == "max_tokens")
                    if lg.stats and lg.stats.started_at and lg.stats.completed_at:
                        RUN_TIMES[(m["id"], key)] = (lg.stats.started_at, lg.stats.completed_at)
                        from datetime import datetime
                        st["seconds"] = (datetime.fromisoformat(lg.stats.completed_at)
                                         - datetime.fromisoformat(lg.stats.started_at)).total_seconds()
                    for s in lg.samples:
                        answers.append({"model": lg.eval.model, "id": s.id, "task": key, "stop_reason": stop_of(s),
                                        "completion": s.output.completion if (s.output and not s.error) else "",
                                        "error": s.error is not None})
                    break
            else:
                if logs:
                    st["status"] = "ufullstendig" if st["attempts"] >= 2 else f"ikke komplett ({st['status']}, {st['samples']} samples)"
            status[m["id"]][key] = st
    return status, answers


def apply_normalisation(answers: list[dict]) -> Counter:
    types = {}
    for name in ("items.jsonl", "items_h3.jsonl"):
        for i in A.load(name):
            types[i["id"]] = i["type"]
    changed = Counter()
    for a in answers:
        new, ch = normalise(a["completion"], types[a["id"]])
        if ch:
            a["completion_original"], a["completion"] = a["completion"], new
            changed[a["model"]] += 1
    return changed


# ------------------------------------------------------------------------------------ analysis

def run_all(models: list[dict], status: dict, answers: list[dict]) -> dict:
    main_models = [m for m in models if status[m["id"]]["main"]["complete"]]
    h3_models = [m for m in models if status[m["id"]]["h3"]["complete"]]
    out = {}
    for name, scorer, subset in (("primary_v2", "v2", "primary"), ("sensitivity1_all916_v2", "v2", "all916"),
                                 ("sensitivity2_v1", "v1", "primary"), ("sensitivity3_v2", "v2", "sensitivity3")):
        t0 = time.time()
        rep = A.analyse(main_models, answers, scorer, subset) if main_models else {"models": {}}
        if h3_models and [m["id"] for m in h3_models] != [m["id"] for m in main_models]:
            rh = A.analyse(h3_models, answers, scorer, subset)
        else:
            rh = rep
        for m in main_models:
            if m["id"] in rh["models"] and m in h3_models:
                rep["models"][m["id"]]["h3"] = rh["models"][m["id"]]["h3"]
            else:
                rep["models"][m["id"]]["h3"] = {"tested": False, "reason": "H3-kjøringen er ikke komplett"}
        out[name] = rep
        print(f"{name}: {time.time() - t0:.0f} s", flush=True)
    return out


# ------------------------------------------------------------------------------------ rendering

def nb(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def pct(x) -> str:
    return "—" if x is None else nb(100 * x) + " %"


def ci(lo, hi, scale: float = 100, d: int = 1) -> str:
    return "—" if lo is None else f"[{nb(lo * scale, d)}; {nb(hi * scale, d)}]"


def pv(p) -> str:
    return "—" if p is None else nb(p, 4)


def holm(r) -> str:
    return {True: "ja", False: "nei", None: "—"}[r.get("holm_reject")] if "holm_reject" in r else "—"


def model_name(m: dict) -> str:
    return f"`{m['id']}`"


def class_table(rep: dict, models: list[dict], title: str) -> list[str]:
    L = [f"#### {title}", "", "| Modell | n | Serier | Korrekt | Utdatert | Feil | Utolket |", "|---|---|---|---|---|---|---|"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r:
            continue
        p = r["primary"]
        cells = [f"{pct(p[c]['share'])} {ci(p[c]['lo95'], p[c]['hi95'])}" for c in A.CLASSES]
        L.append(f"| {model_name(m)} | {p['n']} | {p['series']} | " + " | ".join(cells) + " |")
    return L + ["", "Andel av alle svar, 95 % klyngebootstrap-intervall (prosent) i klammer.", ""]


def tests_tables(rep: dict, models: list[dict], holm_col: bool) -> list[str]:
    hc = " Holm |" if holm_col else ""
    hs = "---|" if holm_col else ""
    L = ["**H1** (andel utdatert etter minus før modellens cutoff, prosentpoeng)", "",
         f"| Modell | Cutoff | n etter / før | Serier etter / før | d | 95 % KI | Nedre 95 % (ensidig) | p (ensidig) |{hc}",
         f"|---|---|---|---|---|---|---|---|{hs}"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r:
            continue
        h = r["h1"]
        if "n_after" not in h:
            L.append(f"| {model_name(m)} | ingen | — | — | — | — | — | ikke testet (ingen cutoff) |" + (" — |" if holm_col else ""))
            continue
        flag = "" if h["tested"] else " (under minimum, ikke testet)"
        L.append(f"| {model_name(m)} | {m['cutoff']} | {h['n_after']} / {h['n_before']} | {h['series_after']} / {h['series_before']} | "
                 f"{'—' if h['d'] is None else nb(100 * h['d'])} | {ci(h.get('lo95'), h.get('hi95'))} | "
                 f"{'—' if h.get('lo90_onesided') is None else nb(100 * h['lo90_onesided'])} | {pv(h.get('p'))}{flag} |"
                 + (f" {holm(h)} |" if holm_col else ""))
    if holm_col:
        L += ["", "Sensitivitetsanalysen for H1 uten modeller med vag cutoff (RUN_PROTOCOL 3.2) er ikke beregnet separat. "
              f"Ingen av de {WORDS.get(len(models), len(models))} modellene har vag cutoff, så den er identisk med hovedanalysen."]
    has_h2 = any("h2" in rep["models"].get(m["id"], {}) for m in models)
    if has_h2:
        L += ["", "**H2** (andel utdaterte svar som er siste avvikende verdi)", "",
              f"| Modell | Utdaterte svar | Serier | s | 95 % KI | Nedre 95 % (ensidig) | p (ensidig, H0: s ≤ 0,5) |{hc}",
              f"|---|---|---|---|---|---|---|{hs}"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r or "h2" not in r:
            continue
        h = r["h2"]
        flag = "" if h["tested"] else " (under 30, ikke testet)"
        L.append(f"| {model_name(m)} | {h['n_outdated']} | {h['series']} | {pct(h['s'])} | {ci(h.get('lo95'), h.get('hi95'))} | "
                 f"{'—' if h.get('lo90_onesided') is None else pct(h['lo90_onesided'])} | {pv(h.get('p'))}{flag} |"
                 + (f" {holm(h)} |" if holm_col else ""))
    L += ["", "**H3** (nynorsk mot bokmål, parvis; b = bokmål korrekt og nynorsk ikke, c = omvendt)", "",
          f"| Modell | Par | Serier | b | c | p (eksakt McNemar, ensidig) | Forskjell nynorsk − bokmål (pp) | 95 % KI |{hc}",
          f"|---|---|---|---|---|---|---|---|{hs}"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r:
            continue
        h = r["h3"]
        if "pairs" not in h:
            L.append(f"| {model_name(m)} | — | — | — | — | {h['reason']} | — | — |" + (" — |" if holm_col else ""))
            continue
        L.append(f"| {model_name(m)} | {h['pairs']} | {h['series']} | {h['b']} | {h['c']} | "
                 f"{pv(h['p']) if h['tested'] else 'ikke testet (b + c = 0)'} | "
                 f"{'—' if h['diff_nn_minus_nb'] is None else nb(100 * h['diff_nn_minus_nb'])} | {ci(h.get('lo95'), h.get('hi95'))} |"
                 + (f" {holm(h)} |" if holm_col else ""))
    return L + [""]


def fs2_table(rep: dict, models: list[dict], itemset: str = "primærsettet") -> list[str]:
    L = [f"**FS2** (alder i år for utdaterte svar, {itemset}). FS2 er deskriptiv og uten test.", "",
         "| Modell | Utdaterte | Q1 | Median | Q3 | 95 % KI for median | 0 | 1 | 2 | 3 | 4 | 5 | 6–10 | >10 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r or "fs2" not in r:
            continue
        f = r["fs2"]
        b = f["bins"]
        if f["n_outdated"] == 0:
            L.append(f"| {model_name(m)} | 0 | — | — | — | — | " + " | ".join(str(b[k]) for k in b) + " |")
            continue
        mc = f["median_ci"]
        L.append(f"| {model_name(m)} | {f['n_outdated']} | {nb(f['q1'], 2)} | {nb(f['median'], 2)} | {nb(f['q3'], 2)} | "
                 f"{ci(mc['lo95'], mc['hi95'], 1, 2)} | " + " | ".join(str(b[k]) for k in b) + " |")
    return L + [""]


def count_table(rep: dict, models: list[dict], key: str, groups: list[str], title: str, labels: dict | None = None) -> list[str]:
    L = [f"#### {title}", "", "| Modell | Gruppe | n | Korrekt | Utdatert | Feil | Utolket |", "|---|---|---|---|---|---|---|"]
    for m in models:
        r = rep["models"].get(m["id"])
        if not r:
            continue
        for g in groups:
            c = r[key].get(g)
            if not c:
                continue
            L.append(f"| {model_name(m)} | {(labels or {}).get(g, g)} | {c['n']} | " + " | ".join(f"{c[k]['count']} ({pct(c[k]['share'])})" for k in A.CLASSES) + " |")
    return L + [""]


def examples(answers: list[dict], models: list[dict], status: dict, k: int = 4) -> list[str]:
    L = []
    for m in models:
        mid = m["id"]
        if not status[mid]["main"]["complete"]:
            continue
        items = {i["id"]: i for i in A.load("items.jsonl")}
        rows = [a for a in answers if a["model"] == mid and a["task"] == "main" and a["id"] in items]
        bad = [a for a in rows if a["error"] or A.classify(a, items[a["id"]], "v2")["klasse"] == "utolket"]
        L += [f"**{model_name(m)}** — utolket {len(bad)} av {len(rows)} svar i hele hovedoppgaven (916). Fire første (avkortet til 220 tegn):", ""]
        for a in bad[:k]:
            t = (a["completion"] or "(tom / endelig feil)").replace("\n", " ⏎ ")
            L.append(f"- `{a['id']}`: {t[:220]}{'…' if len(t) > 220 else ''}")
        L.append("")
    return L


def final_errors(models: list[dict], status: dict, answers: list[dict], n_primary: int, logs_dir: str) -> list[str]:
    """Final errors per model counted from the primary logs (protocol 3.4), with the primary log of each task."""
    excluded = set(json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["excluded_items"])
    L = ["#### Endelige feil (sample-feil etter forsøkene, skåret som utolket)", "",
         f"| Modell | Hovedsett ({n_primary} items) | Alle {EXPECTED['main']} items | H3 ({EXPECTED['h3']} samples) |", "|---|---|---|---|"]
    errs = {}
    for m in models:
        mine = [a for a in answers if a["model"] == m["id"] and a["error"]]
        main = sorted(a["id"] for a in mine if a["task"] == "main")
        h3 = sorted(a["id"] for a in mine if a["task"] == "h3")
        assert len(main) == status[m["id"]]["main"]["errors"] and len(h3) == status[m["id"]]["h3"]["errors"]
        errs[m["id"]] = (main, h3)
        L.append(f"| {model_name(m)} | {sum(1 for i in main if i not in excluded)} | {len(main)} | {len(h3)} |")
    text = (f"Talt direkte fra loggene i `{logs_dir}/`: samples med feil i primærloggen for oppgaven "
            "(første komplette logg, som i avsnitt 1).")
    for m in models:
        for key, task_name in (("main", "hovedoppgave"), ("h3", "H3")):
            earlier = EARLIER_LOGS.get((m["id"], key), [])
            if len(earlier) == 1 and status[m["id"]][key]["complete"]:
                name, st, n = earlier[0]
                what = {"cancelled": "avbrutte", "error": "feilede"}.get(st, "ufullstendige")
                text += (f" For {SHORT.get(m['id'], m['id'])} {task_name} er primærloggen eval-retry-loggen "
                         f"(`{Path(status[m['id']][key]['log']).name}`), ikke den {what} første loggen "
                         f"(`{name.split('_')[0]}_…`, {n} samples, `{st}`).")
    for m in models:
        main, h3 = errs[m["id"]]
        short = SHORT.get(m["id"], m["id"])
        if main:
            ids = main[0] if len(main) == 1 else ", ".join(main[:-1]) + " og " + main[-1]
            inside = sum(1 for i in main if i not in excluded)
            if len(main) == 1:
                text += f" Den ene {short}-feilen ({ids}) ligger {'i' if inside else 'utenfor'} hovedsettet."
            elif inside == len(main):
                text += f" De {WORDS.get(len(main), len(main))} {short}-feilene ({ids}) ligger alle i hovedsettet."
            else:
                text += f" Av de {len(main)} {short}-feilene ({ids}) ligger {inside} i hovedsettet."
        if h3:
            text += f" {short} har {len(h3)} endelige feil på H3 ({', '.join(h3)})."
    L += ["", text + " Primærlogger:", ""]
    for m in models:
        s = status[m["id"]]
        L.append(f"- {model_name(m)}: hovedoppgave `{s['main']['log']}`; H3 `{s['h3']['log']}`")
    return L + [""]


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def dropped_text(rep: dict, models: list[dict]) -> list[str]:
    """Number of dropped bootstrap resamples per interval (tillegget avsnitt 4, punkt 3)."""
    found = []
    for m in models:
        r = rep["models"].get(m["id"], {})
        stats = [(f"{c}", r["primary"][c]) for c in A.CLASSES if c in r.get("primary", {})]
        stats += [(h.upper(), r[h]) for h in ("h1", "h2", "h3") if isinstance(r.get(h), dict)]
        if isinstance(r.get("fs2"), dict):
            stats.append(("FS2-median", r["fs2"]))
        for name, s in stats:
            n = s.get("dropped_resamples") or 0
            if n:
                found.append(f"{name} {SHORT.get(m['id'], m['id'])}: {thousands(n)} forkastet av {thousands(B_TOTAL)}; "
                             f"intervallet bygger på {thousands(B_TOTAL - n)}.")
    text = "Forkastede resamples: " + (" ".join(found) + " Alle andre bootstrap-intervaller i avsnittet: 0 forkastet."
                                        if found else "0 for alle bootstrap-intervaller i avsnittet.")
    return [text, ""]


def wrong_split(rep: dict, models: list[dict], title: str) -> list[str]:
    L = [title, "", "| Modell | Feil totalt | Senere verdi | Verdi utenfor historikken |", "|---|---|---|---|"]
    for m in models:
        r = rep["models"][m["id"]]
        L.append(f"| {model_name(m)} | {r['feil_later_value'] + r['feil_not_in_history']} | {r['feil_later_value']} | {r['feil_not_in_history']} |")
    return L + [""]


TYPE_NAMES = {"belop": "kronebeløp", "prosent": "prosentsats", "alder": "aldersgrense", "g": "G-multippel"}


def type_legend(types: list[str]) -> str:
    return ", ".join(f"{t} = {TYPE_NAMES.get(t, t)}" for t in types)


def d13_text() -> str:
    """Overlapping runs of different API models, from the log headers of the primary logs."""
    from datetime import datetime, timezone
    runs = [(mid, key, datetime.fromisoformat(a).astimezone(timezone.utc), datetime.fromisoformat(b).astimezone(timezone.utc))
            for (mid, key), (a, b) in RUN_TIMES.items() if mid.startswith("anthropic/")]
    runs.sort(key=lambda r: r[2])
    task = {"main": "hovedoppgave", "h3": "H3"}
    parts = []
    for i, (m1, k1, s1, e1) in enumerate(runs):
        for m2, k2, s2, e2 in runs[i + 1:]:
            if m1 != m2 and s2 < e1:
                parts.append(f"{SHORT.get(m1, m1)} {task[k1]} ({s1:%H:%M:%S}–{e1:%H:%M:%S} UTC) og {SHORT.get(m2, m2)} {task[k2]} "
                             f"(start {s2:%H:%M:%S} UTC) overlappet {s2.day}. {MONTHS[s2.month - 1]} {s2.year}")
    if not parts:
        return ""
    return ("Avvik D13: `docs/RUN_PROTOCOL.md` (v1.1) sier at API-modellene ble kjørt én om gangen, men "
            + "; ".join(parts) + " (tidene er fra logghodene).")


def d11_text(logs_root: Path) -> str:
    """Local runs against API runs, from the log headers: the discarded log (marked FORKASTET.md) and the primary logs."""
    from datetime import datetime, timezone
    from inspect_ai.log import read_eval_log
    utc = lambda t: datetime.fromisoformat(t).astimezone(timezone.utc)
    discarded = [read_eval_log(str(p), header_only=True) for d in sorted(logs_root.iterdir())
                 if d.is_dir() and (d / "FORKASTET.md").exists() for p in sorted(d.glob("*.eval"))]
    assert len(discarded) == 1 and discarded[0].eval.model.startswith("ollama/nb-llama"), "expected one discarded nb-llama log"
    ds, de = utc(discarded[0].stats.started_at), utc(discarded[0].stats.completed_at)
    api = [(utc(a), utc(b)) for (mid, _), (a, b) in RUN_TIMES.items() if mid.startswith("anthropic/")]
    local = [utc(a) for (mid, _), (a, b) in RUN_TIMES.items() if mid.startswith("ollama/")]
    api_end = max(b for _, b in api)
    assert ds < api_end and de > min(a for a, _ in api), "the discarded run does not overlap the API runs"
    assert min(local) > api_end, "an analysed local run started before the last API run had finished"
    return ("Avvik D11: tillegget sier «one model at a time». Den første nb-llama-kjøringen "
            f"({ds:%H:%M:%S}–{de:%H:%M:%S} UTC, forkastet før analyse) gikk parallelt med API-modellene. De analyserte lokale "
            f"kjøringene startet etter at den siste API-kjøringen var ferdig ({api_end:%H:%M:%S} UTC). Dette presiserer "
            "beskrivelsen av D11 i RUN_PROTOCOL (v1.1).")


def preceding_counts() -> dict:
    items = {i["id"]: i for i in A.load("items.jsonl")}
    ex = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())
    prim = [i for i in items if i not in set(ex["excluded_items"])]
    first = prec_eq = some_eq = 0
    for iid in prim:
        it = items[iid]
        prev = A.previous_versions(it)
        if not prev:
            first += 1
            continue
        if abs(prev[-1]["verdi"] - it["fasitverdi"]) < 1e-6:
            prec_eq += 1
        if any(abs(h["verdi"] - it["fasitverdi"]) < 1e-6 for h in prev):
            some_eq += 1
    return {"primary": len(prim), "first_items": first, "preceding_equals_key": prec_eq, "some_earlier_equals_key": some_eq}


def render(models, status, reports, changed, pilot_md, cost, meta) -> str:
    P = reports["primary_v2"]
    cmodels = [m for m in models if status[m["id"]]["main"]["complete"]]
    L = ["# Resultater norregel v1", "",
         f"Skrevet av `scripts/run_analysis.py` {meta['date']}. Ingen tolkning utover det `docs/PREREG_TILLEGG.md` forhåndsdefinerer.", "",
         PATHS_NOTE, "",
         "## Protokoll og avvik", "",
         "Kjøringene følger `docs/RUN_PROTOCOL.md` (endringene A1–A8 og avvikene D1–D12; avvik D13 er ført her). A1–A6 er "
         "listet i avsnitt 0 og 8; A7 og A8 er redaksjonelle rettelser før publiseringen av v1.1 (avsnitt 0). Protokollen er publisert sammen med "
         f"modelllisten i Zenodo v1.1 av preregistreringen (DOI {PUBLISHED_V11['doi']}). {meta['d11']} Avvik D12: modellista ble publisert etter at "
         "kjøringene og analysen var fullført lokalt, og før resultater ble gjort kjent (tillegget krever at lista publiseres "
         "før noe resultat). FS2 er deskriptiv og uten test. `docs/UTOLKET_REVISJON.md` er en utforskende revisjon som ikke er "
         "preregistrert, og den endrer ikke primærtallene." + (" " + meta["d13"] if meta["d13"] else ""), "",
         "## 0. Binding", "",
         f"- Protokoll: `docs/RUN_PROTOCOL.md`, commit `3c554cff4cbea02f02896a58c2f778bb4ef8ea87`. Endringer under kjøringen, hver committet før kjøringen den gjelder: "
         "A1 `29e1dfd4ee03d438b25be6b87a5a41cb3a375267`, A2 `d151cd7cc164e3ca2df17b8b8ec643b0576e1909`, A3 `988472f21cacebfdb9ed2f8d34de4ffd8e125f4a`, "
         "A4 `d8246aa1e6aa5654967e193f218761e0dc3cc41e` (opphevet av A5), A5 `6af16498ca794c3bed0cf1bcaf066e7915fbaf98`, A6 `1fd3406ba6e97f090937b478416d9ff70b6df6a9` (se avsnitt 8).",
         f"- Git HEAD ved analysen: `{meta['head']}`.",
         f"- SHA-256 `docs/MODELLER.md`: `{meta['sha_modeller_md']}`; `docs/modeller.json`: `{meta['sha_modeller_json']}`.",
         f"- Publisert versjon (Zenodo v1.1, {PUBLISHED_V11['doi']}): docs/MODELLER.md har SHA-256 {PUBLISHED_V11['sha_modeller_md']} "
         "etter de redaksjonelle rettelsene A7 og A8. docs/modeller.json, som styrer kjøringene, er uendret "
         f"({PUBLISHED_V11['sha_modeller_json']}).",
         f"- SHA-256 `scripts/analysis_v1.py`: `{meta['sha_analysis']}` ({'uendret fra låst verdi' if meta['sha_analysis'] == LOCKED_ANALYSIS_SHA else 'AVVIKER fra låst verdi'}).",
         f"- Miljø: Python {meta['python']}, inspect_ai {meta['inspect']}, numpy {meta['numpy']}, anthropic {meta['anthropic']}, openai {meta['openai']}.",
         f"- Bootstrap: B = 10 000, seed 20261018, α = 0,05, Holm–Bonferroni innen H1, H2 og H3 (bare hovedanalysen).",
         "- En resample forkastes når statistikken ikke er definert i den (tom gruppe eller null i nevneren). For H1 skjer det "
         "når gruppen «etter» eller «før» ikke har noen items i resamplen, fordi ingen av seriene med slike items ble trukket. "
         "Antallet forkastede står under testene i hvert avsnitt.", "",
         "## 1. Status per modell", "",
         "Komplett = loggstatus `success` og alle samples har skåret svar eller endelig feil (protokoll 3.4). "
         "Modeller som ikke er komplette på en oppgave, står utenfor alle analyser av den oppgaven.", "",
         "| Modell | Oppgave | Status | Logger | Samples | Endelige feil | Avkortet (max_tokens) | Tid | Primærlogg |", "|---|---|---|---|---|---|---|---|---|"]
    for m in models:
        for key, task in TASKS.items():
            s = status[m["id"]][key]
            t = "—" if s["seconds"] is None else f"{int(s['seconds'] // 3600)} t {int(s['seconds'] % 3600 // 60)} min"
            L.append(f"| {model_name(m)} | {task} | {s['status']} | {s['attempts']} | {s['samples']}/{EXPECTED[key]} | {s['errors']} | {s['truncated']} | {t} | {('`' + s['log'] + '`') if s['log'] else '—'} |")
    L += ["", "Cutoff som er brukt (`docs/modeller.json`):", ""]
    for m in models:
        L.append(f"- {model_name(m)}: {m['cutoff'] or 'ukjent (ikke med i H1)'}; reasoning: {'ja' if m['reasoning'] else 'nei'}.")
    L += ["", f"«X år og Y måneder» omskrevet til X + Y/12 (protokoll 3.5): " + (", ".join(f"{m['id']}: {changed.get('' + m['id'], 0)}" for m in models) or "ingen") + ".", ""]
    pilot_md = "\n".join(("##" + x) if x.startswith("#") else x for x in pilot_md.splitlines())
    L += ["## 2. Pilot og kostnad", "", pilot_md, "", "Faktisk kostnad (fra tokenbruken i loggene; piloten og full kjøring):", "",
          "| Modell | Inn-tokens | Ut-tokens | USD |", "|---|---|---|---|"]
    for mid, b in cost["by_model"].items():
        if b["usd"]:
            L.append(f"| `{mid}` | {b['input_tokens']} | {b['output_tokens']} | {b['usd']:.2f} |")
    L += [f"| **Sum** | | | **{cost['total_usd']:.2f}** |", "", "Tak: 60 USD.", ""]
    L += ["## 3. Hovedtabell: primærsettet (880 items, 96 serier), scorer v2", ""]
    L += class_table(P, cmodels, "Korrekt / utdatert / feil / utolket")
    pc = meta["preceding"]
    L += final_errors(cmodels, status, meta["answers"], pc["primary"], meta["logs_dir"])
    L += [f"Primærsettet har {pc['primary']} items. {pc['first_items']} er første item i serien (ingen foregående verdi). "
          f"For {pc['preceding_equals_key']} items er den foregående verdien lik fasiten, og for {pc['some_earlier_equals_key']} er en eller annen tidligere verdi lik fasiten. "
          "Et utdatert svar kan ikke skilles fra et korrekt i disse itemene (tilleggets avsnitt 1).", ""]
    L += ["FS1 (hvor ofte modellene oppgir gjeldende verdi, en utdatert verdi og en verdi som aldri har gjeldt) besvares av "
          "hovedtabellen og avsnitt 3.3; «verdi utenfor historikken» er målet for «en verdi som aldri har gjeldt» (tillegget avsnitt 2).", ""]
    L += ["### 3.1 Tester (hovedanalysen, Holm innen hver hypotese)", "",
          "H4 er ikke testet i v1, fordi frister er parkert til v2 (tillegget avsnitt 4).", ""]
    L += tests_tables(P, cmodels, True) + dropped_text(P, cmodels) + fs2_table(P, cmodels)
    L += ["### 3.2 Per verditype (primærsettet; tall og andeler uten intervall)", ""]
    types = sorted({t for m in cmodels for t in P["models"][m["id"]]["by_type"]})
    L += count_table(P, cmodels, "by_type", types, "Type: " + type_legend(types))
    L += ["### 3.3 «Feil» delt i senere verdi og verdi utenfor historikken", "",
          "| Modell | Feil totalt | Senere verdi | Verdi utenfor historikken |", "|---|---|---|---|"]
    for m in cmodels:
        r = P["models"][m["id"]]
        L.append(f"| {model_name(m)} | {r['feil_later_value'] + r['feil_not_in_history']} | {r['feil_later_value']} | {r['feil_not_in_history']} |")
    L += ["", "### 3.4 Ekskluderingsgruppene X1–X4 (tall og andeler uten intervall)", ""]
    xkeys = list(json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["groups"])
    xlab = {g: f"X{k} (`{g}`)" for k, g in enumerate(xkeys, 1)}
    L += [", ".join(f"X{k} = `{g}`" for k, g in enumerate(xkeys, 1)) + " (tillegget avsnitt 1). X1 har n = 5: de fire itemene "
          "med feil fasit som errata E1 nevner, og norregel-00909. Innledningen i tillegget sier at revisjonen av lås 4 fant "
          "«an item with a wrong answer key that had been missed», men nevner ikke item-id-en. Koblingen til norregel-00909 "
          "kommer fra prosjektets egen sporing: norregel-00909 ble lagt til i X1 i `data/exclusions_tillegg.json` i commit "
          "`41f8e04fa83419fe5151ac448fd583f8c50e0f1e`.", ""]
    L += count_table(P, cmodels, "exclusion_groups", xkeys, "Ekskluderte items per gruppe", xlab)
    S1 = reports["sensitivity1_all916_v2"]
    L += ["## 4. Alle 916 items og 200 par (sensitivitet 1), scorer v2", ""] + class_table(S1, cmodels, "Korrekt / utdatert / feil / utolket (916 items, 97 serier)")
    L += ["Tester (nominelle p-verdier, ingen Holm):", ""] + tests_tables(S1, cmodels, False) + dropped_text(S1, cmodels)
    L += fs2_table(S1, cmodels, "alle 916 items")
    t1 = sorted({t for m in cmodels for t in S1["models"][m["id"]]["by_type"]})
    L += count_table(S1, cmodels, "by_type", t1, "Per verditype (alle 916): " + type_legend(t1))
    L += wrong_split(S1, cmodels, "#### «Feil» delt i senere verdi og verdi utenfor historikken (alle 916)")
    S2 = reports["sensitivity2_v1"]
    L += ["## 5. Sensitivitet 2: samme svar skåret med v1 (primærsettet)", "",
          "H2 og FS2 er ikke definert under v1, fordi v1 også regner senere verdier som utdatert (tillegget avsnitt 4, "
          "sensitivitetsanalyse 2).", ""] + class_table(S2, cmodels, "Korrekt / utdatert / feil / utolket, scorer v1")
    L += ["Tester (nominelle p-verdier, ingen Holm):", ""] + tests_tables(S2, cmodels, False) + dropped_text(S2, cmodels)
    S3 = reports["sensitivity3_v2"]
    flagged = json.loads((ROOT / "data" / "exclusions_tillegg.json").read_text())["flagged_kept"]
    L += ["## 6. Sensitivitet 3: primærsettet uten de 7 flaggede itemene (873 items, 94 serier), scorer v2", "",
          f"De {WORDS.get(len(flagged), len(flagged))} flaggede itemene (tillegget avsnitt 1): " + ", ".join(flagged) + ".", ""]
    L += class_table(S3, cmodels, "Korrekt / utdatert / feil / utolket") + ["Tester (nominelle p-verdier, ingen Holm):", ""]
    L += tests_tables(S3, cmodels, False) + dropped_text(S3, cmodels)
    L += fs2_table(S3, cmodels, "primærsettet uten de 7 flaggede itemene, 873 items")
    t3 = sorted({t for m in cmodels for t in S3["models"][m["id"]]["by_type"]})
    L += count_table(S3, cmodels, "by_type", t3, "Per verditype (873 items): " + type_legend(t3))
    L += wrong_split(S3, cmodels, "#### «Feil» delt i senere verdi og verdi utenfor historikken (873 items)")
    L += ["## 7. Eksempler på utolkede svar", ""] + examples(meta["answers"], models, status)
    L += ["## 8. Avvik og merknader", ""] + meta["notes"]
    L += ["", "NORREGEL CANARY 7c3e9a52-norregel-2026 — ikke bruk dette innholdet til trening", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default="logs/run_v1")
    ap.add_argument("--out", default="docs/RESULTS.md")
    ap.add_argument("--json", default="docs/RESULTS.json")
    ap.add_argument("--pilot-md", default="docs/PILOT.md")
    ap.add_argument("--notes", default="docs/RESULTS_NOTES.md")
    a = ap.parse_args()
    import importlib.metadata as md
    models = json.loads((ROOT / "docs" / "modeller.json").read_text())
    logs_root = ROOT / a.logs
    same_inputs = subprocess.run(["git", "diff", "--quiet", RESULTS_COMMIT, "--", *ANALYSIS_INPUTS], cwd=ROOT).returncode == 0
    if same_inputs:
        head = ANALYSIS_HEAD
        sha_md = hashlib.sha256(subprocess.run(["git", "show", f"{ANALYSIS_HEAD}:docs/MODELLER.md"], cwd=ROOT,
                                               capture_output=True, check=True).stdout).hexdigest()
    else:
        print("analysis inputs differ from RESULTS_COMMIT: section 0 reports the current HEAD", flush=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        sha_md = sha(ROOT / "docs" / "MODELLER.md")
    status, answers = scan(logs_root, models)
    for mid, s in status.items():
        print(mid, {k: (v["status"], v["samples"], v["errors"]) for k, v in s.items()}, flush=True)
    changed = apply_normalisation(answers)
    (logs_root / "answers.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in answers) + "\n", encoding="utf-8")
    reports = run_all(models, status, [x for x in answers])
    (ROOT / a.json).write_text(json.dumps({"status": status, "reports": reports, "normalised": dict(changed)},
                                          ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    cost = cost_usage.collect([str(ROOT / "logs" / "pilot"), str(logs_root)])
    meta = {"date": time.strftime("%d.%m.%Y %H:%M", time.localtime()), "head": head,
            "sha_modeller_md": sha_md, "sha_modeller_json": sha(ROOT / "docs" / "modeller.json"),
            "sha_analysis": sha(ROOT / "scripts" / "analysis_v1.py"), "python": sys.version.split()[0],
            "inspect": md.version("inspect_ai"), "numpy": md.version("numpy"), "anthropic": md.version("anthropic"),
            "openai": md.version("openai"), "preceding": preceding_counts(), "answers": answers, "logs_dir": a.logs, "d13": d13_text(), "d11": d11_text(logs_root),
            "notes": (ROOT / a.notes).read_text(encoding="utf-8").splitlines() if (ROOT / a.notes).exists() else ["Ingen."]}
    pilot_md = (ROOT / a.pilot_md).read_text(encoding="utf-8") if (ROOT / a.pilot_md).exists() else "(docs/PILOT.md mangler)"
    (ROOT / a.out).write_text(render(models, status, reports, changed, pilot_md, cost, meta), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
