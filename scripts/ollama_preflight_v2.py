"""Pre-flight for the local models of norregel v2: the same checks as v1 amendments A2 and A3 (docs/RUN_PROTOCOL.md,
section 7), before any sample is run. No sample is scored; the checks only render the prompt (and, for nb-llama,
generate one token of «Hei» to read the token ids).

- NorMistral (A2): the rendered prompt equals the card format «<|im_start|> user\\n{q}<|im_end|>\\n<|im_start|> assistant\\n».
- nb-llama (A3): the rendered prompt equals the pinned card format with the default date 26 Jul 2024, and the token ids
  start with <|begin_of_text|> once.

  .venv/bin/python -I scripts/ollama_preflight_v2.py <inspect model id> <host, e.g. http://127.0.0.1:11435>

Exit code 0 when the check passes, 3 otherwise.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def post(host: str, path: str, obj: dict) -> dict:
    req = urllib.request.Request(host + path, data=json.dumps(obj).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=900))


def main() -> int:
    model_id, host = sys.argv[1], sys.argv[2].rstrip("/")
    m = model_id.split("/", 1)[1]
    q = json.loads((ROOT / "data" / "items.jsonl").open(encoding="utf-8").readline())["spørsmål"]
    r = post(host, "/api/chat", {"model": m, "messages": [{"role": "user", "content": q}], "stream": False,
                                 "_debug_render_only": True})["_debug_info"]["rendered_template"]
    if m.startswith("normistral-"):
        exp = f"<|im_start|> user\n{q}<|im_end|>\n<|im_start|> assistant\n"
        ok = r == exp
        ids = None
    elif m.startswith("nb-llama-"):
        exp = ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nCutting Knowledge Date: December 2023\n"
               "Today Date: 26 Jul 2024\n\n<|eot_id|>"
               f"<|start_header_id|>user<|end_header_id|>\n\n{q}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n")
        ids = post(host, "/api/generate", {"model": m, "prompt": "Hei", "stream": False,
                                            "options": {"num_predict": 1, "temperature": 0}})["context"][:4]
        ok = r == exp and ids[:3] == [128000, 128006, 9125]  # <|begin_of_text|> once, <|start_header_id|>, «system»
    else:
        print(f"no pre-flight defined for {model_id}", file=sys.stderr)
        return 3
    print(("pre-flight OK" if ok else "PRE-FLIGHT FAILED") + f": {model_id}; rendered prompt {'equals' if r == exp else 'differs from'} "
          f"the card format" + (f"; token ids start {ids}" if ids is not None else ""))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
