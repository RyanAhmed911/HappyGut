import json

import pytest

from happygut_pipelines import gpu_jobs as gj


class FakeOllama:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def chat_json(self, model, prompt, schema, temperature, num_ctx=8192):
        self.calls.append((model, prompt))
        return self.reply(prompt), {"prompt_tokens": 10, "output_tokens": 5}

    def digest(self, model):
        return "sha256:fake"


def test_prompts_are_versioned_and_render():
    p = gj.load_prompt("g2-dish-aliases")
    assert p.version == 1 and p.model == "gemma3:12b"
    text = p.render(name_en="Kacchi biryani", name_bn="কাচ্চি বিরিয়ানি", existing="kacchi")
    assert "Kacchi biryani" in text and "{name_en}" not in text
    assert gj.load_prompt("g1-context-header").model == "qwen3:14b"


def test_clean_variants_rejects_mixed_scripts_and_duplicates():
    raw = {
        "bangla": ["কাচ্চি", "কাচ্চি বিরিয়ানি", "नमस्कार", "আ saludar", "কাচ্চী"],
        "banglish": ["Kachchi", "kacchi", "kachhi biriani", "কাচ্চি", "x" * 60, "kachchi"],
    }
    out = gj.clean_variants(raw, existing=["kacchi", "কাচ্চি বিরিয়ানি"])
    assert out["bangla"] == ["কাচ্চি", "কাচ্চী"]  # Devanagari and mixed script dropped
    assert out["banglish"] == ["kachchi", "kachhi biriani"]  # existing, Bangla, too long, duplicate dropped


def test_g2_writes_outputs_and_provenance(tmp_path):
    fake = FakeOllama(lambda prompt: {"bangla": [], "banglish": ["test spelling"]})
    run = gj.run_g2(ollama=fake, jobs_dir=tmp_path, limit=3, log=lambda m: None)
    rows = [json.loads(l) for l in run.output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3 and all(r["candidates"]["banglish"] == ["test spelling"] for r in rows)
    meta = json.loads((tmp_path / "g2" / "meta.json").read_text())
    assert meta["status"] == "finished" and meta["model"] == "gemma3:12b"
    assert meta["model_digest"] == "sha256:fake" and meta["prompt_version"] == 1


def test_g2_resumes_without_repeating_work(tmp_path):
    fake = FakeOllama(lambda prompt: {"bangla": [], "banglish": []})
    gj.run_g2(ollama=fake, jobs_dir=tmp_path, limit=2, log=lambda m: None)
    gj.run_g2(ollama=fake, jobs_dir=tmp_path, limit=2, log=lambda m: None)
    ids = [json.loads(l)["id"] for l in (tmp_path / "g2" / "output.jsonl").read_text().splitlines()]
    assert len(ids) == 4 and len(set(ids)) == 4


def test_embedding_items_cover_names_and_rules():
    items = gj.embedding_items()
    kinds = {i["kind"] for i in items}
    assert {"dish_name", "rule_card"} <= kinds
    names = [i for i in items if i["kind"] == "dish_name" and i["ref"] == "dish.kacchi_biryani"]
    assert {"bn", "en", "banglish"} <= {i["lang"] for i in names}
    assert len({i["id"] for i in items}) == len(items), "ids are unique"


def test_g3_with_injected_encoder(tmp_path):
    encode = lambda texts: [[0.0] * 1023 + [1.0] for _ in texts]
    run = gj.run_g3(encode=encode, jobs_dir=tmp_path, log=lambda m: None)
    first = json.loads(run.output.read_text(encoding="utf-8").splitlines()[0])
    assert len(first["embedding"]) == 1024
    assert json.loads((tmp_path / "g3" / "meta.json").read_text())["dims"] == 1024


def test_g3_rejects_wrong_dimensions(tmp_path):
    with pytest.raises(ValueError):
        gj.run_g3(encode=lambda texts: [[0.0] * 768 for _ in texts], jobs_dir=tmp_path, log=lambda m: None)
