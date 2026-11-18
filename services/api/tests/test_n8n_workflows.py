"""The n8n workflows in n8n/workflows: well-formed, calling routes that exist, with no secrets in the files."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from happygut_api.main import create_app

WORKFLOWS = sorted((Path(__file__).resolve().parents[3] / "n8n" / "workflows").glob("*.json"))
ROUTES = {(m, r.path) for r in create_app().routes for m in getattr(r, "methods", set()) or set()}


def test_there_are_four_workflows():
    assert [p.name for p in WORKFLOWS] == ["happygut-alert.json", "happygut-health.json", "happygut-nightly.json", "happygut-safety-check.json"]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.stem)
def test_workflow_is_well_formed(path):
    wf = json.loads(path.read_text(encoding="utf-8"))
    assert re.fullmatch(r"[A-Za-z0-9]{16}", wf["id"]) and wf["versionId"]  # n8n's import needs both
    names = [n["name"] for n in wf["nodes"]]
    assert len(names) == len(set(names)) and len({n["id"] for n in wf["nodes"]}) == len(names)
    for source, outputs in wf["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            assert all(target["node"] in names for target in branch)
    triggers = [n for n in wf["nodes"] if n["type"].endswith(("Trigger", "trigger"))]
    assert triggers, "every workflow starts with a trigger"
    assert wf["settings"]["timezone"] == "Asia/Dhaka" and wf["active"] is False  # the team switches it on after import


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.stem)
def test_http_calls_hit_real_routes_and_no_secret_is_in_the_file(path):
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"Bearer\s+\S|sk-lf-|pk-lf-|password", text, re.IGNORECASE), "secrets live in n8n credentials, not files"
    for n in json.loads(text)["nodes"]:
        if n["type"] != "n8n-nodes-base.httpRequest":
            continue
        url = n["parameters"]["url"]
        assert url.startswith("={{ $env.HAPPYGUT_API_URL }}/v1/")
        method = n["parameters"].get("method", "GET")
        assert (method, url.split("}}", 1)[1]) in ROUTES, f"{method} {url} is not an API route"
        if "/jobs/" in url:
            assert n["credentials"]["httpHeaderAuth"]["name"] == "HappyGut jobs token"
