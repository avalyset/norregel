"""norregel × Borealis, F4: kjøring på Modal (én modell per container), med utdata som hashkjede.

Mønster: Modals eget vLLM-eksempel for Gemma 4 (KILDER/modal-docs-vllm-gemma4.md): CUDA-image fra registry, vllm==0.21.0,
HF_XET_HIGH_PERFORMANCE=1, revisjonen pinnet, multimodal inndata slått av. Avvik fra eksemplet: offline `vllm.LLM` i stedet
for `vllm serve`, A100-80GB i stedet for H200, enforce_eager=True (eksemplets FAST_BOOT) fordi hver bit kaldstartes uten
cache-volum, og ingen Volume (VERN).

Moduser (local_entrypoint):
  smoke : «Skriv én setning om været.» to ganger, hver for seg; svarene sammenlignes byte for byte.
  full  : spørsmålene fra en låst spørsmålsfil, i biter. SPERRET til forhåndsregistreringen er publisert:
          krever --registrert-doi med en Zenodo-DOI, og --sporsmal med sha256 lik manifestet.

Kjøres med:  ~/.venvs/modal/bin/modal run F4/f4_modal.py --modell borealis2 --modus smoke --ut F4/kjeder/smoke-borealis2.jsonl
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import modal

MODELLER = {  # ADR-0005 (vedtatt 2026-11-01), GT411–GT412
    "borealis2": ("NbAiLab/borealis2-26b-a4b-preview", "6f14c8f8913a9d751b80eee1c4a72d2ca4bfaa98"),
    "gemma4": ("google/gemma-4-26B-A4B-it", "4d7ae4984b7db7de8f8457170b3f1a419ee76d52"),
}
VLLM_VERSJON = "0.21.0"         # Modal-eksemplet (GT418)
TRANSFORMERS_VERSJON = "5.8.1"
GPU = "A100-80GB"               # Modals GPU-navn (KILDER/modal-docs-gpu.md; original r4-modal-docs-gpu.html)
TIMEOUT_S = 1200                # VERN
# Eiriks ordre var 100 GiB. Modal avviste det 2026-11-01T11:39Z: «Function disk request out of bounds: 102400 MiB. Must be
# between 524288 and 3145728 MiB.» (AVVIK A-20). Satt til tjenestens minimum, 512 GiB, som også er standardkvoten (GT417).
EPHEMERAL_DISK_MIB = 524288
# Dekoding som i v2: temperatur 0 (run_v2.sh:99; v2_modeller.json:101). Maks tokens: v2s regel for lokalt kjørte modeller,
# 1024 (run_v2.sh:20; PREREG_V2.md:151). API-regelen på 16 384 (v2_modeller.json:103) gjaldt med tenking på hos leverandøren.
# Her er tenking av, og et svar på 16 384 tokens ville tatt ca. 975 s for Gemma 4 (16,8 tokens/s i røyktesten), mer enn
# timeouten minus overhead. Lengste Gemma 4 26B-svar i v2 var 741 tegn (F4/F4_ANSLAG.md). v2 hadde ingen generasjonsseed; SEED er satt for vLLM, men virker ikke ved
# temperatur 0 (grådig dekoding). Ett spørsmål per samtale, bare brukermelding, ingen systemprompt (inspect_task.py:29–30, :73).
TEMPERATUR = 0.0
MAKS_TOKENS = 1024
SEED = 20261117
MAKS_KONTEKST = 4096
RØYKPROMPT = "Skriv én setning om været."
# Bitstørrelse og tidsvakt (F4/F4_ANSLAG.md, regnet fra røyktesten 2026-11-01, den tregeste modellen Gemma 4):
# overhead per container 334,7 s (veggtid), dekoding 16,8 tokens/s etter oppvarming, og ett svar på maks 1024 tokens
# tar da ca. 61 s. BIT = floor((1200 − 1,5 × 334,7 − 61) / 8,1) = 78, der 8,1 s er tiden for et svar på p99-lengde
# (378 tegn ≈ 130 tokens; v2, Gemma 4 26B) pluss 0,4 s.
# Tidsvakten starter ikke et nytt spørsmål når tiden i containeren pluss RESERVE_S overstiger TIMEOUT_S − 60. Biten
# returnerer da det som er gjort, og neste bit fortsetter fra siste post i hashkjeden.
BIT = 78
RESERVE_S = 120

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    # transformers pinnet: uten pin valgte uv 4.57.6, som ikke kjenner gemma4 (røyktest 2026-11-01T11:43Z, AVVIK A-21).
    # 5.8.1 er versjonen i Borealis-kortets generation_config.json og er tillatt av vllm 0.21.0 (PyPI requires_dist).
    .uv_pip_install(f"vllm=={VLLM_VERSJON}", f"transformers=={TRANSFORMERS_VERSJON}")
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)
app = modal.App("norregel-f4", image=image)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def kanonisk(d: dict) -> bytes:
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@app.function(gpu=GPU, timeout=TIMEOUT_S, ephemeral_disk=EPHEMERAL_DISK_MIB, secrets=[modal.Secret.from_name("hf-norregel")])
def kjør(modell: str, sporsmal: list[dict]) -> dict:
    """Én modell per container. sporsmal = [{"id": ..., "prompt": ...}]. Hvert spørsmål kjøres for seg (egen generate)."""
    import os
    import subprocess

    from huggingface_hub import snapshot_download

    repo, rev = MODELLER[modell]
    t_start = time.time()
    t0 = time.time()
    sti = snapshot_download(repo, revision=rev, local_dir="/tmp/modell", token=os.environ["HF_TOKEN"],
                            allow_patterns=["*.safetensors", "*.json", "*.jinja", "tokenizer*"])
    t_ned = time.time() - t0
    bytes_ned = sum(p.stat().st_size for p in Path(sti).rglob("*") if p.is_file())

    from vllm import LLM, SamplingParams
    t1 = time.time()
    llm = LLM(model=sti, dtype="bfloat16", max_model_len=MAKS_KONTEKST, enforce_eager=True,
              gpu_memory_utilization=0.92, limit_mm_per_prompt={"image": 0, "video": 0, "audio": 0}, seed=SEED)
    t_last = time.time() - t1
    tok = llm.get_tokenizer()

    # Lærdom 11: chat-malen verifisert på token-id-nivå mot formatet i modellkortet (README «Thinking Mode Configuration»:
    # thinking av = ingen <|think|>, tom tankeblokk <|channel>thought\n<channel|>) og malen (chat_template.jinja:186, :383–386).
    def ids_mal(tekst: str) -> list[int]:
        r = tok.apply_chat_template([{"role": "user", "content": tekst}], add_generation_prompt=True, tokenize=True,
                                    enable_thinking=False)
        r = r["input_ids"] if hasattr(r, "keys") else r  # transformers 5 kan returnere en dict
        return list(r[0]) if r and isinstance(r[0], list) else list(r)

    def ids_kort(tekst: str) -> list[int]:
        s = f"{tok.bos_token}<|turn>user\n{tekst}<turn|>\n<|turn>model\n<|channel>thought\n<channel|>"
        return tok.encode(s, add_special_tokens=False)

    malsjekk = {"lik": ids_mal(RØYKPROMPT) == ids_kort(RØYKPROMPT), "ids_mal": ids_mal(RØYKPROMPT),
                "think_token_id": tok.convert_tokens_to_ids("<|think|>")}
    malsjekk["think_i_prompt"] = malsjekk["think_token_id"] in malsjekk["ids_mal"]
    if not malsjekk["lik"] or malsjekk["think_i_prompt"]:
        return {"feil": "chat-malsjekk feilet", "malsjekk": malsjekk}

    sp = SamplingParams(temperature=TEMPERATUR, max_tokens=MAKS_TOKENS, seed=SEED, skip_special_tokens=False)
    poster, ut_tok, t_gen, tidsvakt = [], 0, 0.0, False
    for s in sporsmal:
        if time.time() - t_start + RESERVE_S > TIMEOUT_S - 60:
            tidsvakt = True
            break
        ids = ids_mal(s["prompt"])
        tg = time.time()
        o = llm.generate([{"prompt_token_ids": ids}], sp, use_tqdm=False)[0].outputs[0]
        dt = time.time() - tg
        t_gen += dt
        ut_tok += len(o.token_ids)
        rå = o.text
        svar = rå.split("<channel|>", 1)[1] if "<channel|>" in rå else rå  # tom tankeblokk fjernes før skåring
        svar = svar.replace("<turn|>", "").strip()
        poster.append({"id": s["id"], "prompt_sha256": _sha(s["prompt"].encode()), "prompt_ids_sha256": _sha(json.dumps(ids).encode()),
                       "fullføring_rå": rå, "fullføring": svar, "ut_tokens": len(o.token_ids), "stopp": o.finish_reason,
                       "sekunder": round(dt, 3)})
    smi = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    import vllm
    from huggingface_hub import HfApi
    faktisk_rev = HfApi().model_info(repo, revision=rev, token=os.environ["HF_TOKEN"]).sha  # FEILREGLER 5: revisjonen kontrolleres
    if faktisk_rev != rev or vllm.__version__ != VLLM_VERSJON:
        return {"feil": "revisjon eller vLLM-versjon avviker", "faktisk_rev": faktisk_rev, "vllm": vllm.__version__}
    return {"modell": modell, "repo": repo, "revisjon": rev, "vllm": vllm.__version__, "gpu": smi,
            "nedlasting_s": round(t_ned, 1), "nedlastet_bytes": bytes_ned, "lasting_s": round(t_last, 1),
            "generering_s": round(t_gen, 2), "ut_tokens": ut_tok, "tokens_per_s": round(ut_tok / t_gen, 2) if t_gen else None,
            "malsjekk": malsjekk, "tidsvakt_stoppet": tidsvakt, "poster": poster}


def les_kjede(sti: Path) -> list[dict]:
    if not sti.exists():
        return []
    poster = [json.loads(l) for l in sti.read_text(encoding="utf-8").splitlines() if l.strip()]
    forrige = "0" * 64
    for p in poster:  # kjeden kontrolleres før den forlenges
        h = p.pop("hash")
        assert p["forrige_hash"] == forrige and _sha(kanonisk(p)) == h, f"brudd i hashkjeden ved {p.get('id')}"
        p["hash"] = h
        forrige = h
    return poster


def skriv_kjede(sti: Path, nye: list[dict], meta: dict) -> list[dict]:
    """Atomisk: hele kjeden skrives til en midlertidig fil, synkroniseres til disk og byttes inn med os.replace. Dør
    prosessen underveis, står den gamle kjeden urørt (KONTROLL-F4 4.5)."""
    import os
    poster = les_kjede(sti)
    forrige = poster[-1]["hash"] if poster else "0" * 64
    sti.parent.mkdir(parents=True, exist_ok=True)
    for n in nye:
        p = {**n, **meta, "forrige_hash": forrige, "skrevet_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        p["hash"] = _sha(kanonisk(p))
        forrige = p["hash"]
        poster.append(p)
    tmp = sti.with_name(sti.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for p in poster:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, sti)
    les_kjede(sti)  # kontroll etter skriving
    return poster


@app.local_entrypoint()
def main(modell: str, modus: str = "smoke", ut: str = "", sporsmal: str = "", sporsmal_sha256: str = "",
         bit: int = 0, registrert_doi: str = ""):
    assert modell in MODELLER, modell
    utsti = Path(ut or f"F4/kjeder/{modus}-{modell}.jsonl")
    if modus == "smoke":
        prøver = [{"id": "smoke-1", "prompt": RØYKPROMPT}, {"id": "smoke-2", "prompt": RØYKPROMPT}]
    elif modus == "full":
        # SPERRE: ingen norregel-spørsmål før registreringen er publisert (NRG-MAP-0001, regel 1).
        assert registrert_doi.startswith("10.5281/zenodo."), "full kjøring krever publisert registrering (--registrert-doi)"
        # Spørsmålsfila er norregels låste data/items.jsonl (sha256 i manifestet, «kilde» → «items.jsonl»; LOCK_V2.md:50).
        # Alle 916 items kjøres i filas rekkefølge; primæranalysen bruker manifestets utvalg (analyse_parvis.py).
        raw = Path(sporsmal).expanduser().read_bytes()
        assert _sha(raw) == sporsmal_sha256, "spørsmålsfila stemmer ikke med manifestet"
        alle = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
        assert len(alle) == 916, len(alle)
        gjort = {p["id"] for p in les_kjede(utsti) if p.get("modus") == "full"}
        rest = [a for a in alle if a["id"] not in gjort]  # fortsetter etter siste post i hashkjeden
        prøver = [{"id": a["id"], "prompt": a["spørsmål"]} for a in rest[:(bit or BIT)]]
        if not prøver:
            print("ingenting igjen")
            return
    else:
        raise SystemExit(f"ukjent modus {modus}")
    start = time.time()
    r = kjør.remote(modell, prøver)
    vegg = round(time.time() - start, 1)
    if "feil" in r:
        print(json.dumps(r, ensure_ascii=False)[:2000])
        raise SystemExit(1)
    meta = {"modus": modus, "modell": modell, "repo": r["repo"], "revisjon": r["revisjon"], "vllm": r["vllm"]}
    skriv_kjede(utsti, r.pop("poster"), meta)
    r["veggtid_s"] = vegg
    sammendrag = utsti.with_suffix(".sammendrag.json")
    sammendrag.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    if modus == "smoke":
        p = [x for x in les_kjede(utsti) if x["modus"] == "smoke"][-2:]
        print("svar like byte for byte:", p[0]["fullføring_rå"].encode() == p[1]["fullføring_rå"].encode())
    print(json.dumps({k: v for k, v in r.items() if k != "malsjekk"}, ensure_ascii=False))
    print("malsjekk lik:", r["malsjekk"]["lik"], "think i prompt:", r["malsjekk"]["think_i_prompt"])
