"""norregel × Borealis: frosset analyse av den parvise designen (prereg §7). Leser itemene fra manifestet.

Bruk (F5, etter F4):
  PYTHONDONTWRITEBYTECODE=1 ~/dev/norregel/.venv/bin/python -B F4/analyse/analyse_parvis.py \
      --norregel ~/dev/norregel --manifest F4/manifest_v1.json \
      --a F4/kjeder/full-borealis2.jsonl --b F4/kjeder/full-gemma4.jsonl \
      [--b1 <kjede borealis-4b> --b2 <kjede borealis-open-4b>] --ut F5/resultat_v1.json

Klassene kommer fra norregels låste scorer v2 via scripts/analysis_v2.classify, uendret. sha256 for de importerte filene
kontrolleres mot LÅST før noe regnes ut.

Primærmål (H-a, bekreftende): andel utdaterte svar, med tolkbare svar som nevner (som H1 i v2, PREREG_V2.md:235), parvis på
manifestets primær-items der begge modellenes svar er tolkbare. Test: eksakt McNemar (binomialtest på de diskordante
parene), ensidig i hypotesens retning (A = Borealis 2 > B = Gemma 4), α = 0,05. Effekt: d = (b10 − b01) / n, med 95 %
klyngebootstrap-intervall over serier (B = 10 000, seed 20261117, som i v2).
Tolkning (satt på forhånd): «støttet» når p < 0,05 og nedre intervallgrense > 0; «ingen effekt av interesse» når hele
intervallet ligger innenfor ±10 pp (minste effekt av interesse, SESOI, lik MEI_H1 i v2: analysis_v2.py:39, PREREG_V2.md:283);
ellers «inkonklusiv».
Sekundære mål (Holm over de sekundære målene som kan testes, det vil si har minst ett diskordant par; S-5 bare når
(b)-kjedene er gitt. Tosidig eksakt McNemar, α = 0,05): S-1 utdatert med alle svar som nevner; S-2 «senere
verdi»; S-3 korrekt; S-4 utolket; S-5 (b) primærmålet for borealis-4b mot borealis-open-4b (utforskende); S-6 utdatert lik
den nyeste avvikende verdien. «Utolket» er et eget utfall og rapporteres per underklasse.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from math import comb
from pathlib import Path

LÅST = {  # sha256 for norregels filer som analysen importerer (v2-låsen, docs/LOCK_V2.md)
    "scripts/analysis_v2.py": None,
    "src/norregel/score_v2.py": None,
    "scripts/norm_aar_maaneder.py": None,
}
B, SEED, ALFA, SESOI = 10_000, 20261117, 0.05, 0.10  # SESOI = MEI_H1 i v2


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def last_norregel(rot: Path, låst: dict):
    for rel, h in låst.items():
        if h is not None and sha(rot / rel) != h:
            raise SystemExit(f"{rel} avviker fra låst sha256")
    sys.path.insert(0, str(rot / "src"))
    sys.path.insert(0, str(rot / "scripts"))
    import analysis_v2 as A  # noqa: E402
    return A


def mcnemar_eksakt(b10: int, b01: int, retning: str = "tosidig") -> float | None:
    n = b10 + b01
    if n == 0:
        return None
    cdf = lambda k: sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n  # noqa: E731
    if retning == "større":  # H: b10 > b01
        return 1 - cdf(b10 - 1)
    return min(1.0, 2 * min(cdf(b10), 1 - cdf(b10 - 1)))


def holm(p: dict[str, float | None]) -> dict[str, bool | None]:
    test = sorted((v, k) for k, v in p.items() if v is not None)
    m, ut, stopp = len(test), {k: None for k in p}, False
    for r, (v, k) in enumerate(test):
        forkast = (not stopp) and v <= ALFA / (m - r)
        stopp = stopp or not forkast
        ut[k] = forkast
    return ut


def bootstrap_d(par: list[tuple[str, int]], b: int = B, seed: int = SEED) -> tuple[float | None, float | None]:
    """par = [(serie, diff)] med diff ∈ {−1, 0, 1}; klyngebootstrap over serier."""
    import numpy as np
    if not par:
        return None, None
    serier = sorted({s for s, _ in par})
    per = {s: [d for t, d in par if t == s] for s in serier}
    rng = np.random.default_rng(seed)
    ds = []
    for _ in range(b):
        valg = rng.integers(0, len(serier), len(serier))
        xs = [x for j in valg for x in per[serier[j]]]
        ds.append(sum(xs) / len(xs))
    return float(np.quantile(ds, 0.025)), float(np.quantile(ds, 0.975))


def klasser(A, kjede: list[dict], items: dict, rejected: dict) -> dict[str, dict]:
    ut = {}
    for p in kjede:
        if p.get("modus") != "full":
            continue
        ut[p["id"]] = A.classify({"completion": p["fullføring"], "error": bool(p.get("feil"))}, items[p["id"]], rejected)
    return ut


def utdatert_nyeste(A, c: dict, item: dict) -> bool:
    if c["klasse"] != "utdatert":
        return False
    pv = A.immediately_preceding_value(item)
    return pv is not None and c["lest"] is not None and abs(c["lest"] - pv) < A.S2.TOL


def parvis(ids, ka, kb, items, utfall, krev_tolkbar: bool) -> dict:
    b10 = b01 = n = 0
    par = []
    for i in ids:
        a, b = ka.get(i), kb.get(i)
        if a is None or b is None:
            continue
        if krev_tolkbar and (a["klasse"] == "utolket" or b["klasse"] == "utolket"):
            continue
        ya, yb = utfall(a, items[i]), utfall(b, items[i])
        n += 1
        b10 += ya and not yb
        b01 += yb and not ya
        par.append((items[i]["serie_id"], int(ya) - int(yb)))
    return {"n": n, "b10": b10, "b01": b01, "d": (b10 - b01) / n if n else None, "par": par}


def analyser(A, manifest: dict, items: dict, kjeder: dict[str, list[dict]], rejected: dict, b: int = B) -> dict:
    prim = manifest["primær_a_b"]
    k = {m: klasser(A, kj, items, rejected) for m, kj in kjeder.items()}
    for m in ("a", "b"):
        mangler = [i for i in prim if i not in k[m]]
        if mangler:
            raise SystemExit(f"modell {m} mangler {len(mangler)} primær-items, f.eks. {mangler[:3]}")
    utd = lambda c, it: c["klasse"] == "utdatert"  # noqa: E731
    r = {}
    h = parvis(prim, k["a"], k["b"], items, utd, krev_tolkbar=True)
    lo, hi = bootstrap_d(h["par"], b)
    p = mcnemar_eksakt(h["b10"], h["b01"], "større")
    if p is not None and p < ALFA and lo is not None and lo > 0:
        tilstand = "støttet"
    elif lo is not None and lo > -SESOI and hi < SESOI:
        tilstand = "ingen effekt av interesse"
    else:
        tilstand = "inkonklusiv"
    r["primær_H_a"] = {**{x: h[x] for x in ("n", "b10", "b01", "d")}, "ki95": [lo, hi], "p_ensidig": p, "tilstand": tilstand,
                       "test": "eksakt McNemar, ensidig (Borealis 2 > Gemma 4)"}
    sek = {
        "S-1_utdatert_alle_svar": parvis(prim, k["a"], k["b"], items, utd, krev_tolkbar=False),
        "S-2_senere_verdi": parvis(prim, k["a"], k["b"], items, lambda c, it: c["under"] == "senere_verdi", False),
        "S-3_korrekt": parvis(prim, k["a"], k["b"], items, lambda c, it: c["klasse"] == "korrekt", False),
        "S-4_utolket": parvis(prim, k["a"], k["b"], items, lambda c, it: c["klasse"] == "utolket", False),
        "S-6_utdatert_nyeste": parvis(prim, k["a"], k["b"], items, lambda c, it: utdatert_nyeste(A, c, it), True),
    }
    if "b1" in k and "b2" in k:
        sek["S-5_b_utdatert"] = parvis(prim, k["b1"], k["b2"], items, utd, krev_tolkbar=True)
    ps = {n_: mcnemar_eksakt(v["b10"], v["b01"]) for n_, v in sek.items()}
    hf = holm(ps)
    r["sekundære"] = {n_: {**{x: v[x] for x in ("n", "b10", "b01", "d")}, "p_tosidig": ps[n_], "holm_forkastet": hf[n_]}
                      for n_, v in sek.items()}
    r["sekundær_korreksjon"] = "Holm (1979) over de sekundære målene som kunne testes, α = 0,05"
    r["beskrivende"] = {m: {"klasser": dict(Counter(c["klasse"] for i, c in km.items() if i in set(prim))),
                            "utolket_under": dict(Counter(c["under"] for i, c in km.items() if i in set(prim) and c["klasse"] == "utolket"))}
                        for m, km in k.items()}
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    for a in ("--norregel", "--manifest", "--a", "--b", "--ut"):
        ap.add_argument(a, required=True)
    ap.add_argument("--b1")
    ap.add_argument("--b2")
    x = ap.parse_args()
    rot = Path(x.norregel).expanduser().resolve()
    låst = json.loads((Path(__file__).parent / "LAAST_SHA256.json").read_text())
    A = last_norregel(rot, låst)
    manifest = json.loads(Path(x.manifest).read_text(encoding="utf-8"))
    if sha(rot / "data" / "items.jsonl") != manifest["kilde"]["items.jsonl"]:
        raise SystemExit("items.jsonl avviker fra manifestet")
    items = {d["id"]: d for d in (json.loads(l) for l in (rot / "data" / "items.jsonl").open(encoding="utf-8"))}
    rejected = A.rejected_values({items[i]["serie_id"] for i in items})
    les = lambda p: [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]  # noqa: E731
    kjeder = {"a": les(x.a), "b": les(x.b)}
    if x.b1 and x.b2:
        kjeder.update({"b1": les(x.b1), "b2": les(x.b2)})
    r = analyser(A, manifest, items, kjeder, rejected)
    Path(x.ut).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(r["primær_H_a"], ensure_ascii=False))


if __name__ == "__main__":
    main()
