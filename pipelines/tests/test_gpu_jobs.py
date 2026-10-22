import json

import pytest

from happygut_pipelines import gpu_jobs as gj


class FakeOllama:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def chat_json(self, model, prompt, schema, temperature, num_ctx=8192, seed=None):
        self.calls.append((model, prompt, seed))
        return self.reply(prompt, seed), {"prompt_tokens": 10, "output_tokens": 5}

    def digest(self, model):
        return "sha256:fake"


def test_prompts_are_versioned_and_render():
    p = gj.load_prompt("g2-dish-aliases")
    assert p.version == 2 and p.model == "gemma3:12b" and p.params["samples"] == "3"
    assert gj.load_prompt("g2-dish-aliases", version=1).temperature == 0.2
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
    fake = FakeOllama(lambda prompt, seed: {"bangla": [], "banglish": ["test spelling"]})
    run = gj.run_g2(ollama=fake, jobs_dir=tmp_path, limit=3, log=lambda m: None)
    rows = run.rows()
    assert len(rows) == 3 and all(r["candidates"]["banglish"] == ["test spelling"] for r in rows)
    assert [c[2] for c in fake.calls[:3]] == [1, 2, 3], "three seeded samples per dish"
    meta = json.loads((tmp_path / "g2" / "meta.json").read_text())
    assert meta["status"] == "finished" and meta["model"] == "gemma3:12b"
    assert meta["model_digest"] == "sha256:fake" and meta["prompt_version"] == 2 and meta["min_votes"] == 2


def test_g2_vote_drops_one_off_inventions(tmp_path):
    def reply(prompt, seed):
        invented = {1: ["beef therri"], 2: ["beef theri"], 3: []}[seed]
        return {"bangla": ["গরুর তেহারি", "বিফ থেরী"] if seed == 1 else ["গরুর তেহারি"],
                "banglish": ["bif tehari", *invented]}
    row = gj.run_g2(ollama=FakeOllama(reply), jobs_dir=tmp_path, limit=1, log=lambda m: None).rows()[0]
    assert row["candidates"] == {"bangla": ["গরুর তেহারি"], "banglish": ["bif tehari"]}
    assert row["votes"]["banglish"]["bif tehari"] == 3 and row["votes"]["bangla"]["বিফ থেরী"] == 1
    assert len(row["raw"]) == 3


def test_changed_prompt_version_starts_fresh(tmp_path):
    out = tmp_path / "g2"
    out.mkdir()
    (out / "meta.json").write_text(json.dumps({"model": "gemma3:12b", "prompt_version": 1}))
    (out / "output.jsonl").write_text(json.dumps({"id": "dish.alu_bhorta"}) + "\n")
    fake = FakeOllama(lambda prompt, seed: {"bangla": [], "banglish": []})
    run = gj.run_g2(ollama=fake, jobs_dir=tmp_path, limit=1, log=lambda m: None)
    assert [r["id"] for r in run.rows()] == ["dish.alu_bhorta"] and fake.calls, "v1 row was not reused"
    assert (out / "output.superseded.jsonl").exists()


def test_g2_resumes_without_repeating_work(tmp_path):
    fake = FakeOllama(lambda prompt, seed: {"bangla": [], "banglish": []})
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
    first = run.rows()[0]
    assert gj.decode_vector(first["embedding_f16"]) == [0.0] * 1023 + [1.0]
    assert json.loads((tmp_path / "g3" / "meta.json").read_text())["dims"] == 1024
    assert not (tmp_path / "g3" / "output.jsonl.partial").exists()


def test_g3_reuses_only_unchanged_texts(tmp_path):
    calls = []

    def encode(texts):
        calls.append(len(texts))
        return [[0.5] * 1024 for _ in texts]

    first = gj.run_g3(encode=encode, jobs_dir=tmp_path, log=lambda m: None)
    total = len(first.rows())
    rows = first.rows()
    rows[0]["text"] = "an older wording of this item"  # as if the seed text changed after the last run
    first.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    calls.clear()
    second = gj.run_g3(encode=encode, jobs_dir=tmp_path, log=lambda m: None)
    assert sum(calls) == 1 and len(second.rows()) == total


def test_vector_encoding_round_trips_fp16():
    vec = [0.1, -0.25, 0.0, 1.0]
    assert gj.decode_vector(gj.encode_vector(vec)) == pytest.approx(vec, abs=1e-3)


def test_g3_rejects_wrong_dimensions(tmp_path):
    with pytest.raises(ValueError):
        gj.run_g3(encode=lambda texts: [[0.0] * 768 for _ in texts], jobs_dir=tmp_path, log=lambda m: None)
