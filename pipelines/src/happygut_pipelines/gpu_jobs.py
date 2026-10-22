"""Finite GPU jobs, run by hand on the team's Ubuntu machine (AMD RX 7700 XT).

Each job reads its inputs from the repo, writes its outputs to data/gpu_jobs/<job>/ and records
provenance (model, digest, prompt version, parameters, git commit, timings) in meta.json. Jobs are
resumable: rerunning skips items already in the output. No secrets are needed.

    uv run python -m happygut_pipelines.gpu_jobs check          # Ollama + GPU + models ready?
    uv run python -m happygut_pipelines.gpu_jobs g2              # Bangla/Banglish dish-name variants (Gemma)
    uv run python -m happygut_pipelines.gpu_jobs g3              # BGE-M3 embeddings (ROCm PyTorch)
    uv run python -m happygut_pipelines.gpu_jobs g1              # guideline chunk context headers (Qwen3)

Then commit data/gpu_jobs/ and push; Windows loads the outputs into Supabase / Neo4j.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import subprocess
import sys
import time
import unicodedata
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from .seeds import DEFAULT_SEEDS, _read

REPO = DEFAULT_SEEDS.parents[1]
JOBS_DIR = REPO / "data" / "gpu_jobs"
PROMPTS_DIR = REPO / "prompts" / "runtime"
OLLAMA_URL = "http://127.0.0.1:11434"

MODELS = {
    "g1": "qwen3:14b",
    "g2": "gemma3:12b",
    "g3": "BAAI/bge-m3",
}


# ---------------------------------------------------------------- prompts

@dataclass(frozen=True)
class Prompt:
    id: str
    version: int
    model: str
    temperature: float
    body: str
    params: dict = field(default_factory=dict)  # other front-matter keys, as strings

    def render(self, **values) -> str:
        text = self.body
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        return text


def load_prompt(prompt_id: str, version: int | None = None) -> Prompt:
    folder = PROMPTS_DIR / prompt_id
    versions = sorted(int(p.stem[1:]) for p in folder.glob("v*.md"))
    v = version or versions[-1]
    raw = (folder / f"v{v}.md").read_text(encoding="utf-8")
    _, front, body = raw.split("---", 2)
    meta = {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in front.strip().splitlines() if ":" in line)}
    return Prompt(
        id=meta.pop("id"), version=int(meta.pop("version")), model=meta.pop("model"),
        temperature=float(meta.pop("temperature")), body=body.strip(), params=meta,
    )


# ---------------------------------------------------------------- Ollama client (stdlib only)

class Ollama:
    def __init__(self, url: str = OLLAMA_URL, timeout: float = 600):
        self.url, self.timeout = url.rstrip("/"), timeout

    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            self.url + path, data=json.dumps(payload).encode(), headers={"content-type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def chat_json(self, model: str, prompt: str, schema: dict, temperature: float, num_ctx: int = 8192,
                  seed: int | None = None) -> tuple[dict, dict]:
        """Structured-output chat. Returns (parsed JSON, usage). Thinking is switched off."""
        options = {"temperature": temperature, "num_ctx": num_ctx}
        if seed is not None:
            options["seed"] = seed  # fixed seeds make sampled runs reproducible
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": schema,
            "stream": False,
            "keep_alive": "30m",
            "options": options,
        }
        if model.startswith(("qwen3", "deepseek-r1")):
            payload["think"] = False  # only thinking models accept this switch
        out = self._post("/api/chat", payload)
        usage = {"prompt_tokens": out.get("prompt_eval_count", 0), "output_tokens": out.get("eval_count", 0)}
        return json.loads(out["message"]["content"]), usage

    def digest(self, model: str) -> str:
        req = urllib.request.Request(self.url + "/api/tags")
        with urllib.request.urlopen(req, timeout=30) as resp:
            for m in json.loads(resp.read()).get("models", []):
                if m.get("name") == model or m.get("model") == model:
                    return m.get("digest", "")
        raise RuntimeError(f"model {model} is not pulled; run: ollama pull {model}")

    def processor(self) -> list[dict]:
        req = urllib.request.Request(self.url + "/api/ps")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()).get("models", [])

    def unload_all(self) -> list[str]:
        """Free GPU and system memory held by loaded Ollama models (keep_alive 0 unloads at once)."""
        names = [m["name"] for m in self.processor()]
        for name in names:
            self._post("/api/generate", {"model": name, "keep_alive": 0})
        return names


# ---------------------------------------------------------------- job runs

def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


@dataclass
class JobRun:
    job: str
    out_dir: Path
    meta: dict = field(default_factory=dict)

    @property
    def output(self) -> Path:
        return self.out_dir / "output.jsonl"

    def rows(self, path: Path | None = None) -> list[dict]:
        path = path or self.output
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def done_ids(self) -> set[str]:
        return {r["id"] for r in self.rows()}

    def append(self, row: dict, path: Path | None = None) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        with (path or self.output).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write_meta(self, **extra) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.meta.update(extra)
        (self.out_dir / "meta.json").write_text(json.dumps(self.meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def start_run(job: str, jobs_dir: Path = JOBS_DIR, restart_on: tuple[str, ...] = (),
              log: Callable[[str], None] = print, **meta) -> JobRun:
    """Open a job's output folder. If any `restart_on` setting (e.g. the prompt version) differs from
    the last run, earlier output is set aside so old and new results are never mixed."""
    run = JobRun(job=job, out_dir=jobs_dir / job)
    previous = {}
    if (run.out_dir / "meta.json").exists():
        previous = json.loads((run.out_dir / "meta.json").read_text(encoding="utf-8"))
    changed = [k for k in restart_on if k in previous and previous[k] != meta.get(k)]
    if changed and run.output.exists():
        kept = run.out_dir / "output.superseded.jsonl"
        run.output.replace(kept)
        log(f"[{job}] {', '.join(changed)} changed since the last run: starting fresh (old output moved to {kept.name})")
        previous = {}
    run.meta = {**previous, "job": job, "git_commit": git_commit(),
                "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **meta}
    return run


# ---------------------------------------------------------------- G2: dish-name variants

G2_SCHEMA = {
    "type": "object",
    "properties": {
        "bangla": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "banglish": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    },
    "required": ["bangla", "banglish"],
}

_BANGLA_ONLY = re.compile(r"^[ঀ-৿‌‍ ]+$")
_BANGLISH_ONLY = re.compile(r"^[a-z][a-z' -]*$")


def clean_variants(raw: dict, existing: Iterable[str]) -> dict:
    """Keep only plausible spellings: Bangla script only / Latin letters only, new, deduplicated."""
    seen = {unicodedata.normalize("NFC", e).strip().lower() for e in existing}
    out: dict[str, list[str]] = {"bangla": [], "banglish": []}
    for kind, pattern in (("bangla", _BANGLA_ONLY), ("banglish", _BANGLISH_ONLY)):
        for item in raw.get(kind, [])[:6]:
            v = re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(item)).strip().lower())
            if not v or len(v) > 40 or not pattern.match(v) or v in seen:
                continue
            seen.add(v)
            out[kind].append(v)
    return out


def vote_variants(samples: list[dict], min_votes: int) -> tuple[dict, dict]:
    """Self-consistency vote over cleaned samples: keep a spelling only if at least `min_votes`
    samples produced it. Real spellings recur; one-off inventions usually don't."""
    kept, votes = {}, {}
    for kind in ("bangla", "banglish"):
        counts = Counter(v for s in samples for v in dict.fromkeys(s[kind]))  # first-seen order, one vote per sample
        votes[kind] = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
        kept[kind] = [v for v, n in votes[kind].items() if n >= min_votes]
    return kept, votes


def run_g2(seeds: Path = DEFAULT_SEEDS, ollama: Ollama | None = None, jobs_dir: Path = JOBS_DIR,
           limit: int | None = None, log: Callable[[str], None] = print) -> JobRun:
    ollama = ollama or Ollama()
    prompt = load_prompt("g2-dish-aliases")
    samples, min_votes = int(prompt.params.get("samples", 1)), int(prompt.params.get("min_votes", 1))
    seeds_used = list(range(1, samples + 1))
    run = start_run("g2", jobs_dir, restart_on=("model", "prompt_version"), log=log,
                    model=prompt.model, model_digest=ollama.digest(prompt.model),
                    prompt_id=prompt.id, prompt_version=prompt.version, temperature=prompt.temperature,
                    samples=samples, min_votes=min_votes, sample_seeds=seeds_used, status="running",
                    review="Candidates only: a native Bangla speaker reviews before they enter the seeds.")
    run.write_meta()
    done = run.done_ids()
    dishes = [_read(p) for p in sorted((seeds / "dishes").glob("*.yaml"))]
    todo = [d for d in dishes if d["id"] not in done][: limit or None]
    t0 = time.monotonic()
    for i, d in enumerate(todo, 1):
        existing = [d["name_en"], d["name_bn"], *d.get("aliases", [])]
        text = prompt.render(name_en=d["name_en"], name_bn=d["name_bn"], existing=", ".join(existing))
        raws, usage = [], {"prompt_tokens": 0, "output_tokens": 0}
        for seed in seeds_used:
            raw, u = ollama.chat_json(prompt.model, text, G2_SCHEMA, prompt.temperature, seed=seed)
            raws.append(raw)
            usage = {k: usage[k] + u.get(k, 0) for k in usage}
        variants, votes = vote_variants([clean_variants(r, existing) for r in raws], min_votes)
        run.append({"id": d["id"], "candidates": variants, "votes": votes, "raw": raws, "usage": usage,
                    "is_synthetic": False})
        log(f"[g2] {i}/{len(todo)} {d['id']}: +{len(variants['bangla'])} bn, +{len(variants['banglish'])} banglish")
    run.write_meta(status="finished", finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   items=len(run.done_ids()), seconds=round(time.monotonic() - t0, 1))
    return run


# ---------------------------------------------------------------- G3: embeddings

def embedding_items(seeds: Path = DEFAULT_SEEDS, include_drafts: bool = True) -> list[dict]:
    """Texts to embed: every dish name / alias and every Rule Card (English and Bangla)."""
    from .graph import normalise_name

    items = []
    for p in sorted((seeds / "dishes").glob("*.yaml")):
        d = _read(p)
        if not include_drafts and d.get("status") != "approved":
            continue
        names: dict[str, str] = {}
        for a in d.get("aliases", []):
            names[normalise_name(a)] = "bn" if re.search(r"[ঀ-৿]", a) else "banglish"
        names[normalise_name(d["name_en"])] = "en"  # the English / Bangla name wins over an identical alias
        names[normalise_name(d["name_bn"])] = "bn"
        for name, lang in sorted(names.items()):
            items.append({"id": f"name:{d['id']}:{name}", "kind": "dish_name", "ref": d["id"], "lang": lang, "text": name})
    for p in sorted((seeds / "rule_cards").glob("*.yaml")):
        r = _read(p)
        if not include_drafts and r.get("status") != "approved":
            continue
        for lang in ("en", "bn"):
            text = f"{r[f'title_{lang}']}. {r[f'recommendation_{lang}']}"
            items.append({"id": f"rule:{r['id']}:{lang}", "kind": "rule_card", "ref": r["id"], "lang": lang, "text": text})
    chunks = JOBS_DIR / "g1" / "output.jsonl"
    if chunks.exists():
        for line in chunks.read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            items.append({"id": f"chunk:{c['id']}", "kind": "chunk", "ref": c["id"], "lang": "en",
                          "text": f"{c['header']}\n\n{c['text']}"})
    return items


def encode_vector(vec: Iterable[float]) -> str:
    """float16 little-endian, base64. The model runs in fp16, so this loses nothing and is ~4x smaller than JSON."""
    values = [float(x) for x in vec]
    return base64.b64encode(struct.pack(f"<{len(values)}e", *values)).decode("ascii")


def decode_vector(data: str) -> list[float]:
    raw = base64.b64decode(data)
    return list(struct.unpack(f"<{len(raw) // 2}e", raw))


def run_g3(encode: Callable[[list[str]], list[list[float]]] | None = None, seeds: Path = DEFAULT_SEEDS,
           jobs_dir: Path = JOBS_DIR, batch_size: int = 32, log: Callable[[str], None] = print) -> JobRun:
    """Rebuilds output.jsonl for the current seeds and corpus. A vector is reused only when both the
    item id and its exact text are unchanged; stopped runs resume from output.jsonl.partial."""
    device = "injected"
    if encode is None:
        try:
            freed = Ollama().unload_all()
            if freed:
                log(f"[g3] unloaded Ollama models to free memory: {', '.join(freed)}")
        except OSError:
            pass  # Ollama isn't running: nothing to free
        encode, device = _bge_m3_encoder()
    run = start_run("g3", jobs_dir, restart_on=("model",), log=log, model=MODELS["g3"], device=device,
                    normalized=True, dims=1024, encoding="float16 little-endian, base64", status="running")
    run.write_meta()
    partial = run.out_dir / "output.jsonl.partial"
    cached = {(r["id"], r["text"]): r["embedding_f16"] for r in run.rows() + run.rows(partial) if "embedding_f16" in r}
    partial.unlink(missing_ok=True)
    items = embedding_items(seeds)
    todo = []
    for item in items:
        if (item["id"], item["text"]) in cached:
            run.append({**item, "embedding_f16": cached[(item["id"], item["text"])]}, partial)
        else:
            todo.append(item)
    log(f"[g3] {len(items) - len(todo)} unchanged, {len(todo)} to embed")
    t0 = time.monotonic()
    for start in range(0, len(todo), batch_size):
        batch = todo[start : start + batch_size]
        vectors = encode([b["text"] for b in batch])
        for item, vec in zip(batch, vectors):
            if len(vec) != 1024:
                raise ValueError(f"expected 1024 dims, got {len(vec)}")
            run.append({**item, "embedding_f16": encode_vector(vec)}, partial)
        log(f"[g3] {min(start + batch_size, len(todo))}/{len(todo)} embedded")
    if partial.exists():
        partial.replace(run.output)
    else:
        run.output.unlink(missing_ok=True)
    run.write_meta(status="finished", finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   items=len(items), embedded=len(todo), seconds=round(time.monotonic() - t0, 1))
    return run


def _bge_m3_encoder():
    # BAAI/bge-m3 ships only pytorch_model.bin. Transformers then starts a background download of a
    # second 2.3 GB safetensors copy while the model loads; on a 16 GB machine that gets the job killed.
    os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"  # ROCm builds expose the GPU as "cuda"
    model = SentenceTransformer(MODELS["g3"], device=device)
    if device == "cuda":
        model.half()

    def encode(texts: list[str]) -> list[list[float]]:
        return model.encode(texts, batch_size=len(texts), normalize_embeddings=True).tolist()

    name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
    return encode, f"{device}:{name}"


# ---------------------------------------------------------------- check

def check(ollama: Ollama | None = None, log: Callable[[str], None] = print) -> bool:
    ollama = ollama or Ollama()
    ok = True
    for job in ("g1", "g2"):
        try:
            ollama.digest(MODELS[job])
            log(f"OK   {MODELS[job]} is pulled ({job})")
        except Exception as exc:  # noqa: BLE001
            ok = False
            log(f"FAIL {exc}")
    try:
        import torch

        gpu = torch.cuda.is_available()
        log(f"{'OK  ' if gpu else 'WARN'} torch {torch.__version__}, GPU available: {gpu}"
            + (f" ({torch.cuda.get_device_name(0)})" if gpu else ""))
    except ImportError:
        log("WARN torch not importable in this environment (needed for g3; see docs/setup.md §3)")
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HappyGut GPU jobs (run on Ubuntu)")
    parser.add_argument("job", choices=["check", "g1", "g2", "g3"])
    parser.add_argument("--limit", type=int, default=None, help="process at most N new items (for a quick try)")
    args = parser.parse_args(argv)
    if args.job == "check":
        return 0 if check() else 1
    if args.job == "g2":
        run_g2(limit=args.limit)
    elif args.job == "g3":
        run_g3()
    elif args.job == "g1":
        try:
            from .corpus import run_g1
        except ImportError:
            print("G1 needs the guideline corpus first (docs/setup.md §3 will say when it's ready).")
            return 1
        run_g1(limit=args.limit)
    print(f"Done. Now: git add data/gpu_jobs && git commit -m 'GPU job {args.job} outputs' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
